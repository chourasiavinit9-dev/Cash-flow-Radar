# CashFlow Radar

GPU-accelerated cash-flow intelligence dashboard for freelancers and small business owners.

�� **Live demo:** https://cash-flow-radar-avg53pwdk4mxpmt6rev5tz.streamlit.app/

## What it does
CashFlow Radar ingests transaction data, cleans and aggregates it using **NVIDIA RAPIDS (cuDF)**,
detects spending anomalies, and forecasts the next 30 days of cash position — surfacing a single
Cash-Flow Risk Score and ranked alerts so users can decide, in seconds, whether a purchase or
expense is safe to make.

## Why it matters
Freelancers and small business owners often only discover a cash-flow problem after it's already
happened. This tool answers the question that actually matters: **"Can I afford this, and what
should I do about my finances right now?"**

## Tech stack
- **Data processing:** NVIDIA RAPIDS, cuDF (GPU-accelerated cleaning/aggregation)
- **Modeling:** cuML-based anomaly detection, lightweight time-series forecasting
- **Dashboard:** Streamlit + Plotly
- **No GCP dependency** — built entirely on the NVIDIA acceleration layer

## Key features
- 📊 Real-time dashboard with balance, spend trends, and risk score
- 🔮 30-day cash-flow forecast with confidence bands
- 🚨 Anomaly detection for unusual/suspicious transactions
- ⚡ Live CPU (pandas) vs GPU (cuDF) benchmark, demonstrating measurable acceleration
- 🧭 Full navigation: Dashboard, Accounts, Transactions, Analytics, Budgets, Settings

## Running locally
\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Data pipeline
Data is generated and processed in a Colab notebook (GPU-accelerated via RAPIDS), then exported
as CSV/JSON files consumed by this dashboard. See \`/data\` for sample output.

---
Built for the GenAI APAC Edition Hackathon.
