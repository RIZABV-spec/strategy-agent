"""
strategy_engine.py — The brain of the agent.

Sends annual report text to Claude with structured prompts that map directly
to the strategy framework from Prof. Koçak's Strategic Management course:

  Resources → Activities → Value Propositions → Intermediate Objectives → Final Objective

Also extracts financial health metrics from the 10-K for a scorecard evaluation.

Returns structured JSON for Strategy Map, SWOT, Strategy Statement, and Financial Health.
"""

import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------------------
# SYSTEM PROMPT — Strategy + Financial analyst persona
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a strategy analyst AI. You analyze corporate annual reports 
and extract strategic information using the following academic framework:

STRATEGY FRAMEWORK (Koçak, Emory Goizueta MBA):
1. OBJECTIVE: What does the company want to accomplish? (financial targets, 
   market position, mission)
2. SCOPE ("Where"): Where does it compete? Product markets, customer segments, 
   geographies, value chain position. What does it explicitly choose NOT to do?
3. ADVANTAGE ("How"): 
   - Customer Value Proposition: What unique value does it offer?
   - Activities: What operational activities deliver that value?
   - Resources & Capabilities: What assets/skills enable those activities?
4. SUSTAINABILITY: What makes the advantage hard to copy? (complementarities, 
   network effects, switching costs, scale, regulatory moats)

STRATEGY MAP STRUCTURE (bottom to top):
- Resources/Capabilities (bottom layer): tangible assets, IP, talent, tech, data
- Activities (second layer): key operational processes and routines  
- Value Propositions (third layer): what the customer actually gets
- Intermediate Objectives (fourth layer): market share, customer loyalty, 
  cost leadership, brand equity
- Final Objective (top): the overarching strategic goal

ARROWS between nodes represent causal/complementarity relationships — how one 
element enables or reinforces another.

You also perform financial health analysis using standard financial ratios 
and metrics extracted from the income statement, balance sheet, and cash flow 
statement found in the annual report.

RULES:
- Use ONLY information found in the provided annual report text.
- Do NOT invent, assume, or use outside knowledge about the company.
- If the report doesn't discuss something, say "Not discussed in report."
- If a financial metric cannot be calculated from available data, set its 
  value to null and note "Not available in report" in the commentary.
- Be specific — cite business segments, product names, geographies, and 
  numbers from the report.
- Each node in the strategy map should be a concise label (5-10 words max).
"""

# ---------------------------------------------------------------------------
# ANALYSIS PROMPT — Strategy Map + SWOT + Financial Health in one call
# ---------------------------------------------------------------------------
ANALYSIS_PROMPT = """Analyze this annual report text and produce FOUR outputs in JSON format.

OUTPUT 1 — STRATEGY MAP (as a node-and-edge graph):
{
  "strategy_map": {
    "final_objective": {
      "id": "fo1",
      "label": "...(the company's overarching strategic goal)..."
    },
    "intermediate_objectives": [
      {"id": "io1", "label": "..."},
      {"id": "io2", "label": "..."}
    ],
    "value_propositions": [
      {"id": "vp1", "label": "..."},
      {"id": "vp2", "label": "..."}
    ],
    "activities": [
      {"id": "act1", "label": "..."},
      {"id": "act2", "label": "..."}
    ],
    "resources": [
      {"id": "res1", "label": "..."},
      {"id": "res2", "label": "..."}
    ],
    "edges": [
      {"from": "res1", "to": "act1", "rationale": "...why this resource enables this activity..."},
      {"from": "act1", "to": "vp1", "rationale": "..."},
      {"from": "vp1", "to": "io1", "rationale": "..."},
      {"from": "io1", "to": "fo1", "rationale": "..."}
    ]
  }
}

Guidelines for the strategy map:
- Include 3-6 nodes per layer (not too sparse, not overwhelming)
- Every node must connect to at least one other node via an edge
- Edges can cross layers (e.g., a resource can link directly to a value prop)
- Include complementarity edges (horizontal links within a layer) where relevant
- Label each edge with a brief rationale

OUTPUT 2 — SWOT TABLE:
{
  "swot": {
    "strengths": ["...", "...", "..."],
    "weaknesses": ["...", "...", "..."],
    "opportunities": ["...", "...", "..."],
    "threats": ["...", "...", "..."]
  }
}

Guidelines for SWOT:
- 4-6 items per quadrant
- Each item should be one specific, concrete sentence
- Strengths/Weaknesses = internal (resources, capabilities, financials)
- Opportunities/Threats = external (market, competition, regulation, macro)
- Tie items back to specific details from the report

OUTPUT 3 — STRATEGY STATEMENT:
{
  "strategy_statement": "In one sentence: [Company] seeks to [objective] by competing in 
  [scope] through [advantage]."
}

OUTPUT 4 — FINANCIAL HEALTH SCORECARD:
Extract financial data from the income statement, balance sheet, and cash flow 
statement in the report. Calculate the following metrics. If a metric cannot be 
calculated because the required data is not in the report, set value to null.

