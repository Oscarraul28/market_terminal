# core/bots/bot4_retail_sentiment.py
import yfinance as yf

def calculate_retail_sentiment(ticker):
    """
    Score simplificado de retail sentiment basado solo en yfinance.
    En versión futura agregaremos pytrends y Reddit.
    """
    # Por ahora retornamos valores de ejemplo
    # TODO: Implementar Google Trends y Reddit
    return {
        'score': 65,  # Placeholder
        'google_trends': 70,
        'reddit_mentions': 60,
        'level': '📈 BULLISH'
    }

def calculate_fundamental_score(ticker):
    """
    Score 0-100 de salud fundamental basado en yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # P/E Score (invertido: menor P/E es mejor)
        pe = info.get('trailingPE', 50)
        if pe <= 0:
            pe_score = 0
        elif pe > 100:
            pe_score = 10
        else:
            pe_score = max(0, 100 - pe)
        
        # Debt/Equity Score
        debt_equity = info.get('debtToEquity', 100) / 100 if info.get('debtToEquity') else 1
        debt_score = max(0, 100 - debt_equity * 50)
        
        # Revenue Growth Score
        revenue_growth = info.get('revenueGrowth', 0)
        if revenue_growth is None:
            growth_score = 50
        else:
            growth_score = min(100, max(0, 50 + revenue_growth * 100))
        
        # Profit Margin Score
        profit_margin = info.get('profitMargins', 0)
        if profit_margin is None:
            margin_score = 50
        else:
            margin_score = min(100, profit_margin * 500)
        
        # Weighted average
        fundamental_score = (
            pe_score * 0.25 +
            debt_score * 0.25 +
            growth_score * 0.25 +
            margin_score * 0.25
        )
        
        return {
            'score': int(fundamental_score),
            'pe_ratio': round(pe, 2) if pe else 'N/A',
            'debt_to_equity': info.get('debtToEquity', 'N/A'),
            'revenue_growth': round(revenue_growth * 100, 2) if revenue_growth else 'N/A',
            'profit_margin': round(profit_margin * 100, 2) if profit_margin else 'N/A',
            'level': get_fundamental_level(fundamental_score)
        }
    except Exception as e:
        print(f"Error calculating fundamentals: {e}")
        return {
            'score': 50,
            'pe_ratio': 'N/A',
            'debt_to_equity': 'N/A',
            'revenue_growth': 'N/A',
            'profit_margin': 'N/A',
            'level': 'UNKNOWN'
        }

def get_fundamental_level(score):
    """Categoriza la salud fundamental."""
    if score >= 75:
        return "💪 EXCELENTE"
    elif score >= 60:
        return "✅ BUENO"
    elif score >= 40:
        return "⚠️ REGULAR"
    elif score >= 25:
        return "🔴 DÉBIL"
    else:
        return "💀 TERRIBLE"

def get_trading_signal(retail_score, fundamental_score):
    """Genera señal basada en los dos velocímetros."""
    if retail_score < 50 and fundamental_score >= 60:
        return {
            'signal': '🟢 COMPRA',
            'message': 'Oportunidad oculta: Fundamentales fuertes pero retail no lo ve aún.',
            'color': 'success'
        }
    elif retail_score >= 75 and fundamental_score < 40:
        return {
            'signal': '⚠️ SOBREVALORADO',
            'message': 'FOMO retail en activo con fundamentales débiles. Alto riesgo.',
            'color': 'warning'
        }
    elif retail_score >= 60 and fundamental_score >= 60:
        return {
            'signal': '⚡ MOMENTUM',
            'message': 'Ambos fuertes. Ride the trend con stop loss.',
            'color': 'info'
        }
    elif retail_score < 40 and fundamental_score < 40:
        return {
            'signal': '🔴 EVITAR',
            'message': 'Trampa de valor: Fundamentales débiles y sentiment negativo.',
            'color': 'danger'
        }
    else:
        return {
            'signal': '😐 NEUTRAL',
            'message': 'Señales mixtas. Espera confirmación.',
            'color': 'secondary'
        }

def analyze_stock(ticker):
    """Análisis completo: Retail sentiment vs Fundamentals"""
    retail = calculate_retail_sentiment(ticker)
    fundamentals = calculate_fundamental_score(ticker)
    signal = get_trading_signal(retail['score'], fundamentals['score'])
    
    return {
        'ticker': ticker.upper(),
        'retail': retail,
        'fundamentals': fundamentals,
        'signal': signal
    }