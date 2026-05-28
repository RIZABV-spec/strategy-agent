"""
visualizer.py — Render the strategy map, SWOT table, and financial health as HTML.

Strategy Map: Interactive SVG with 5 layers (bottom to top):
  Resources → Activities → Value Props → Intermediate Objectives → Final Objective

SWOT: Clean 2x2 grid table.

Financial Health: Scorecard with gauge-style ratings per category.
"""

import html


def generate_strategy_map_html(data: dict) -> str:
    """
    Generate a LEFT-TO-RIGHT strategy map matching the Koçak framework:
    Resources → Activities → Value Props → Intermediate Objectives → Objective

    Each layer gets a distinct pastel color. Arrows flow left to right with
    complementarity (⊕) markers between layers. "Where" annotation boxes
    appear above the Value Props and Intermediate Objectives columns.
    """
    smap = data.get("strategy_map", {})
    company = data.get("company_name", "Company")
    fy = data.get("fiscal_year", "")

    # Layer order: LEFT to RIGHT
    layer_order = ["resources", "activities", "value_propositions",
                   "intermediate_objectives", "final_objective"]

    layers = {
        "resources": smap.get("resources", []),
        "activities": smap.get("activities", []),
        "value_propositions": smap.get("value_propositions", []),
        "intermediate_objectives": smap.get("intermediate_objectives", []),
        "final_objective": [smap.get("final_objective", {"id": "fo1", "label": "N/A"})],
    }

    edges = smap.get("edges", [])

    layer_labels = {
        "resources": "Resources",
        "activities": "Activities",
        "value_propositions": "Value Propositions",
        "intermediate_objectives": "Intermediate Objectives",
        "final_objective": "Objective",
    }

    # Koçak-style pastel colors
    layer_fill = {
        "resources": "#E8D5F5",       # lavender/purple
        "activities": "#FDDEDE",      # pink/peach
        "value_propositions": "#FFF9C4",  # yellow
        "intermediate_objectives": "#D5F5E3",  # green
        "final_objective": "#D6EAF8",  # blue
    }
    layer_border = {
        "resources": "#C39BD3",
        "activities": "#F1948A",
        "value_propositions": "#F9E79F",
        "intermediate_objectives": "#82E0AA",
        "final_objective": "#85C1E9",
    }
    layer_text = {
        "resources": "#6C3483",
        "activities": "#922B21",
        "value_propositions": "#7D6608",
        "intermediate_objectives": "#1E8449",
        "final_objective": "#1A5276",
    }

    # Layout constants
    col_width = 200
    col_gap = 80
    box_w = 160
    box_h = 60
    top_margin = 140
    left_margin = 60
    node_gap_y = 16  # vertical gap between nodes in same column

    # Calculate max nodes in any column for height
    max_nodes = max(len(layers[l]) for l in layer_order) if layer_order else 1
    svg_height = top_margin + max_nodes * (box_h + node_gap_y) + 100
    svg_width = left_margin + len(layer_order) * (col_width + col_gap) + 40

    # Position nodes: each layer is a vertical column
    node_positions = {}
    node_layer_map = {}

    for col_idx, layer_name in enumerate(layer_order):
        nodes = layers[layer_name]
        n = len(nodes)
        if n == 0:
            continue
        col_center_x = left_margin + col_idx * (col_width + col_gap) + col_width / 2
        total_h = n * box_h + (n - 1) * node_gap_y
        start_y = top_margin + (svg_height - top_margin - 80) / 2 - total_h / 2

        for i, node in enumerate(nodes):
            nid = node["id"]
            x = col_center_x
            y = start_y + i * (box_h + node_gap_y) + box_h / 2
            node_positions[nid] = (x, y)
            node_layer_map[nid] = layer_name

    svg_parts = []

    # Defs
    svg_parts.append("""
    <defs>
      <marker id="arrowhead" markerWidth="10" markerHeight="7"
              refX="10" refY="3.5" orient="auto" fill="#7f8c8d">
        <polygon points="0 0, 10 3.5, 0 7" />
      </marker>
      <filter id="shadow" x="-3%" y="-3%" width="106%" height="112%">
        <feDropShadow dx="1" dy="1" stdDeviation="2" flood-opacity="0.10"/>
      </filter>
    </defs>
    """)

    # Background
    svg_parts.append(f"""
    <rect x="0" y="0" width="{svg_width}" height="{svg_height}"
          fill="#FAFAFA" rx="8" />
    """)

    # Column background bands + labels
    for col_idx, layer_name in enumerate(layer_order):
        band_x = left_margin + col_idx * (col_width + col_gap) - 10
        band_w = col_width + 20
        fill = layer_fill[layer_name]
        border = layer_border[layer_name]
        txt_color = layer_text[layer_name]
        label = layer_labels[layer_name]

        svg_parts.append(f"""
        <rect x="{band_x}" y="{top_margin - 10}"
              width="{band_w}" height="{svg_height - top_margin - 30}"
              fill="{fill}" opacity="0.35" rx="10"
              stroke="{border}" stroke-width="1" stroke-opacity="0.3" />
        <text x="{band_x + band_w/2}" y="{top_margin - 20}"
              font-size="12" fill="{txt_color}" font-weight="700"
              text-anchor="middle" font-family="'Source Sans 3','Segoe UI',sans-serif">
          {label}
        </text>
        """)

    # "Where" annotation boxes — positioned above column headers
    where_annotations = {
        "value_propositions": (
            '"Where" does this activity\\ncreate more value\\n(e.g. for which customer)?'
        ),
        "intermediate_objectives": (
            '"Where" does the value\\ncreated lead to more sales\\n(e.g. less rivalry)?'
        ),
    }
    for layer_name, text_lines in where_annotations.items():
        col_idx = layer_order.index(layer_name)
        cx = left_margin + col_idx * (col_width + col_gap) + col_width / 2
        ann_w = 170
        ann_h = 50
        ann_y = 15  # near top of SVG

        fill = layer_fill[layer_name]
        border = layer_border[layer_name]
        txt_color = layer_text[layer_name]

        # Rounded box
        svg_parts.append(f"""
        <rect x="{cx - ann_w/2}" y="{ann_y}" width="{ann_w}" height="{ann_h}"
              fill="{fill}" stroke="{border}" stroke-width="1.5" rx="8"
              filter="url(#shadow)" />
        """)

        # Text lines
        lines = text_lines.split("\\n")
        for li, line in enumerate(lines):
            ty = ann_y + 15 + li * 13
            svg_parts.append(f"""
            <text x="{cx}" y="{ty}" font-size="9" fill="{txt_color}"
                  text-anchor="middle" font-family="'Source Sans 3','Segoe UI',sans-serif"
                  font-weight="500">{line}</text>
            """)

        # Small arrow pointing down from annotation to column header
        arrow_top = ann_y + ann_h
        arrow_bottom = top_margin - 25
        svg_parts.append(f"""
        <line x1="{cx}" y1="{arrow_top}" x2="{cx}" y2="{arrow_bottom}"
              stroke="{border}" stroke-width="1.2" stroke-dasharray="4,3" opacity="0.6" />
        <polygon points="{cx},{arrow_bottom + 6} {cx - 4},{arrow_bottom} {cx + 4},{arrow_bottom}"
                 fill="{border}" opacity="0.6" />
        """)

    # Draw edges (arrows) — left to right bezier curves
    for edge in edges:
        src = edge.get("from", "")
        dst = edge.get("to", "")
        rationale = html.escape(edge.get("rationale", ""))
        if src in node_positions and dst in node_positions:
            x1, y1 = node_positions[src]
            x2, y2 = node_positions[dst]

            # Determine direction and offset from box edge
            if x1 < x2:
                # Left to right (normal)
                start_x = x1 + box_w / 2
                end_x = x2 - box_w / 2
            elif x1 > x2:
                # Right to left (unusual, cross-layer back)
                start_x = x1 - box_w / 2
                end_x = x2 + box_w / 2
            else:
                # Same column (vertical)
                start_x = x1
                end_x = x2
                if y1 < y2:
                    y1 += box_h / 2
                    y2 -= box_h / 2
                else:
                    y1 -= box_h / 2
                    y2 += box_h / 2

            ctrl_offset = abs(end_x - start_x) * 0.4

            svg_parts.append(f"""
            <path d="M {start_x} {y1} C {start_x + ctrl_offset} {y1}, {end_x - ctrl_offset} {y2}, {end_x} {y2}"
                  stroke="#95a5a6" stroke-width="1.5" fill="none"
                  marker-end="url(#arrowhead)" opacity="0.55">
              <title>{rationale}</title>
            </path>
            """)

    # Draw nodes
    for layer_name in layer_order:
        nodes = layers[layer_name]
        fill = layer_fill[layer_name]
        border = layer_border[layer_name]
        txt_color = layer_text[layer_name]

        for node in nodes:
            nid = node["id"]
            label = html.escape(node.get("label", nid))
            if nid not in node_positions:
                continue
            x, y = node_positions[nid]

            bw = box_w
            bh = box_h
            if layer_name == "final_objective":
                bw = 170
                bh = 65

            svg_parts.append(f"""
            <g class="node" data-id="{nid}">
              <rect x="{x - bw/2}" y="{y - bh/2}"
                    width="{bw}" height="{bh}" rx="6"
                    fill="{fill}" stroke="{border}" stroke-width="1.5"
                    filter="url(#shadow)" />
              <foreignObject x="{x - bw/2}" y="{y - bh/2}"
                             width="{bw}" height="{bh}">
                <div xmlns="http://www.w3.org/1999/xhtml"
                     style="display:flex;align-items:center;justify-content:center;
                            width:100%;height:100%;text-align:center;
                            font-size:10px;color:{txt_color};font-weight:600;
                            padding:4px 8px;box-sizing:border-box;
                            line-height:1.25;overflow:hidden;
                            font-family:'Source Sans 3','Segoe UI',sans-serif;">
                  {label}
                </div>
              </foreignObject>
            </g>
            """)

    svg_content = "\n".join(svg_parts)

    return f"""
    <div style="overflow-x:auto; margin: 1rem 0; background:#FAFAFA;
                border-radius:10px; padding:1rem;">
      <h3 style="text-align:center; color:#1a365d; margin-bottom:0.3rem;
                 font-family:'Playfair Display',Georgia,serif;">
        Strategy Map — {html.escape(str(company))} {html.escape(str(fy))}
      </h3>
      <p style="text-align:center; color:#7f8c8d; font-size:0.82rem; margin-bottom:0.8rem;
                font-family:'Source Sans 3','Segoe UI',sans-serif;">
        Resources → Activities → Value Propositions → Intermediate Objectives → Objective
        &nbsp;|&nbsp; Hover over arrows to see causal rationale
      </p>
      <svg viewBox="0 0 {svg_width} {svg_height}"
           xmlns="http://www.w3.org/2000/svg"
           style="width:100%; max-width:{svg_width}px;">
        {svg_content}
      </svg>
    </div>
    """


