# core/views.py
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render

from .bots.bot1_macro import analyze_macro_sentiment
from .bots.bot2_flow import analyze_flow
from .bots.bot3_smart_money import analyze_smart_money
from .bots.bot4_retail_sentiment import analyze_stock
from .bots.bot5_stock_analysis import analyze_stock_technical

N_VELAS_MAP = {'1h': 24, '4h': 6, '1d': 5, '1wk': 6}


def _cached(key, ttl, fn, *args, **kwargs):
    """Devuelve fn(*args) desde caché, o lo calcula y lo guarda."""
    hit = cache.get(key)
    if hit is not None:
        return hit
    result = fn(*args, **kwargs)
    # Solo cachear resultados válidos: si el bot falló, no congeles el error.
    if result is not None:
        cache.set(key, result, ttl)
    return result


def run_all_bots(ticker, temporalidad, rsi_manual=''):
    """
    Ejecuta los cinco bots con caché.

    Bots 1 y 2 son de mercado completo: su resultado depende solo de
    (temporalidad, n_velas), no del ticker, así que una sola consulta
    los deja calientes para todas las demás.
    """
    n_velas = N_VELAS_MAP.get(temporalidad, 5)
    ttl_macro = settings.CACHE_TTL_MACRO
    ttl_ticker = settings.CACHE_TTL_TICKER

    # --- Bloque macro: compartido entre todos los tickers ---
    bot1_result = _cached(
        f'bot1:{temporalidad}:{n_velas}', ttl_macro,
        analyze_macro_sentiment, temporalidad, n_velas,
    )
    bot2_result = _cached(
        f'bot2:{temporalidad}:{n_velas}', ttl_macro,
        analyze_flow, temporalidad, n_velas,
    )

    # --- Bloque por ticker ---
    bot3_result = _cached(f'bot3:{ticker}', ttl_ticker, analyze_smart_money, ticker)
    bot4_result = _cached(f'bot4:{ticker}', ttl_ticker, analyze_stock, ticker)

    # Bot 5: si hay RSI manual el resultado es específico de ese valor,
    # así que entra en la clave de caché.
    if rsi_manual:
        try:
            rsi_value = float(rsi_manual)
            bot5_result = _cached(
                f'bot5:{ticker}:rsi={rsi_value}', ttl_ticker,
                analyze_stock_technical, ticker, manual_rsi=rsi_value,
            )
        except ValueError:
            bot5_result = _cached(
                f'bot5:{ticker}', ttl_ticker, analyze_stock_technical, ticker
            )
    else:
        bot5_result = _cached(
            f'bot5:{ticker}', ttl_ticker, analyze_stock_technical, ticker
        )

    return {
        'n_velas': n_velas,
        'bot1': bot1_result,
        'bot2': bot2_result,
        'bot3': bot3_result,
        'bot4': bot4_result,
        'bot5': bot5_result,
    }


def dashboard(request):
    """Vista principal del dashboard."""
    context = {
        'ticker': 'TSLA',
        'temporalidad': '1d',
        'n_velas': 5,
        'rsi_manual': '',
        'show_results': False,
    }

    if request.method == 'POST':
        ticker = request.POST.get('ticker', 'TSLA').upper().strip()
        temporalidad = request.POST.get('temporalidad', '1d')
        rsi_manual = request.POST.get('rsi_manual', '')

        results = run_all_bots(ticker, temporalidad, rsi_manual)

        context.update(results)
        context.update({
            'ticker': ticker,
            'temporalidad': temporalidad,
            'rsi_manual': rsi_manual,
            'show_results': True,
        })

    return render(request, 'core/dashboard.html', context)


def api_analyze(request):
    """API endpoint para análisis."""
    ticker = request.GET.get('ticker', 'TSLA').upper().strip()
    temporalidad = request.GET.get('temporalidad', '1d')
    rsi_manual = request.GET.get('rsi_manual', '')

    results = run_all_bots(ticker, temporalidad, rsi_manual)
    results.pop('n_velas', None)

    return JsonResponse(results)


def healthz(request):
    """Ping ligero para mantener el servicio despierto."""
    return JsonResponse({'status': 'ok'})
