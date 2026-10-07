# 🎯 Market Terminal

**A market analysis dashboard that aggregates five quantitative signals — from macro sentiment down to single-ticker technicals — into one clear verdict.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Online-10B981?style=for-the-badge)](https://oscar-sanchez-market-terminal.onrender.com)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-2.18-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Deployed on Render](https://img.shields.io/badge/Deployed-Render-5F5AF5?style=for-the-badge)

> **🔗 Live demo:** https://oscar-sanchez-market-terminal.onrender.com
> *Hosted on a free tier that sleeps after 15 minutes of inactivity — the first request may take up to a minute to wake the service.*

---

## What it is

Market Terminal is a Bloomberg-terminal–inspired analytics dashboard built with Django and Plotly. You enter a ticker and a timeframe; the app runs five independent analytical **bots**, renders their findings in a dark, data-dense interface, and organizes everything along the way a real analyst reasons: **macro → fundamental → technical**.

The guiding principle is a **top-down funnel**. You don't start by looking at a stock's RSI — you start by asking whether the market even wants risk right now, then whether capital is rotating toward this kind of asset, then whether this specific company is sound, and only then whether the timing is good.

---

## Features

### 📊 Section 01 — Macro Analysis
Systemic context: is the market in a risk-on or risk-off state, and where is capital flowing?

- **Bot 1 — Macro Market Sentiment.** Reads US10Y (`^TNX`), Nasdaq (`QQQ`), the dollar index (`DX-Y.NYB`), and the VIX (`^VIX`) to classify the overall risk environment as bullish, bearish, or neutral.
- **Bot 2 — Flow Analysis / Sector Rotation.** Ranks performance across the eight SPDR sector ETFs, and measures factor rotation — Growth vs. Value (`IWF`/`IWD`) and Large vs. Small cap (`SPY`/`IWM`) — to detect whether the market is rotating aggressive or defensive.

### 🧠 Section 02 — Fundamental Analysis
Who is positioning in this name, and is the underlying business actually sound?

- **Bot 3 — Smart Money vs. Retail.** Compares options positioning (put/call ratio from the live options chain) against insider transaction activity. Raises its own alert when retail is euphoric on calls while insiders are selling.
- **Bot 4 — Retail Sentiment vs. Fundamentals.** Twin Plotly gauges score crowd attention against business strength (trailing P/E, debt-to-equity, revenue growth, profit margin). *See "Current state" — the fundamentals gauge is live; the crowd-attention gauge is not yet wired to real data.*
- **⚠️ Divergence flag.** When Bot 3 and Bot 4 resolve to conflicting signals, the dashboard surfaces a warning banner — a higher-order signal that neither bot gives you alone.

### 🔬 Section 03 — Technical Analysis
Price action and entry timing for the specific ticker.

- **Bot 5 — Technical Analysis.** Price action, RSI(14), MACD, Bollinger Bands, support/resistance levels with distance-to-level, and volume analysis — combined into a single conviction read.

### Dashboard experience
- **Dark, premium UI** with a clear visual hierarchy: the headline signal is always the loudest element.
- **Semantic color system** (green = bullish, red = bearish, amber = neutral) applied consistently across every bot.
- **Sticky section navigation** with scroll-synced highlighting across the three analytical sections.
- **Typography for data:** Inter for text, JetBrains Mono for every number and metric.
- **Optional manual RSI override** for the technical section.

---

## How it works

```
   TICKER + TIMEFRAME
          │
          ▼
  ┌───────────────────────────────────────────────┐
  │  01 MACRO        Bot 1  (sentiment)            │
  │                  Bot 2  (sector / factor flow) │
  ├───────────────────────────────────────────────┤
  │  02 FUNDAMENTAL  Bot 3  (smart vs retail)      │
  │                  Bot 4  (sentiment vs funds)   │
  │                  ⚠ divergence detection        │
  ├───────────────────────────────────────────────┤
  │  03 TECHNICAL    Bot 5  (price / RSI / MACD)   │
  └───────────────────────────────────────────────┘
          │
          ▼
   RENDERED DASHBOARD  (Django template + Plotly)
```

Each bot returns a small, uniform result object — a semantic `color`, a headline `signal`, a human-readable `message`, and its supporting data — which the template renders through one shared card component. This uniformity is what makes the dashboard easy to extend: a new bot only has to speak the same shape. It is also what makes the divergence flag possible: because every bot resolves to the same semantic color vocabulary, conflicting signals can be detected generically rather than case by case.

### Caching: the macro block is ticker-independent

Bots 1 and 2 analyze the market as a whole — their output doesn't depend on which ticker you entered. A naive implementation recomputes them on every request anyway, which means downloading 16 separate one-year price series each time a user hits analyze.

They're cached instead, keyed on timeframe rather than ticker:

```
First query (cold):     21 Yahoo Finance calls
Subsequent queries:      5 Yahoo Finance calls
```

Measured locally: 11 seconds cold, under 3 seconds warm. The macro block holds for 15 minutes, per-ticker results for 5. Cache keys include the timeframe, so switching from daily to weekly correctly recomputes the macro block.

This matters more than it sounds on a shared-CPU free tier, where a request that takes a minute gets killed before it returns.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.4, Python 3.13 |
| Visualization | Plotly.js 2.18 (gauges, charts — client-side) |
| Frontend | Bootstrap 5.3, custom CSS (dark theme), Inter + JetBrains Mono |
| Market & fundamental data | yfinance 1.2.1, pandas 3.0.2, NumPy 2.4.4 |
| Serving | Gunicorn + WhiteNoise, deployed on Render |

No database beyond Django's defaults — the app holds no state between requests, so it deploys cleanly to an ephemeral filesystem. No API keys required; all market data comes from Yahoo Finance's public endpoints.

> The authoritative dependency list is in `requirements.txt`.

---

## Project structure

```
market_terminal/
├── config/                     # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                       # Main app
│   ├── bots/                   # Analytical engines (one per signal)
│   │   ├── bot1_macro.py
│   │   ├── bot2_flow.py
│   │   ├── bot3_smart_money.py
│   │   ├── bot4_retail_sentiment.py
│   │   └── bot5_stock_analysis.py
│   ├── templates/core/
│   │   └── dashboard.html      # The full dashboard UI
│   ├── utils/
│   ├── views.py                # Orchestrates the bots, handles caching
│   ├── models.py
│   └── urls.py
├── build.sh                    # Render build script
├── render.yaml                 # Render service definition
├── manage.py
├── requirements.txt
└── README.md
```

---

## Getting started (local)

```bash
# 1. Clone
git clone https://github.com/Oscarraul28/market_terminal.git
cd market_terminal

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Database (SQLite by default)
python manage.py migrate

# 5. Run
python manage.py runserver
```

Then open **http://127.0.0.1:8000** and enter a ticker (e.g. `AAPL`, `NVDA`, `SPY`).

A JSON endpoint is available at `/api/analyze/?ticker=AAPL&temporalidad=1d` for programmatic access.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev placeholder | Set a real value in production |
| `DEBUG` | `True` | Set to `False` when deployed |
| `ALLOWED_HOSTS` | localhost | Comma-separated; Render's hostname is detected automatically |
| `CACHE_TTL_MACRO` | `900` | Seconds to cache bots 1 and 2 |
| `CACHE_TTL_TICKER` | `300` | Seconds to cache bots 3, 4 and 5 |

---

## Current state

This is an active project, not a finished product. What's real and what isn't:

**Working against live data** — bots 1, 2, 3, 5, and the fundamental-strength gauge of bot 4.

**Not yet implemented** — the retail sentiment gauge in bot 4 returns a fixed placeholder value. The intent is to derive it from Google Trends search interest and Reddit mention volume, which is why `pytrends` and `praw` appear in the dependency list.

**Known limitations**

- Signal thresholds are heuristics chosen from reading, not from backtesting. They haven't been validated against historical outcomes.
- Yahoo Finance is an unofficial data source with no uptime guarantee. Each bot fails independently, so the dashboard still renders if one source goes down.

---

## Roadmap — next steps

The architecture is deliberately built so new signals slot in as additional sections or bots.

### 🎲 Bot 6 — Monte Carlo Risk Simulation *(in progress)*
A probabilistic risk engine living at the bottom of the Technical section. Rather than predicting a single price, it simulates thousands of possible future paths and reports the **distribution** of outcomes.

- **Phase 1 — Core (VaR / CVaR).** Geometric Brownian Motion with a correct physical-measure (ℙ) calibration — including the Itô drift correction (`μ = mean + ½σ²`) that most retail tools get wrong. Outputs:
  - Fan chart with 5 / 25 / 50 / 75 / 95 percentile bands.
  - **Value at Risk (VaR)** and **Conditional VaR (CVaR / Expected Shortfall)** — CVaR prioritized because it is a *coherent* risk measure (the standard under Basel III).
  - Probability of touching the Bot 5 support/resistance levels.
  - Variance-reduction (antithetic variates, Sobol sequences) and a reported standard error on the estimate itself.
- **Phase 2 — Stress testing.** The *same* engine re-run with crisis parameters (e.g. 2008-calibrated μ/σ, elevated jump intensity) to compare loss distributions under adverse scenarios.

### 🔭 Further directions
- **Master Signal** — a weighted-consensus verdict that aggregates all bots into one 0–100 conviction score (aggregation logic prototyped).
- **Real retail sentiment** — wire bot 4's crowd-attention gauge to Google Trends and Reddit, replacing the current placeholder.
- **Fat-tail realism** — Merton jump-diffusion as a toggle on Bot 6, to capture the crashes that plain GBM underestimates.
- **Backtesting** — validate the signal thresholds against historical outcomes rather than leaving them as heuristics.
- **Research flag** — rough-volatility (fractional Brownian motion, H ≈ 0.1) as an experimental v2 of the simulation engine.

> **Design note:** options pricing (risk-neutral ℚ measure) is intentionally **out of scope**. This is a single-asset risk and analysis tool under the physical measure, not a derivatives pricer — keeping those two worlds separate is a deliberate choice, not an omission.

---

## Author

**Oscar Sánchez** — Physics student @ Universidad de Guanajuato
Bridging physics and quantitative methods with financial systems and data engineering.

🔗 [linkedin.com/in/osraul](https://linkedin.com/in/osraul) · [github.com/Oscarraul28](https://github.com/Oscarraul28)

---

## Disclaimer

Market Terminal is an **educational and analytical tool**, not financial advice. Every signal is the output of a model built on simplifying assumptions, and data may be delayed or incomplete. Do your own research before making any investment decision. The Monte Carlo module, in particular, estimates a *distribution of possibilities* — it is not a forecast.

---

## License

Released under the MIT License.