def generate_swot_html(data: dict) -> str:
    swot = data.get("swot", {})
    company = data.get("company_name", "Company")

    def make_list(items):
        if not items:
            return "<em>Not identified in report</em>"
        return "<ul style='margin:0;padding-left:1.2rem;'>" + \
               "".join(f"<li style='margin-bottom:0.3rem;font-size:0.9rem;'>{html.escape(item)}</li>"
                       for item in items) + "</ul>"

    return f"""
    <div style="max-width:900px; margin:1.5rem auto; background:#FAFAFA;
                border-radius:10px; padding:1.5rem;">
      <h3 style="text-align:center; color:#1a365d; margin-bottom:1rem;
                 font-family:'Playfair Display',Georgia,serif;">
        SWOT Analysis — {html.escape(str(company))}
      </h3>
      <table style="width:100%; border-collapse:collapse; table-layout:fixed;">
        <thead>
          <tr>
            <th style="width:50%; background:#276749; color:white; padding:10px;
                       border:2px solid white; font-size:1rem;">
              Strengths (Internal +)
            </th>
            <th style="width:50%; background:#c53030; color:white; padding:10px;
                       border:2px solid white; font-size:1rem;">
              Weaknesses (Internal −)
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:12px; border:1px solid #e2e8f0; vertical-align:top;
                       background:#f0fff4;">
              {make_list(swot.get("strengths", []))}
            </td>
            <td style="padding:12px; border:1px solid #e2e8f0; vertical-align:top;
                       background:#fff5f5;">
              {make_list(swot.get("weaknesses", []))}
            </td>
          </tr>
          <tr>
            <th style="background:#2b6cb0; color:white; padding:10px;
                       border:2px solid white; font-size:1rem;">
              Opportunities (External +)
            </th>
            <th style="background:#b7791f; color:white; padding:10px;
                       border:2px solid white; font-size:1rem;">
              Threats (External −)
            </th>
          </tr>
          <tr>
            <td style="padding:12px; border:1px solid #e2e8f0; vertical-align:top;
                       background:#ebf8ff;">
              {make_list(swot.get("opportunities", []))}
            </td>
            <td style="padding:12px; border:1px solid #e2e8f0; vertical-align:top;
                       background:#fffff0;">
              {make_list(swot.get("threats", []))}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    """


