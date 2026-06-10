# core/bots/bot2_flow.py
import yfinance as yf

def get_sector_performance(ticker, n_velas, interval):
    """Obtiene el cambio porcentual de un sector ETF."""
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

def analyze_flow(temporalidad="1d", n_velas=5):
    """
    Analiza el flujo de capital entre sectores y factores.
    
    Args:
        temporalidad: '1h', '4h', '1d', '1wk'
        n_velas: número de velas a analizar
    
    Returns:
        dict con análisis completo de rotación
    """
    
    # Sectores principales
    sectors = {
        'XLK': {'name': 'Technology', 'emoji': '💻'},
        'XLF': {'name': 'Financials', 'emoji': '🏦'},
        'XLE': {'name': 'Energy', 'emoji': '⚡'},
        'XLV': {'name': 'Healthcare', 'emoji': '🏥'},
        'XLY': {'name': 'Consumer Discretionary', 'emoji': '🛍️'},
        'XLP': {'name': 'Consumer Staples', 'emoji': '🛒'},
        'XLI': {'name': 'Industrials', 'emoji': '🏭'},
        'XLU': {'name': 'Utilities', 'emoji': '💡'},
    }
    
    # Factors
    factors = {
        'growth_vs_value': {
            'growth': 'IWF',  # iShares Russell 1000 Growth
            'value': 'IWD',   # iShares Russell 1000 Value
        },
        'large_vs_small': {
            'large': 'SPY',   # S&P 500
            'small': 'IWM',   # Russell 2000
        }
    }
    
    # Fetch sector data
    sector_performance = {}
    for ticker, info in sectors.items():
        change = get_sector_performance(ticker, n_velas, temporalidad)
        sector_performance[ticker] = {
            'name': info['name'],
            'emoji': info['emoji'],
            'change': change
        }
    
    # Fetch factor data
    growth = get_sector_performance(factors['growth_vs_value']['growth'], n_velas, temporalidad)
    value = get_sector_performance(factors['growth_vs_value']['value'], n_velas, temporalidad)
    large_cap = get_sector_performance(factors['large_vs_small']['large'], n_velas, temporalidad)
    small_cap = get_sector_performance(factors['large_vs_small']['small'], n_velas, temporalidad)
    
    # Ordenar sectores por performance
    sorted_sectors = sorted(
        sector_performance.items(), 
        key=lambda x: x[1]['change'], 
        reverse=True
    )
    
    # Top 3 ganadores y perdedores
    winners = sorted_sectors[:3]
    losers = sorted_sectors[-3:]
    
    # Factor analysis
    growth_vs_value_diff = growth - value
    large_vs_small_diff = large_cap - small_cap
    
    # Determinar tipo de rotación
    rotation_signal = determine_rotation_type(
        sector_performance, 
        growth_vs_value_diff, 
        large_vs_small_diff,
        large_cap,
        small_cap
    )
    
    return {
        'sectors': sector_performance,
        'winners': winners,
        'losers': losers,
        'factors': {
            'growth': growth,
            'value': value,
            'growth_vs_value': growth_vs_value_diff,
            'large_cap': large_cap,
            'small_cap': small_cap,
            'large_vs_small': large_vs_small_diff
        },
        'rotation': rotation_signal,
        'temporalidad': temporalidad,
        'n_velas': n_velas
    }

def determine_rotation_type(sectors, growth_vs_value, large_vs_small, large_cap, small_cap):
    """
    Determina el tipo de rotación y genera señal.
    
    Returns:
        dict con señal, mensaje y color
    """
    
    # Extraer performance de sectores clave
    tech = sectors.get('XLK', {}).get('change', 0)
    financials = sectors.get('XLF', {}).get('change', 0)
    energy = sectors.get('XLE', {}).get('change', 0)
    utilities = sectors.get('XLU', {}).get('change', 0)
    staples = sectors.get('XLP', {}).get('change', 0)
    discretionary = sectors.get('XLY', {}).get('change', 0)
    
    # Defensive sectors
    defensive_avg = (utilities + staples) / 2
    
    # Cyclical sectors
    cyclical_avg = (financials + energy + discretionary) / 3
    
    # Risk-on sectors
    risk_on_avg = (tech + discretionary) / 2
    
    # Lógica de rotación
    if defensive_avg > 0.01 and tech < 0 and discretionary < 0:
        return {
            'signal': '🛡️ DEFENSIVE ROTATION',
            'message': 'Capital flowing into defensive sectors (Utilities, Staples). Risk-off positioning.',
            'color': 'warning',
            'type': 'defensive'
        }
    
    elif tech > 0.02 and discretionary > 0.01 and growth_vs_value > 0.01:
        return {
            'signal': '🚀 GROWTH ROTATION',
            'message': 'Strong tech & discretionary performance. Growth stocks outperforming value. Risk-on.',
            'color': 'success',
            'type': 'growth'
        }
    
    elif financials > 0.02 and energy > 0.02 and growth_vs_value < -0.01:
        return {
            'signal': '💼 VALUE ROTATION',
            'message': 'Financials & Energy leading. Value outperforming growth. Economic recovery play.',
            'color': 'info',
            'type': 'value'
        }
    
    elif small_cap > large_cap and small_cap > 0.02:
        return {
            'signal': '📈 RISK-ON (SMALL CAPS)',
            'message': 'Small caps outperforming large caps. Aggressive risk-taking in the market.',
            'color': 'success',
            'type': 'risk_on_small'
        }
    
    elif cyclical_avg > risk_on_avg and cyclical_avg > 0.015:
        return {
            'signal': '🏭 CYCLICAL ROTATION',
            'message': 'Cyclical sectors (Financials, Energy, Industrials) leading. Recovery positioning.',
            'color': 'info',
            'type': 'cyclical'
        }
    
    elif all(sectors[ticker]['change'] < 0.005 for ticker in sectors):
        return {
            'signal': '😐 BROAD WEAKNESS',
            'message': 'Most sectors underperforming. Lack of leadership in the market.',
            'color': 'danger',
            'type': 'weakness'
        }
    
    else:
        return {
            'signal': '🔀 MIXED ROTATION',
            'message': 'No clear sector rotation pattern. Market in transition.',
            'color': 'secondary',
            'type': 'mixed'
        }

# Test
if __name__ == "__main__":
    result = analyze_flow("1d", 5)
    print(f"\n{result['rotation']['signal']}")
    print(result['rotation']['message'])
    print(f"\nTop Winners:")
    for ticker, data in result['winners']:
        print(f"  {data['emoji']} {data['name']}: {data['change']:+.2%}")
    print(f"\nTop Losers:")
    for ticker, data in result['losers']:
        print(f"  {data['emoji']} {data['name']}: {data['change']:+.2%}")
    print(f"\nGrowth vs Value: {result['factors']['growth_vs_value']:+.2%}")
    print(f"Large vs Small: {result['factors']['large_vs_small']:+.2%}")