{
  "financial_health": {
    "profitability": {
      "gross_margin": {"value": 0.45, "prior_year": 0.42, "unit": "pct", "commentary": "..."},
      "operating_margin": {"value": 0.18, "prior_year": 0.16, "unit": "pct", "commentary": "..."},
      "net_margin": {"value": 0.12, "prior_year": 0.10, "unit": "pct", "commentary": "..."},
      "return_on_equity": {"value": 0.22, "prior_year": 0.19, "unit": "pct", "commentary": "..."},
      "return_on_assets": {"value": 0.08, "prior_year": 0.07, "unit": "pct", "commentary": "..."}
    },
    "liquidity": {
      "current_ratio": {"value": 1.8, "prior_year": 1.6, "unit": "ratio", "commentary": "..."},
      "quick_ratio": {"value": 1.2, "prior_year": 1.1, "unit": "ratio", "commentary": "..."}
    },
    "leverage": {
      "debt_to_equity": {"value": 0.65, "prior_year": 0.70, "unit": "ratio", "commentary": "..."},
      "interest_coverage": {"value": 8.5, "prior_year": 7.2, "unit": "x", "commentary": "..."},
      "debt_to_assets": {"value": 0.35, "prior_year": 0.38, "unit": "pct", "commentary": "..."}
    },
    "growth": {
      "revenue_growth": {"value": 0.12, "prior_year": null, "unit": "pct", "commentary": "..."},
      "net_income_growth": {"value": 0.15, "prior_year": null, "unit": "pct", "commentary": "..."},
      "fcf_growth": {"value": 0.08, "prior_year": null, "unit": "pct", "commentary": "..."}
    },
    "efficiency": {
      "asset_turnover": {"value": 0.65, "prior_year": 0.60, "unit": "x", "commentary": "..."},
      "inventory_turnover": {"value": 5.2, "prior_year": 4.8, "unit": "x", "commentary": "..."},
      "receivables_days": {"value": 45, "prior_year": 50, "unit": "days", "commentary": "..."}
    },
    "cash_flow": {
      "operating_cash_flow": {"value": 5200000000, "prior_year": 4800000000, "unit": "usd", "commentary": "..."},
      "free_cash_flow": {"value": 3100000000, "prior_year": 2900000000, "unit": "usd", "commentary": "..."},
      "capex_to_revenue": {"value": 0.08, "prior_year": 0.07, "unit": "pct", "commentary": "..."}
    },
    "key_financials": {
      "revenue": {"value": 42000000000, "prior_year": 37500000000, "unit": "usd"},
      "net_income": {"value": 5040000000, "prior_year": 3750000000, "unit": "usd"},
      "total_assets": {"value": 63000000000, "prior_year": 58000000000, "unit": "usd"},
      "total_equity": {"value": 22900000000, "prior_year": 19700000000, "unit": "usd"},
      "total_debt": {"value": 14900000000, "prior_year": 13800000000, "unit": "usd"}
    },
    "overall_assessment": "2-3 sentence summary of the company's financial health based on the metrics above. Highlight the strongest and weakest areas. Do NOT make a buy/sell/hold recommendation — just state the financial facts."
  }
}

Guidelines for financial health:
- All percentage values should be decimals (0.45 = 45%)
- All dollar values in raw numbers (not thousands or millions)
- "prior_year" = the comparison year in the report (usually the year before the fiscal year)
- If the report only shows one year of data for a metric, set prior_year to null
- "commentary" = one sentence explaining what the number means in context
- Be precise — use the actual numbers from the financial statements, not estimates
- If the company is a bank or financial institution, note that some ratios 
  (like current ratio) may not apply in the traditional sense

Return ONLY valid JSON combining all four outputs in this structure:
{
  "company_name": "...",
  "fiscal_year": "...",
  "strategy_map": { ... },
  "swot": { ... },
  "strategy_statement": "...",
  "financial_health": { ... }
}

ANNUAL REPORT TEXT:
"""


def analyze_report(report_text: str, chunks: list[str] | None = None, model: str = "claude-sonnet-4-6") -> dict:
    if chunks and len(chunks) > 1:
        return _analyze_chunked(chunks, model)
    else:
        return _analyze_single(report_text, model)


def _analyze_single(report_text: str, model: str = "claude-sonnet-4-6") -> dict:
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": ANALYSIS_PROMPT + report_text
            }
        ]
    )
    return _parse_response(response)


def _analyze_chunked(chunks: list[str], model: str = "claude-sonnet-4-6") -> dict:
    extractions = []
    for i, chunk in enumerate(chunks):
        response = client.messages.create(
            model=model,
            max_tokens=3072,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"""This is chunk {i+1} of {len(chunks)} from an annual report.

Extract ALL strategically and financially relevant information from this chunk:
- Company objectives, mission, vision statements
- Business segments, products, services, geographies  
- Key activities and operational processes
- Resources: assets, IP, technology, talent, partnerships
- Financial highlights: revenue, margins, growth rates
- Income statement line items (revenue, COGS, gross profit, operating income, net income)
- Balance sheet items (total assets, current assets, current liabilities, total debt, equity)
- Cash flow items (operating cash flow, capex, free cash flow)
- Financial ratios if stated directly
- Competitive advantages mentioned
- Risks and challenges discussed
- Market opportunities mentioned
- Any scope decisions (what they do and don't do)

Return a structured summary. Be thorough — I need this for a full strategy AND financial analysis.

CHUNK TEXT:
{chunk}"""
                }
            ]
        )
        extractions.append(response.content[0].text)

    combined = "\n\n=== EXTRACTION FROM CHUNK ===\n\n".join(extractions)

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Below are strategic and financial extractions from different sections of an annual report.
Synthesize them into the final analysis.

{ANALYSIS_PROMPT}

EXTRACTED INFORMATION:
{combined}"""
            }
        ]
    )
    return _parse_response(response)


def _parse_response(response) -> dict:
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
        raise ValueError(f"Could not parse JSON from Claude's response: {e}\nRaw: {raw[:500]}")
