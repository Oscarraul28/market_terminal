# core/bots/bot3_smart_money.py
import yfinance as yf
import pandas as pd

def get_put_call_ratio(ticker):
    """
    Calcula el Put/Call ratio de un ticker.
    Ratio > 1 = más puts que calls (bearish)
    Ratio < 1 = más calls que puts (bullish)
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Obtener opciones disponibles
        expirations = stock.options
        if not expirations:
            return None
        
        # Usar la primera fecha de expiración
        options_chain = stock.option_chain(expirations[0])
        
        calls = options_chain.calls
        puts = options_chain.puts
        
        # Volumen total
        call_volume = calls['volume'].sum()
        put_volume = puts['volume'].sum()
        
        if call_volume == 0:
            return None
        
        put_call_ratio = put_volume / call_volume
        
        return {
            'ratio': put_call_ratio,
            'put_volume': int(put_volume),
            'call_volume': int(call_volume),
            'expiration': expirations[0]
        }
    except Exception as e:
        print(f"Error getting options data: {e}")
        return None

def get_insider_activity(ticker):
    """
    Obtiene actividad de insiders (compras/ventas).
    Limitado por yfinance - datos básicos solamente.
    """
    try:
        stock = yf.Ticker(ticker)
        insider_purchases = stock.insider_purchases
        insider_trades = stock.insider_transactions
        
        if insider_trades is None or insider_trades.empty:
            return {
                'available': False,
                'net_shares': 0,
                'transactions': 0
            }
        
        # Últimas transacciones (90 días aprox)
        recent_trades = insider_trades.head(10)
        
        # Calcular net shares (compras - ventas)
        net_shares = recent_trades['Shares'].sum() if 'Shares' in recent_trades.columns else 0
        
        return {
            'available': True,
            'net_shares': int(net_shares),
            'transactions': len(recent_trades)
        }
    except Exception as e:
        print(f"Error getting insider data: {e}")
        return {
            'available': False,
            'net_shares': 0,
            'transactions': 0
        }

def analyze_smart_money(ticker):
    """
    Analiza divergencias entre smart money (institucionales) y retail.
    
    Returns:
        dict con análisis de posicionamiento
    """
    
    # Put/Call Ratio
    pc_data = get_put_call_ratio(ticker)
    
    # Insider Activity
    insider_data = get_insider_activity(ticker)
    
    # Análisis de Put/Call Ratio
    if pc_data:
        ratio = pc_data['ratio']
        
        if ratio < 0.5:
            pc_signal = {
                'level': '🔴 RETAIL FOMO EXTREMO',
                'message': f'Put/Call ratio at {ratio:.2f}. Heavy call buying indicates retail euphoria.',
                'color': 'danger',
                'sentiment': 'extreme_bullish_retail'
            }
        elif ratio < 0.7:
            pc_signal = {
                'level': '📈 BULLISH BIAS',
                'message': f'Put/Call ratio at {ratio:.2f}. More calls than puts, bullish positioning.',
                'color': 'success',
                'sentiment': 'bullish'
            }
        elif ratio < 1.3:
            pc_signal = {
                'level': '😐 NEUTRAL',
                'message': f'Put/Call ratio at {ratio:.2f}. Balanced options positioning.',
                'color': 'secondary',
                'sentiment': 'neutral'
            }
        elif ratio < 2.0:
            pc_signal = {
                'level': '📉 BEARISH BIAS',
                'message': f'Put/Call ratio at {ratio:.2f}. More puts than calls, protective positioning.',
                'color': 'warning',
                'sentiment': 'bearish'
            }
        else:
            pc_signal = {
                'level': '💀 EXTREME FEAR',
                'message': f'Put/Call ratio at {ratio:.2f}. Heavy put buying indicates fear or hedging.',
                'color': 'danger',
                'sentiment': 'extreme_bearish'
            }
    else:
        pc_signal = {
            'level': 'N/A',
            'message': 'Options data not available for this ticker.',
            'color': 'secondary',
            'sentiment': 'unknown'
        }
    
    # Análisis de Insider Activity
    if insider_data['available']:
        net_shares = insider_data['net_shares']
        
        if net_shares > 100000:
            insider_signal = {
                'level': '✅ HEAVY BUYING',
                'message': f'Insiders buying heavily ({net_shares:,} net shares). Bullish signal.',
                'color': 'success'
            }
        elif net_shares > 10000:
            insider_signal = {
                'level': '🟢 BUYING',
                'message': f'Insiders accumulating ({net_shares:,} net shares).',
                'color': 'success'
            }
        elif net_shares > -10000:
            insider_signal = {
                'level': '😐 NEUTRAL',
                'message': 'Minimal insider activity.',
                'color': 'secondary'
            }
        elif net_shares > -100000:
            insider_signal = {
                'level': '🔴 SELLING',
                'message': f'Insiders selling ({net_shares:,} net shares). Caution.',
                'color': 'warning'
            }
        else:
            insider_signal = {
                'level': '⚠️ HEAVY SELLING',
                'message': f'Insiders dumping shares ({net_shares:,} net shares). Red flag.',
                'color': 'danger'
            }
    else:
        insider_signal = {
            'level': 'N/A',
            'message': 'Insider transaction data not available.',
            'color': 'secondary'
        }
    
    # Señal combinada
    combined_signal = generate_combined_signal(pc_signal, insider_signal)
    
    return {
        'ticker': ticker.upper(),
        'put_call': {
            'data': pc_data,
            'signal': pc_signal
        },
        'insider': {
            'data': insider_data,
            'signal': insider_signal
        },
        'combined': combined_signal
    }

def generate_combined_signal(pc_signal, insider_signal):
    """
    Genera señal combinada basada en opciones e insiders.
    """
    
    # Divergencia: Retail eufórico pero insiders vendiendo
    if pc_signal['sentiment'] == 'extreme_bullish_retail' and 'SELLING' in insider_signal['level']:
        return {
            'signal': '🚨 DIVERGENCE ALERT',
            'message': 'Retail showing extreme optimism (heavy call buying) while insiders are selling. Major red flag.',
            'color': 'danger',
            'recommendation': 'Consider taking profits or avoiding entry.'
        }
    
    # Ambos bullish
    elif 'bullish' in pc_signal['sentiment'] and 'BUYING' in insider_signal['level']:
        return {
            'signal': '💪 ALIGNED BULLISH',
            'message': 'Both retail and insiders showing bullish conviction. Strong buy signal.',
            'color': 'success',
            'recommendation': 'Consider entering or adding to position.'
        }
    
    # Retail bearish pero insiders comprando
    elif 'bearish' in pc_signal['sentiment'] and 'BUYING' in insider_signal['level']:
        return {
            'signal': '🎯 CONTRARIAN OPPORTUNITY',
            'message': 'Retail fearful (heavy put buying) but insiders accumulating. Potential bottom.',
            'color': 'info',
            'recommendation': 'Watch for reversal signals.'
        }
    
    # Datos insuficientes
    elif pc_signal['level'] == 'N/A' or insider_signal['level'] == 'N/A':
        return {
            'signal': '📊 INSUFFICIENT DATA',
            'message': 'Not enough data to determine smart money positioning.',
            'color': 'secondary',
            'recommendation': 'Rely on other analysis methods.'
        }
    
    # Default: neutral
    else:
        return {
            'signal': '😐 MIXED SIGNALS',
            'message': 'No clear divergence or alignment between retail and institutional positioning.',
            'color': 'secondary',
            'recommendation': 'Wait for clearer signals.'
        }

# Test
if __name__ == "__main__":
    result = analyze_smart_money("TSLA")
    print(f"\n{result['ticker']} Smart Money Analysis:")
    print(f"\nPut/Call: {result['put_call']['signal']['level']}")
    print(result['put_call']['signal']['message'])
    print(f"\nInsider: {result['insider']['signal']['level']}")
    print(result['insider']['signal']['message'])
    print(f"\n{result['combined']['signal']}")
    print(result['combined']['message'])