def generate_strategy_statement_html(data: dict) -> str:
    stmt = data.get("strategy_statement", "Not generated.")
    return f"""
    <div style="max-width:800px; margin:1.5rem auto; padding:1.2rem;
                background:linear-gradient(135deg, #ebf8ff, #f0fff4);
                border-left:4px solid #2b6cb0; border-radius:6px;">
      <h4 style="color:#1a365d; margin:0 0 0.5rem 0;">Strategy Statement</h4>
      <p style="font-size:1.05rem; color:#2d3748; margin:0; line-height:1.5;">
        {html.escape(stmt)}
      </p>
    </div>
    """


# ---------------------------------------------------------------------------
# NEW — Financial Health Scorecard
# ---------------------------------------------------------------------------

def _fmt_value(val, unit):
    """Format a metric value for display."""
    if val is None:
        return "N/A"
    if unit == "pct":
        return f"{val * 100:.1f}%"
    elif unit == "ratio":
        return f"{val:.2f}"
    elif unit == "x":
        return f"{val:.1f}x"
    elif unit == "days":
        return f"{val:.0f} days"
    elif unit == "usd":
        abs_val = abs(val)
        sign = "-" if val < 0 else ""
        if abs_val >= 1_000_000_000:
            return f"{sign}${abs_val / 1_000_000_000:.1f}B"
        elif abs_val >= 1_000_000:
            return f"{sign}${abs_val / 1_000_000:.0f}M"
        elif abs_val >= 1_000:
            return f"{sign}${abs_val / 1_000:.0f}K"
        else:
            return f"{sign}${abs_val:,.0f}"
    return str(val)


