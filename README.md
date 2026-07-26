# CashFlow Radar

GPU-accelerated cash-flow intelligence dashboard for freelancers and small business owners — built for the GenAI APAC Edition Hackathon (Cohort 2).

🔗 **Live demo:** [add your Streamlit Cloud URL here]
💻 **GitHub:** https://github.com/chourasiavinit9-dev/Cash-flow-Radar

---

## What it does

CashFlow Radar turns raw transaction history into a forward-looking financial decision tool. Instead of just showing what already happened, it forecasts what's coming, flags what's suspicious, and tells you what to do about it.

- **30-day cash-flow forecast** with confidence bands
- **Cash-Flow Risk Score** (0–100) with a plain-language explanation
- **Anomaly detection**: statistical outliers, duplicate charges, and vendor spending spikes
- **CashFlow Insight** — a natural language financial assistant powered by Groq, grounded strictly in your real data, with a reliable rule-based fallback if the API is unavailable
- **Scenario Simulator** — live what-if forecasting (delay an expense, add income, add a recurring cost)
- **Smart Budget Planner** — auto-suggested budgets from historical spend, with over-budget alerts
- **Financial Reports** — CSV export and a shareable HTML report
- **Manual transaction entry** — add a transaction on the fly and see the risk score/forecast recalculate live (session-only)
- **Live CPU vs GPU benchmark** — a real, measured pandas-vs-cuDF speedup, proving the acceleration claim rather than just stating it

## Why it matters

Freelancers and small business owners typically discover a cash-flow problem only after it's already happened — bank apps and spreadsheets show history, not risk. CashFlow Radar answers the question that actually matters: **"Can I afford this, and what should I do about my finances right now?"**

## Architecture

```
[NVIDIA layer — Colab, GPU]
  RAPIDS cuDF + cuML
    → cleaning, aggregation, anomaly/fraud detection, forecasting
    → exports processed data files

[Application layer — Streamlit]
  Reads processed data only, no GPU needed at runtime
  Dashboard, Accounts, Transactions, Analytics, Budgets,
  Simulator, Reports, Settings — all fully functional

[AI + Hosting layer]
  Groq API (Llama 3.3) → CashFlow Insight, grounded + fallback-safe
  Deployed on Streamlit Community Cloud (free, no billing account required)
```

This is a deliberate, staged architecture: GPU-heavy processing happens offline (NVIDIA layer), while the always-on serving layer stays lightweight and CPU-only — the same separation a real production ML system would use. Groq was chosen for the reasoning layer specifically because its free tier requires no billing account, keeping the entire deployment cost-free and demo-reliable.

## Technology requirement compliance

Satisfies the hackathon's "2+ approved technologies" requirement entirely through the **NVIDIA acceleration layer**:
- **NVIDIA RAPIDS**
- **cuDF** (cleaning, aggregation, benchmarked directly against pandas)
- **cuML** (anomaly and fraud detection)

Groq API was layered in during the refinement round to add natural-language reasoning on top of an already-working NVIDIA-first foundation — not required to meet the base technical bar.

## Tech stack

| Layer | Technology |
|---|---|
| GPU data processing | NVIDIA RAPIDS, cuDF |
| ML / anomaly detection | cuML |
| GenAI | Groq API (Llama 3.3 70B) — free tier, no billing account required |
| Dashboard | Streamlit + Plotly |
| Deployment | Streamlit Community Cloud (free) |

## Running locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`) with your own Groq API key:
```toml
GROQ_API_KEY = "your-key-here"
```

Then run:
```bash
.venv/bin/streamlit run app.py
```

## Data pipeline

Transaction data is generated and processed in a GPU-accelerated Colab notebook using RAPIDS (cuDF/cuML), then exported as CSV/JSON files consumed by this dashboard. Sample output lives in `/data`. The dashboard itself never requires a GPU at runtime — it only reads pre-computed results, which is what allows it to deploy cleanly on Streamlit Cloud's CPU-only free tier.

## Reliability notes

- **CashFlow Insight** is built with an engineered fallback: if the Groq API is unavailable (rate limit, network issue, or misconfiguration), the app automatically shows a rule-based answer computed from the same real data, so the core experience never breaks.
- **Manual transaction entry** is session-only by design (not written to disk), consistent with the prototype's other configurable settings.

## Roadmap

Deliberately scoped out of this round, to keep the shipped feature set reliable rather than broad:
- CSV upload for user-provided transaction data
- OCR-based receipt ingestion
- Real bank account integration
- Client-level invoice and payment-delay tracking
- Multi-account support

## Built for

Built for the GenAI APAC Edition Hackathon, Cohort 2.
