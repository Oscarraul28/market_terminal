# core/views.py
from django.shortcuts import render
from django.http import JsonResponse

from .bots.bot1_macro import analyze_macro_sentiment
from .bots.bot2_flow import analyze_flow
from .bots.bot3_smart_money import analyze_smart_money
from .bots.bot4_retail_sentiment import analyze_stock
from .bots.bot5_stock_analysis import analyze_stock_technical


def dashboard(request):
    """Vista principal del dashboard."""
    context = {
        'ticker': 'TSLA',
        'temporalidad': '1d',
        'n_velas': 5,
        'rsi_manual': '',  # ← NUEVO
        'show_results': False
    }
    
    if request.method == 'POST':
        ticker = request.POST.get('ticker', 'TSLA').upper()
        temporalidad = request.POST.get('temporalidad', '1d')
        rsi_manual = request.POST.get('rsi_manual', '')  # ← NUEVO: obtener RSI manual
        
        # Determinar n_velas según temporalidad
        n_velas_map = {
            '1h': 24,
            '4h': 6,
            '1d': 5,
            '1wk': 6
        }
        n_velas = n_velas_map.get(temporalidad, 5)
        
        # Ejecutar TODOS los bots
        bot1_result = analyze_macro_sentiment(temporalidad, n_velas)
        bot2_result = analyze_flow(temporalidad, n_velas)
        bot3_result = analyze_smart_money(ticker)
        bot4_result = analyze_stock(ticker)
        
        # Bot 5: Pasar RSI manual si existe
        if rsi_manual:
            try:
                rsi_value = float(rsi_manual)
                bot5_result = analyze_stock_technical(ticker, manual_rsi=rsi_value)  # ← NUEVO
            except ValueError:
                bot5_result = analyze_stock_technical(ticker)  # Si el valor no es válido, usar automático
        else:
            bot5_result = analyze_stock_technical(ticker)
        
        context.update({
            'ticker': ticker,
            'temporalidad': temporalidad,
            'n_velas': n_velas,
            'rsi_manual': rsi_manual,  # ← NUEVO
            'bot1': bot1_result,
            'bot2': bot2_result,
            'bot3': bot3_result,
            'bot4': bot4_result,
            'bot5': bot5_result,
            'show_results': True
        })
    
    return render(request, 'core/dashboard.html', context)


def api_analyze(request):
    """API endpoint para análisis."""
    ticker = request.GET.get('ticker', 'TSLA')
    temporalidad = request.GET.get('temporalidad', '1d')
    rsi_manual = request.GET.get('rsi_manual', '')
    
    n_velas_map = {'1h': 24, '4h': 6, '1d': 5, '1wk': 6}
    n_velas = n_velas_map.get(temporalidad, 5)
    
    bot1_result = analyze_macro_sentiment(temporalidad, n_velas)
    bot2_result = analyze_flow(temporalidad, n_velas)
    bot3_result = analyze_smart_money(ticker)
    bot4_result = analyze_stock(ticker)
    
    if rsi_manual:
        try:
            rsi_value = float(rsi_manual)
            bot5_result = analyze_stock_technical(ticker, manual_rsi=rsi_value)
        except ValueError:
            bot5_result = analyze_stock_technical(ticker)
    else:
        bot5_result = analyze_stock_technical(ticker)
    
    return JsonResponse({
        'bot1': bot1_result,
        'bot2': bot2_result,
        'bot3': bot3_result,
        'bot4': bot4_result,
        'bot5': bot5_result
    })