def _trend_arrow(val, prior, higher_is_better=True):
    """Return an HTML arrow showing YoY direction."""
    if val is None or prior is None:
        return ""
    if val > prior:
        color = "#276749" if higher_is_better else "#c53030"
        return f'<span style="color:{color};font-size:0.85rem;">▲</span>'
    elif val < prior:
        color = "#c53030" if higher_is_better else "#276749"
        return f'<span style="color:{color};font-size:0.85rem;">▼</span>'
    else:
        return '<span style="color:#718096;font-size:0.85rem;">—</span>'


def _rating_color(category, metrics):
    """
    Assign a simple Strong/Adequate/Weak rating per category
    based on common benchmarks. Returns (label, bg_color, text_color).
    """
    # Default
    label, bg, txt = "Adequate", "#FFF2CC", "#7F6000"

    if category == "profitability":
        nm = _safe_val(metrics, "net_margin")
        roe = _safe_val(metrics, "return_on_equity")
        if nm is not None and nm > 0.10 and roe is not None and roe > 0.15:
            label, bg, txt = "Strong", "#D9EAD3", "#276749"
        elif nm is not None and nm < 0.03:
            label, bg, txt = "Weak", "#FCE4D6", "#c53030"

    elif category == "liquidity":
        cr = _safe_val(metrics, "current_ratio")
        if cr is not None and cr > 1.5:
            label, bg, txt = "Strong", "#D9EAD3", "#276749"
        elif cr is not None and cr < 1.0:
            label, bg, txt = "Weak", "#FCE4D6", "#c53030"

    elif category == "leverage":
        de = _safe_val(metrics, "debt_to_equity")
        ic = _safe_val(metrics, "interest_coverage")
        if de is not None and de < 0.5 and ic is not None and ic > 5:
            label, bg, txt = "Strong", "#D9EAD3", "#276749"
        elif de is not None and de > 2.0:
            label, bg, txt = "Weak", "#FCE4D6", "#c53030"

    elif category == "growth":
        rg = _safe_val(metrics, "revenue_growth")
        if rg is not None and rg > 0.10:
            label, bg, txt = "Strong", "#D9EAD3", "#276749"
        elif rg is not None and rg < 0.0:
            label, bg, txt = "Weak", "#FCE4D6", "#c53030"

    elif category == "efficiency":
        at = _safe_val(metrics, "asset_turnover")
        if at is not None and at > 0.8:
            label, bg, txt = "Strong", "#D9EAD3", "#276749"
        elif at is not None and at < 0.3:
            label, bg, txt = "Weak", "#FCE4D6", "#c53030"

    elif category == "cash_flow":
        fcf = _safe_val(metrics, "free_cash_flow")
        if fcf is not None and fcf > 0:
            label, bg, txt = "Strong", "#D9EAD3", "#276749"
        elif fcf is not None and fcf < 0:
            label, bg, txt = "Weak", "#FCE4D6", "#c53030"

    return label, bg, txt


