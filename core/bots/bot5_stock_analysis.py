# core/bots/bot5_stock_analysis.py
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_rsi(data, period=14):
    """Calcula el Relative Strength Index (RSI)."""
    # Asegurarse de tener suficientes datos
    if len(data) < period + 1:
        return 50  # Neutral si no hay suficientes datos
    
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Evitar división por cero
    rs = gain / loss.replace(0, 0.0001)
    rsi = 100 - (100 / (1 + rs))
    
    # Retornar el RSI más reciente
    return rsi.iloc[-1]

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calcula MACD (Moving Average Convergence Divergence)."""
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line.iloc[-1],
        'signal': signal_line.iloc[-1],
        'histogram': histogram.iloc[-1],
        'crossover': 'bullish' if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0 else 
                     'bearish' if histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0 else 'none'
    }

def calculate_bollinger_bands(data, period=20, std_dev=2):
    """Calcula Bollinger Bands."""
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    current_price = data.iloc[-1]
    
    return {
        'upper': upper_band.iloc[-1],
        'middle': sma.iloc[-1],
        'lower': lower_band.iloc[-1],
        'current': current_price,
        'position': 'overbought' if current_price > upper_band.iloc[-1] else
                   'oversold' if current_price < lower_band.iloc[-1] else 'normal'
    }

def find_support_resistance(data, window=20):
    """Identifica niveles de soporte y resistencia."""
    highs = data.rolling(window=window).max()
    lows = data.rolling(window=window).min()
    
    # Resistencia: máximo reciente
    resistance = highs.iloc[-window:].max()
    
    # Soporte: mínimo reciente
    support = lows.iloc[-window:].min()
    
    current = data.iloc[-1]
    
    return {
        'resistance': resistance,
        'support': support,
        'current': current,
        'distance_to_resistance': ((resistance - current) / current) * 100,
        'distance_to_support': ((current - support) / current) * 100
    }

def analyze_volume(data_df):
    """Analiza el volumen relativo."""
    recent_volume = data_df['Volume'].iloc[-1]
    avg_volume = data_df['Volume'].tail(20).mean()
    
    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
    
    return {
        'current': int(recent_volume),
        'average': int(avg_volume),
        'ratio': volume_ratio,
        'level': 'extreme' if volume_ratio > 3 else
                'high' if volume_ratio > 2 else
                'above_average' if volume_ratio > 1.2 else
                'normal' if volume_ratio > 0.8 else 'low'
    }

def analyze_stock_technical(ticker, period="6mo", manual_rsi=None):  # ← NUEVO parámetro
    """
    Análisis técnico profundo de una acción.
    
    Args:
        ticker: símbolo del ticker
        period: período de datos históricos
        manual_rsi: RSI introducido manualmente (opcional)
    
    Returns:
        dict con análisis técnico completo
    """
    try:
        # Descargar datos
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        if data.empty or len(data) < 20:
            return {
                'available': False,
                'error': 'Insufficient data available for this ticker'
            }
        
        close_prices = data['Close']
        
        # Indicadores técnicos
        if manual_rsi is not None:  # ← NUEVO: Usar RSI manual si se proporciona
            rsi = manual_rsi
            rsi_source = 'manual'
        else:
            rsi = calculate_rsi(close_prices)
            rsi_source = 'calculated'
        
        macd = calculate_macd(close_prices)
        bollinger = calculate_bollinger_bands(close_prices)
        sr_levels = find_support_resistance(close_prices)
        volume_analysis = analyze_volume(data)
        
        # Precio actual
        current_price = close_prices.iloc[-1]
        price_change = ((current_price - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100
        
        # Análisis de RSI
        if rsi > 70:
            rsi_signal = {
                'level': '🔴 OVERBOUGHT',
                'message': f'RSI at {rsi:.1f}. Stock is overbought, potential pullback ahead.',
                'color': 'danger'
            }
        elif rsi > 60:
            rsi_signal = {
                'level': '📈 STRONG',
                'message': f'RSI at {rsi:.1f}. Strong momentum but nearing overbought.',
                'color': 'warning'
            }
        elif rsi > 40:
            rsi_signal = {
                'level': '😐 NEUTRAL',
                'message': f'RSI at {rsi:.1f}. No extreme conditions.',
                'color': 'secondary'
            }
        elif rsi > 30:
            rsi_signal = {
                'level': '📉 WEAK',
                'message': f'RSI at {rsi:.1f}. Weak momentum, nearing oversold.',
                'color': 'warning'
            }
        else:
            rsi_signal = {
                'level': '🟢 OVERSOLD',
                'message': f'RSI at {rsi:.1f}. Stock is oversold, potential bounce ahead.',
                'color': 'success'
            }
        
        # ... resto del código MACD, señales, etc. (igual que antes)
        
        # Análisis de MACD
        if macd['crossover'] == 'bullish':
            macd_signal = {
                'level': '✅ BULLISH CROSSOVER',
                'message': 'MACD crossed above signal line. Buy signal.',
                'color': 'success'
            }
        elif macd['crossover'] == 'bearish':
            macd_signal = {
                'level': '⚠️ BEARISH CROSSOVER',
                'message': 'MACD crossed below signal line. Sell signal.',
                'color': 'danger'
            }
        elif macd['histogram'] > 0:
            macd_signal = {
                'level': '📈 BULLISH',
                'message': 'MACD above signal line. Uptrend intact.',
                'color': 'success'
            }
        else:
            macd_signal = {
                'level': '📉 BEARISH',
                'message': 'MACD below signal line. Downtrend intact.',
                'color': 'danger'
            }
        
        # Señal combinada
        combined_signal = generate_technical_signal(
            rsi, macd, bollinger, sr_levels, volume_analysis
        )
        
        return {
            'available': True,
            'ticker': ticker.upper(),
            'price': {
                'current': current_price,
                'change': price_change
            },
            'rsi': {
                'value': rsi,
                'source': rsi_source,  # ← NUEVO: Indicar si es manual o calculado
                'signal': rsi_signal
            },
            'macd': {
                'data': macd,
                'signal': macd_signal
            },
            'bollinger': bollinger,
            'support_resistance': sr_levels,
            'volume': volume_analysis,
            'combined': combined_signal
        }
        
    except Exception as e:
        print(f"Error in technical analysis: {e}")
        return {
            'available': False,
            'error': str(e)
        }

def generate_technical_signal(rsi, macd, bollinger, sr_levels, volume):
    """Genera señal técnica combinada."""
    
    # Condiciones bullish fuertes
    if (rsi < 35 and macd['crossover'] == 'bullish' and 
        volume['ratio'] > 1.5 and bollinger['position'] == 'oversold'):
        return {
            'signal': '🚀 STRONG BUY',
            'message': 'Multiple bullish signals: Oversold RSI, MACD crossover, high volume. Strong entry opportunity.',
            'color': 'success',
            'conviction': 'high'
        }
    
    # Condiciones bearish fuertes
    elif (rsi > 70 and macd['crossover'] == 'bearish' and 
          bollinger['position'] == 'overbought'):
        return {
            'signal': '⚠️ STRONG SELL',
            'message': 'Multiple bearish signals: Overbought RSI, MACD crossover. Consider taking profits.',
            'color': 'danger',
            'conviction': 'high'
        }
    
    # Cerca de resistencia con volumen alto
    elif sr_levels['distance_to_resistance'] < 3 and volume['ratio'] > 2:
        return {
            'signal': '⏸️ WAIT AT RESISTANCE',
            'message': f'Price near resistance (${sr_levels["resistance"]:.2f}) with high volume. Wait for breakout confirmation.',
            'color': 'warning',
            'conviction': 'medium'
        }
    
    # Cerca de soporte
    elif sr_levels['distance_to_support'] < 3:
        return {
            'signal': '🎯 NEAR SUPPORT',
            'message': f'Price near support (${sr_levels["support"]:.2f}). Watch for bounce or breakdown.',
            'color': 'info',
            'conviction': 'medium'
        }
    
    # MACD bullish + volumen
    elif macd['histogram'] > 0 and volume['level'] in ['high', 'extreme']:
        return {
            'signal': '📈 BULLISH MOMENTUM',
            'message': 'MACD bullish with strong volume. Uptrend confirmed.',
            'color': 'success',
            'conviction': 'medium'
        }
    
    # Neutral
    else:
        return {
            'signal': '😐 NEUTRAL',
            'message': 'No clear technical setup. Wait for better entry/exit signals.',
            'color': 'secondary',
            'conviction': 'low'
        }

# Test
if __name__ == "__main__":
    result = analyze_stock_technical("TSLA")
    if result['available']:
        print(f"\n{result['ticker']} Technical Analysis:")
        print(f"Price: ${result['price']['current']:.2f} ({result['price']['change']:+.2f}%)")
        print(f"\nRSI: {result['rsi']['signal']['level']}")
        print(result['rsi']['signal']['message'])
        print(f"\nMACD: {result['macd']['signal']['level']}")
        print(result['macd']['signal']['message'])
        print(f"\n{result['combined']['signal']}")
        print(result['combined']['message'])