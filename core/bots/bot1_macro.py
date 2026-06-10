# core/bots/bot1_macro.py
import yfinance as yf

def get_change_series(ticker, n_velas, interval):
    """Calcula el cambio porcentual de un ticker en n velas."""
    try:
        data = yf.download(ticker, period="1y", interval=interval, progress=False)
        if data.empty:
            return 0
        series = data["Close"].tail(n_velas)
        change = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0]).item()
        return change
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return 0

def analyze_macro_sentiment(temporalidad="1d", n_velas=5):
    """
    Analiza el sentimiento macro del mercado.
    
    Args:
        temporalidad: '1h', '4h', '1d', '1wk'
        n_velas: número de velas a analizar
    
    Returns:
        dict con análisis completo
    """
    # Fetch data
    us10y = get_change_series("^TNX", n_velas, temporalidad)
    qqq = get_change_series("QQQ", n_velas, temporalidad)
    dxy = get_change_series("DX-Y.NYB", n_velas, temporalidad)
    vix = get_change_series("^VIX", n_velas, temporalidad)
    
    # Lógica de decisión (más específicas primero)
    if us10y > 0 and dxy > 0 and qqq < 0:
        signal = "⚠️ PRECAUCIÓN"
        message = "US10Y y DXY al alza, Nasdaq corrigiendo. Posible salida de riesgo."
        color = "warning"
        
    elif us10y < 0 and qqq > 0 and dxy < 0:
        signal = "🚀 MUY BULLISH"
        message = "US10Y y DXY bajando, Nasdaq subiendo. Excelente apetito por riesgo, capital fluyendo a tech."
        color = "success"
        
    elif us10y < 0 and qqq > 0 and vix < 0:
        signal = "✅ BULLISH"
        message = "Rendimiento del bono y VIX bajando, Nasdaq subiendo. Buen sentimiento de riesgo."
        color = "success"
        
    elif us10y < 0 and qqq < 0 and dxy > 0:
        signal = "💀 PÁNICO"
        message = "Flight to safety extremo: US10Y y Nasdaq caen, DXY sube. Búsqueda de refugio en dólar."
        color = "danger"
        
    elif us10y < 0 and vix > 0:
        signal = "🔴 MIEDO"
        message = "US10Y cayendo mientras VIX sube: miedo real en el mercado."
        color = "danger"
        
    else:
        signal = "⏸️ NEUTRAL"
        message = "Mercado indeciso, espera confirmación."
        color = "secondary"
    
    return {
        'signal': signal,
        'message': message,
        'color': color,
        'data': {
            'us10y': us10y,
            'qqq': qqq,
            'dxy': dxy,
            'vix': vix
        },
        'temporalidad': temporalidad,
        'n_velas': n_velas
    }