def _safe_val(metrics, key):
    """Safely extract a metric value from the nested dict."""
    m = metrics.get(key, {})
    if isinstance(m, dict):
        return m.get("value")
    return None


# Map of metric keys to display names and whether higher is better
METRIC_DISPLAY = {
    "profitability": {
        "gross_margin": ("Gross Margin", True),
        "operating_margin": ("Operating Margin", True),
        "net_margin": ("Net Margin", True),
        "return_on_equity": ("Return on Equity (ROE)", True),
        "return_on_assets": ("Return on Assets (ROA)", True),
    },
    "liquidity": {
        "current_ratio": ("Current Ratio", True),
        "quick_ratio": ("Quick Ratio", True),
    },
    "leverage": {
        "debt_to_equity": ("Debt-to-Equity", False),
        "interest_coverage": ("Interest Coverage", True),
        "debt_to_assets": ("Debt-to-Assets", False),
    },
    "growth": {
        "revenue_growth": ("Revenue Growth (YoY)", True),
        "net_income_growth": ("Net Income Growth (YoY)", True),
        "fcf_growth": ("FCF Growth (YoY)", True),
    },
    "efficiency": {
        "asset_turnover": ("Asset Turnover", True),
        "inventory_turnover": ("Inventory Turnover", True),
        "receivables_days": ("Receivables Days", False),
    },
    "cash_flow": {
        "operating_cash_flow": ("Operating Cash Flow", True),
        "free_cash_flow": ("Free Cash Flow", True),
        "capex_to_revenue": ("CapEx / Revenue", False),
    },
}

