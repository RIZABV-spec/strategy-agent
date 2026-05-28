# 🎯 Strategy Agent — AI-Powered Annual Report Analyzer

Built for **Strategic Management (ISOM 640)** — Prof. Koçak, Emory Goizueta EvMBA28, Summer 2026.

Upload a public company's annual report (PDF) → get a **Strategy Map** + **SWOT Analysis** powered by Claude AI.

## Quick Start (Local)

```bash
# 1. Clone / download this project
cd strategy-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
cp .env.example .env
# Edit .env and paste your key from console.anthropic.com/settings/keys

# 5. Run
streamlit run app.py
```

Opens at http://localhost:8501

## Deploy to Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set `ANTHROPIC_API_KEY` in Streamlit Cloud's Secrets manager
5. Deploy — share the URL with Prof. Koçak

## Project Structure

```
strategy-agent/
├── app.py                  # Streamlit frontend
├── src/
│   ├── pdf_parser.py       # PDF text extraction (pdfplumber)
│   ├── strategy_engine.py  # Claude API integration + prompts
│   └── visualizer.py       # Strategy map SVG + SWOT table HTML
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml
└── README.md
```

## Cost

~$0.30–0.60 per annual report analysis using Claude Sonnet.

## Strategy Framework

Based on Koçak's Session 1 framework:
- **Objective** → What do we want to accomplish?
- **Scope** → Where do we compete? (product, customer, geography, value chain)
- **Advantage** → How? (value proposition, activities, resources)
- **Sustainability** → Can the advantage survive?

Strategy Map layers (bottom → top):
Resources → Activities → Value Propositions → Intermediate Objectives → Final Objective