CATEGORY_LABELS = {
    "profitability": "Profitability",
    "liquidity": "Liquidity",
    "leverage": "Leverage",
    "growth": "Growth",
    "efficiency": "Efficiency",
    "cash_flow": "Cash Flow",
}

CATEGORY_ICONS = {
    "profitability": "💰",
    "liquidity": "💧",
    "leverage": "⚖️",
    "growth": "📈",
    "efficiency": "⚙️",
    "cash_flow": "🏦",
}


def generate_financial_health_html(data: dict) -> str:
    """Generate the Financial Health Scorecard as HTML."""
    fh = data.get("financial_health", {})
    company = data.get("company_name", "Company")
    fy = data.get("fiscal_year", "")

    if not fh:
        return """
        <div style="max-width:900px; margin:1.5rem auto; padding:2rem; text-align:center;
                    color:#718096; font-size:1rem;">
          Financial health data was not extracted from this report.
        </div>
        """

    # --- Key financials summary bar ---
    kf = fh.get("key_financials", {})
    summary_items = []
    for key, label in [("revenue", "Revenue"), ("net_income", "Net Income"),
                       ("total_assets", "Total Assets"), ("total_equity", "Equity"),
                       ("total_debt", "Total Debt")]:
        m = kf.get(key, {})
        if isinstance(m, dict) and m.get("value") is not None:
            val = _fmt_value(m["value"], "usd")
            prior = _fmt_value(m.get("prior_year"), "usd") if m.get("prior_year") is not None else ""
            arrow = _trend_arrow(m.get("value"), m.get("prior_year"),
                                 higher_is_better=(key != "total_debt"))
            prior_html = f'<div style="font-size:0.7rem;color:#a0aec0;">Prior: {prior}</div>' if prior else ""
            summary_items.append(f"""
            <div style="text-align:center;padding:8px 12px;">
              <div style="font-size:0.75rem;color:#718096;margin-bottom:2px;">{label}</div>
              <div style="font-size:1.3rem;font-weight:600;color:#1a365d;">{val} {arrow}</div>
              {prior_html}
            </div>
            """)

    summary_bar = f"""
    <div style="display:flex;justify-content:space-around;flex-wrap:wrap;
                background:#f7fafc;border:1px solid #e2e8f0;border-radius:8px;
                padding:8px 0;margin-bottom:1.5rem;">
      {"".join(summary_items)}
    </div>
    """ if summary_items else ""

    # --- Category sections ---
    category_sections = []
    for cat_key in ["profitability", "liquidity", "leverage", "growth", "efficiency", "cash_flow"]:
        metrics = fh.get(cat_key, {})
        if not metrics:
            continue

        display_map = METRIC_DISPLAY.get(cat_key, {})
        cat_label = CATEGORY_LABELS.get(cat_key, cat_key.title())
        cat_icon = CATEGORY_ICONS.get(cat_key, "📊")
        rating_label, rating_bg, rating_txt = _rating_color(cat_key, metrics)

        rows_html = ""
        for metric_key, (metric_name, higher_better) in display_map.items():
            m = metrics.get(metric_key, {})
            if not isinstance(m, dict):
                continue

            val = m.get("value")
            prior = m.get("prior_year")
            unit = m.get("unit", "")
            commentary = html.escape(m.get("commentary", "")) if m.get("commentary") else ""

            val_str = _fmt_value(val, unit)
            prior_str = _fmt_value(prior, unit) if prior is not None else "—"
            arrow = _trend_arrow(val, prior, higher_better)

            rows_html += f"""
            <tr>
              <td style="padding:6px 10px;border-bottom:1px solid #edf2f7;font-size:0.85rem;
                         color:#2d3748;width:30%;">{metric_name}</td>
              <td style="padding:6px 10px;border-bottom:1px solid #edf2f7;font-size:0.95rem;
                         font-weight:600;color:#1a365d;text-align:right;width:15%;">
                {val_str} {arrow}
              </td>
              <td style="padding:6px 10px;border-bottom:1px solid #edf2f7;font-size:0.8rem;
                         color:#a0aec0;text-align:right;width:12%;">{prior_str}</td>
              <td style="padding:6px 10px;border-bottom:1px solid #edf2f7;font-size:0.8rem;
                         color:#718096;width:43%;">{commentary}</td>
            </tr>
            """

        category_sections.append(f"""
        <div style="margin-bottom:1.2rem;border:1px solid #e2e8f0;border-radius:8px;
                    overflow:hidden;">
          <div style="display:flex;justify-content:space-between;align-items:center;
                      background:#f7fafc;padding:8px 12px;border-bottom:1px solid #e2e8f0;">
            <span style="font-weight:600;color:#1a365d;font-size:0.95rem;">
              {cat_icon} {cat_label}
            </span>
            <span style="background:{rating_bg};color:{rating_txt};font-size:0.75rem;
                         font-weight:600;padding:2px 10px;border-radius:12px;">
              {rating_label}
            </span>
          </div>
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr style="background:#fafafa;">
                <th style="padding:4px 10px;text-align:left;font-size:0.7rem;color:#a0aec0;
                           font-weight:500;border-bottom:1px solid #edf2f7;">Metric</th>
                <th style="padding:4px 10px;text-align:right;font-size:0.7rem;color:#a0aec0;
                           font-weight:500;border-bottom:1px solid #edf2f7;">Current</th>
                <th style="padding:4px 10px;text-align:right;font-size:0.7rem;color:#a0aec0;
                           font-weight:500;border-bottom:1px solid #edf2f7;">Prior Yr</th>
                <th style="padding:4px 10px;text-align:left;font-size:0.7rem;color:#a0aec0;
                           font-weight:500;border-bottom:1px solid #edf2f7;">Commentary</th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>
        </div>
        """)

    # --- Overall assessment ---
    assessment = fh.get("overall_assessment", "")
    assessment_html = ""
    if assessment:
        assessment_html = f"""
        <div style="background:linear-gradient(135deg, #ebf8ff, #f0fff4);
                    border-left:4px solid #2b6cb0;border-radius:6px;
                    padding:1rem 1.2rem;margin-top:1rem;">
          <h4 style="color:#1a365d;margin:0 0 0.4rem 0;font-size:0.95rem;">Overall Assessment</h4>
          <p style="color:#2d3748;margin:0;font-size:0.95rem;line-height:1.5;">
            {html.escape(assessment)}
          </p>
        </div>
        """

    disclaimer = """
    <div style="margin-top:1.2rem;padding:0.8rem;background:#fff5f5;border:1px solid #fed7d7;
                border-radius:6px;font-size:0.75rem;color:#c53030;">
      <strong>Disclaimer:</strong> This analysis is based solely on data extracted from 
      the company's annual report. It does not constitute financial advice. It does not 
      account for current market price, analyst consensus, forward guidance, or 
      macroeconomic conditions. Always do your own due diligence before making investment 
      decisions.
    </div>
    """

    return f"""
    <div style="max-width:960px; margin:1rem auto; font-family:'Source Sans 3','Segoe UI',system-ui,sans-serif;
                background:#FAFAFA; border-radius:10px; padding:1.5rem;">
      <h3 style="text-align:center; color:#1a365d; margin-bottom:0.5rem;">
        Financial Health Scorecard — {html.escape(str(company))} {html.escape(str(fy))}
      </h3>
      <p style="text-align:center; color:#718096; font-size:0.85rem; margin-bottom:1.2rem;">
        Metrics extracted from the annual report's financial statements
      </p>
      {summary_bar}
      {"".join(category_sections)}
      {assessment_html}
      {disclaimer}
    </div>
    """