"""
pdf_export.py — Export strategy analysis as a professional PDF report.

Generates a multi-page PDF with:
  Page 1: Title page with company name and fiscal year
  Page 2-3: Strategy Map diagram (drawn with boxes and arrows like the SVG)
  Page 4: Causal Linkages
  Page 5: SWOT Analysis table
  Page 6: Financial Health Scorecard
  Page 7: Strategy Statement
"""

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import textwrap


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
NAVY = HexColor("#1a365d")
BLUE_DARK = HexColor("#2c5282")
BLUE_MED = HexColor("#2b6cb0")
BLUE_LIGHT = HexColor("#3182ce")
BLUE_SKY = HexColor("#4299e1")
GREEN = HexColor("#276749")
RED = HexColor("#c53030")
BLUE_OPP = HexColor("#2b6cb0")
GOLD = HexColor("#b7791f")
GRAY = HexColor("#718096")
LIGHT_GREEN_BG = HexColor("#f0fff4")
LIGHT_RED_BG = HexColor("#fff5f5")
LIGHT_BLUE_BG = HexColor("#ebf8ff")
LIGHT_GOLD_BG = HexColor("#fffff0")
WHITE_BG = HexColor("#ffffff")
LAYER_BG = HexColor("#f7fafc")
AMBER_BG = HexColor("#FFF2CC")
AMBER_TXT = HexColor("#7F6000")


# ---------------------------------------------------------------------------
# Strategy Map Flowable — Left-to-Right Koçak Layout
# ---------------------------------------------------------------------------
class StrategyMapDiagram(Flowable):
    """
    Draws the strategy map in LEFT-TO-RIGHT layout matching Koçak's framework:
    Resources → Activities → Value Props → Intermediate Objectives → Objective
    Uses landscape orientation with color-coded columns.
    """
    def __init__(self, smap, width=7*inch, height=8.5*inch):
        Flowable.__init__(self)
        self.smap = smap
        self.width = width
        self.height = height
        self.node_positions = {}

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        canvas = self.canv
        smap = self.smap

        # Left-to-right order
        layer_order = [
            ("Resources", smap.get("resources", []),
             HexColor("#E8D5F5"), HexColor("#C39BD3"), HexColor("#6C3483")),
            ("Activities", smap.get("activities", []),
             HexColor("#FDDEDE"), HexColor("#F1948A"), HexColor("#922B21")),
            ("Value Props", smap.get("value_propositions", []),
             HexColor("#FFF9C4"), HexColor("#F9E79F"), HexColor("#7D6608")),
            ("Intermed. Obj.", smap.get("intermediate_objectives", []),
             HexColor("#D5F5E3"), HexColor("#82E0AA"), HexColor("#1E8449")),
            ("Objective", [smap.get("final_objective", {"id": "fo1", "label": "N/A"})],
             HexColor("#D6EAF8"), HexColor("#85C1E9"), HexColor("#1A5276")),
        ]

        edges = smap.get("edges", [])

        total_w = self.width
        total_h = self.height
        n_cols = len(layer_order)
        col_w = total_w / n_cols
        margin_top = 20
        margin_bot = 10
        box_h = 32
        box_rx = 4
        text_size = 6
        label_size = 7

        node_positions = {}

        # Position nodes in vertical columns, left to right
        for col_idx, (layer_name, nodes, fill, border, txt_color) in enumerate(layer_order):
            n = len(nodes)
            if n == 0:
                continue
            col_cx = col_idx * col_w + col_w / 2
            box_w = min(col_w - 16, 110)
            node_gap = 8
            total_nodes_h = n * box_h + (n - 1) * node_gap
            start_y = total_h / 2 + total_nodes_h / 2 - box_h / 2

            for i, node in enumerate(nodes):
                nid = node.get("id", f"node_{col_idx}_{i}")
                y = start_y - i * (box_h + node_gap)
                node_positions[nid] = (col_cx, y, box_w, box_h)

        self.node_positions = node_positions

        # Draw column backgrounds + labels
        for col_idx, (layer_name, nodes, fill, border, txt_color) in enumerate(layer_order):
            x = col_idx * col_w
            canvas.setFillColor(fill)
            canvas.setFillAlpha(0.3)
            canvas.roundRect(x + 2, margin_bot, col_w - 4, total_h - margin_top - margin_bot, 6, fill=1, stroke=0)
            canvas.setFillAlpha(1.0)
            canvas.setFillColor(txt_color)
            canvas.setFont("Helvetica-Bold", label_size)
            canvas.drawCentredString(x + col_w / 2, total_h - margin_top + 2, layer_name)

        # Draw edges
        canvas.setStrokeColor(HexColor("#95a5a6"))
        canvas.setLineWidth(0.7)

        for edge in edges:
            src_id = edge.get("from", "")
            dst_id = edge.get("to", "")
            if src_id in node_positions and dst_id in node_positions:
                sx, sy, sw, sh = node_positions[src_id]
                dx, dy, dw, dh = node_positions[dst_id]

                if sx < dx:
                    start_x = sx + sw / 2
                    end_x = dx - dw / 2
                elif sx > dx:
                    start_x = sx - sw / 2
                    end_x = dx + dw / 2
                else:
                    start_x = sx
                    end_x = dx
                    if sy > dy:
                        sy -= sh / 2
                        dy += dh / 2
                    else:
                        sy += sh / 2
                        dy -= dh / 2

                canvas.setStrokeAlpha(0.4)
                ctrl = abs(end_x - start_x) * 0.35
                p = canvas.beginPath()
                p.moveTo(start_x, sy)
                p.curveTo(start_x + ctrl, sy, end_x - ctrl, dy, end_x, dy)
                canvas.drawPath(p, fill=0, stroke=1)

                # Arrowhead
                arrow_size = 3
                canvas.setFillColor(HexColor("#95a5a6"))
                canvas.setFillAlpha(0.5)
                if end_x > start_x:
                    p2 = canvas.beginPath()
                    p2.moveTo(end_x, dy)
                    p2.lineTo(end_x - arrow_size * 1.5, dy + arrow_size)
                    p2.lineTo(end_x - arrow_size * 1.5, dy - arrow_size)
                    p2.close()
                    canvas.drawPath(p2, fill=1, stroke=0)

                canvas.setStrokeAlpha(1.0)
                canvas.setFillAlpha(1.0)

        # Draw nodes
        for col_idx, (layer_name, nodes, fill, border, txt_color) in enumerate(layer_order):
            for i, node in enumerate(nodes):
                nid = node.get("id", f"node_{col_idx}_{i}")
                label = node.get("label", "N/A")
                if nid not in node_positions:
                    continue
                x, y, box_w, bh = node_positions[nid]
                canvas.setFillColor(fill)
                canvas.setStrokeColor(border)
                canvas.setLineWidth(0.8)
                canvas.roundRect(x - box_w / 2, y - bh / 2, box_w, bh, box_rx, fill=1, stroke=1)
                canvas.setFillColor(txt_color)
                canvas.setFont("Helvetica", text_size)
                wrapped = textwrap.wrap(label, width=int(box_w / (text_size * 0.42)))
                lines = wrapped[:4]
                line_height = text_size + 1.5
                start_y_text = y + ((len(lines) - 1) * line_height) / 2
                for li, line in enumerate(lines):
                    ty = start_y_text - li * line_height
                    canvas.drawCentredString(x, ty - text_size / 3, line)


def _fmt_value_pdf(val, unit):
    """Format a metric value for PDF display."""
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


def _rating_label(category, metrics):
    """Return Strong/Adequate/Weak for a category."""
    def safe(key):
        m = metrics.get(key, {})
        return m.get("value") if isinstance(m, dict) else None

    if category == "profitability":
        nm = safe("net_margin")
        roe = safe("return_on_equity")
        if nm is not None and nm > 0.10 and roe is not None and roe > 0.15:
            return "Strong", LIGHT_GREEN_BG, GREEN
        elif nm is not None and nm < 0.03:
            return "Weak", LIGHT_RED_BG, RED
    elif category == "liquidity":
        cr = safe("current_ratio")
        if cr is not None and cr > 1.5:
            return "Strong", LIGHT_GREEN_BG, GREEN
        elif cr is not None and cr < 1.0:
            return "Weak", LIGHT_RED_BG, RED
    elif category == "leverage":
        de = safe("debt_to_equity")
        if de is not None and de < 0.5:
            return "Strong", LIGHT_GREEN_BG, GREEN
        elif de is not None and de > 2.0:
            return "Weak", LIGHT_RED_BG, RED
    elif category == "growth":
        rg = safe("revenue_growth")
        if rg is not None and rg > 0.10:
            return "Strong", LIGHT_GREEN_BG, GREEN
        elif rg is not None and rg < 0.0:
            return "Weak", LIGHT_RED_BG, RED
    elif category == "efficiency":
        at = safe("asset_turnover")
        if at is not None and at > 0.8:
            return "Strong", LIGHT_GREEN_BG, GREEN
        elif at is not None and at < 0.3:
            return "Weak", LIGHT_RED_BG, RED
    elif category == "cash_flow":
        fcf = safe("free_cash_flow")
        if fcf is not None and fcf > 0:
            return "Strong", LIGHT_GREEN_BG, GREEN
        elif fcf is not None and fcf < 0:
            return "Weak", LIGHT_RED_BG, RED

    return "Adequate", AMBER_BG, AMBER_TXT


METRIC_NAMES = {
    "profitability": {
        "gross_margin": "Gross Margin",
        "operating_margin": "Operating Margin",
        "net_margin": "Net Margin",
        "return_on_equity": "ROE",
        "return_on_assets": "ROA",
    },
    "liquidity": {
        "current_ratio": "Current Ratio",
        "quick_ratio": "Quick Ratio",
    },
    "leverage": {
        "debt_to_equity": "Debt/Equity",
        "interest_coverage": "Interest Coverage",
        "debt_to_assets": "Debt/Assets",
    },
    "growth": {
        "revenue_growth": "Revenue Growth",
        "net_income_growth": "Net Income Growth",
        "fcf_growth": "FCF Growth",
    },
    "efficiency": {
        "asset_turnover": "Asset Turnover",
        "inventory_turnover": "Inventory Turnover",
        "receivables_days": "Receivables Days",
    },
    "cash_flow": {
        "operating_cash_flow": "Operating CF",
        "free_cash_flow": "Free Cash Flow",
        "capex_to_revenue": "CapEx/Revenue",
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


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"],
        fontSize=28, textColor=NAVY, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="CoverSubtitle", parent=styles["Normal"],
        fontSize=14, textColor=GRAY, alignment=TA_CENTER, spaceAfter=6))
    styles.add(ParagraphStyle(name="SectionHead", parent=styles["Heading1"],
        fontSize=18, textColor=NAVY, spaceBefore=16, spaceAfter=10))
    styles.add(ParagraphStyle(name="SubHead", parent=styles["Heading2"],
        fontSize=13, textColor=BLUE_DARK, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", parent=styles["Normal"],
        fontSize=10, textColor=black, leading=14, spaceAfter=4))
    styles.add(ParagraphStyle(name="SmallBody", parent=styles["Normal"],
        fontSize=9, textColor=black, leading=12, spaceAfter=2))
    styles.add(ParagraphStyle(name="TinyBody", parent=styles["Normal"],
        fontSize=7.5, textColor=GRAY, leading=10, spaceAfter=1))
    styles.add(ParagraphStyle(name="NodeLabel", parent=styles["Normal"],
        fontSize=9, textColor=NAVY, leading=11, spaceAfter=1))
    styles.add(ParagraphStyle(name="SwotItem", parent=styles["Normal"],
        fontSize=9, textColor=black, leading=12, spaceAfter=2,
        bulletIndent=10, leftIndent=20))
    styles.add(ParagraphStyle(name="StrategyStmt", parent=styles["Normal"],
        fontSize=12, textColor=HexColor("#2d3748"), leading=18, spaceAfter=6,
        leftIndent=20, rightIndent=20))
    styles.add(ParagraphStyle(name="Footer", parent=styles["Normal"],
        fontSize=7, textColor=GRAY, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Disclaimer", parent=styles["Normal"],
        fontSize=8, textColor=RED, leading=11, spaceAfter=4,
        leftIndent=10, rightIndent=10))

    return styles


def generate_pdf(data: dict, output_path: str) -> str:
    styles = build_styles()
    company = str(data.get("company_name", "Company"))
    fy = str(data.get("fiscal_year", ""))
    smap = data.get("strategy_map", {})
    swot = data.get("swot", {})
    stmt = data.get("strategy_statement", "Not generated.")
    fh = data.get("financial_health", {})

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
    )

    usable_width = letter[0] - 1.2 * inch

    story = []

    # --- PAGE 1 — Title Page ---
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("Strategy Analysis Report", styles["CoverTitle"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"{company}", styles["CoverTitle"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Fiscal Year {fy}", styles["CoverSubtitle"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph("Generated by Strategy Agent", styles["CoverSubtitle"]))
    story.append(Paragraph(
        "Framework: Kocak Strategic Management (Emory Goizueta)", styles["CoverSubtitle"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Analysis based solely on the company's annual report. No outside data used.",
        styles["CoverSubtitle"]))
    story.append(PageBreak())

    # --- PAGE 2 — Strategy Map ---
    story.append(Paragraph("Strategy Map", styles["SectionHead"]))
    story.append(Paragraph(
        "Resources &rarr; Activities &rarr; Value Propositions &rarr; "
        "Intermediate Objectives &rarr; Final Objective", styles["Body"]))
    story.append(Spacer(1, 4))
    diagram = StrategyMapDiagram(smap, width=usable_width, height=8.0 * inch)
    story.append(diagram)
    story.append(PageBreak())

    # --- PAGE 3 — Causal Linkages ---
    edges = smap.get("edges", [])
    if edges:
        story.append(Paragraph("Causal Linkages", styles["SectionHead"]))
        story.append(Paragraph(
            "Arrows in the strategy map represent the following causal relationships:",
            styles["Body"]))
        story.append(Spacer(1, 6))

        all_nodes = {}
        if smap.get("final_objective"):
            fo = smap["final_objective"]
            all_nodes[fo.get("id", "")] = fo.get("label", "")
        for layer_key in ["intermediate_objectives", "value_propositions",
                          "activities", "resources"]:
            for n in smap.get(layer_key, []):
                all_nodes[n.get("id", "")] = n.get("label", "")

        for edge in edges:
            src_label = all_nodes.get(edge.get("from", ""), edge.get("from", ""))
            dst_label = all_nodes.get(edge.get("to", ""), edge.get("to", ""))
            rationale = edge.get("rationale", "")
            story.append(Paragraph(
                f"<b>{src_label}</b> &rarr; <b>{dst_label}</b>: {rationale}",
                styles["SmallBody"]))

    story.append(PageBreak())

    # --- PAGE 4 — SWOT Analysis ---
    story.append(Paragraph("SWOT Analysis", styles["SectionHead"]))
    story.append(Spacer(1, 8))

    def swot_cell(items, style_name="SwotItem"):
        if not items:
            return Paragraph("<i>Not identified in report</i>", styles["SmallBody"])
        return [Paragraph(f"&bull; {item}", styles[style_name]) for item in items]

    s_items = swot_cell(swot.get("strengths", []))
    w_items = swot_cell(swot.get("weaknesses", []))
    o_items = swot_cell(swot.get("opportunities", []))
    t_items = swot_cell(swot.get("threats", []))

    half_w = usable_width / 2
    swot_data = [
        [Paragraph("<b>Strengths (Internal +)</b>", styles["SmallBody"]),
         Paragraph("<b>Weaknesses (Internal -)</b>", styles["SmallBody"])],
        [s_items, w_items],
        [Paragraph("<b>Opportunities (External +)</b>", styles["SmallBody"]),
         Paragraph("<b>Threats (External -)</b>", styles["SmallBody"])],
        [o_items, t_items],
    ]

    swot_table = Table(swot_data, colWidths=[half_w, half_w])
    swot_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), GREEN),
        ("BACKGROUND", (1, 0), (1, 0), RED),
        ("BACKGROUND", (0, 2), (0, 2), BLUE_OPP),
        ("BACKGROUND", (1, 2), (1, 2), GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("TEXTCOLOR", (0, 2), (-1, 2), white),
        ("BACKGROUND", (0, 1), (0, 1), LIGHT_GREEN_BG),
        ("BACKGROUND", (1, 1), (1, 1), LIGHT_RED_BG),
        ("BACKGROUND", (0, 3), (0, 3), LIGHT_BLUE_BG),
        ("BACKGROUND", (1, 3), (1, 3), LIGHT_GOLD_BG),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 2), (-1, 2), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 1, GRAY),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(swot_table)
    story.append(PageBreak())

    # --- PAGE 5 — Financial Health Scorecard ---
    if fh:
        story.append(Paragraph("Financial Health Scorecard", styles["SectionHead"]))
        story.append(Paragraph(
            "Metrics extracted from the annual report's financial statements.",
            styles["Body"]))
        story.append(Spacer(1, 8))

        for cat_key in ["profitability", "liquidity", "leverage", "growth",
                        "efficiency", "cash_flow"]:
            metrics = fh.get(cat_key, {})
            if not metrics:
                continue

            names = METRIC_NAMES.get(cat_key, {})
            cat_label = CATEGORY_LABELS.get(cat_key, cat_key.title())
            rl, rbg, rtxt = _rating_label(cat_key, metrics)

            story.append(Paragraph(
                f"<b>{cat_label}</b> — <font color='{'#276749' if rl == 'Strong' else '#c53030' if rl == 'Weak' else '#7F6000'}'>{rl}</font>",
                styles["SubHead"]))

            table_data = [[
                Paragraph("<b>Metric</b>", styles["TinyBody"]),
                Paragraph("<b>Current</b>", styles["TinyBody"]),
                Paragraph("<b>Prior Yr</b>", styles["TinyBody"]),
                Paragraph("<b>Commentary</b>", styles["TinyBody"]),
            ]]

            for mk, mname in names.items():
                m = metrics.get(mk, {})
                if not isinstance(m, dict):
                    continue
                val = _fmt_value_pdf(m.get("value"), m.get("unit", ""))
                prior = _fmt_value_pdf(m.get("prior_year"), m.get("unit", "")) if m.get("prior_year") is not None else "—"
                commentary = m.get("commentary", "")
                table_data.append([
                    Paragraph(mname, styles["TinyBody"]),
                    Paragraph(f"<b>{val}</b>", styles["TinyBody"]),
                    Paragraph(prior, styles["TinyBody"]),
                    Paragraph(commentary, styles["TinyBody"]),
                ])

            col_widths = [usable_width * 0.18, usable_width * 0.12,
                          usable_width * 0.12, usable_width * 0.58]
            t = Table(table_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), LAYER_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))

        # Overall assessment
        assessment = fh.get("overall_assessment", "")
        if assessment:
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>Overall Assessment</b>", styles["SubHead"]))
            story.append(Paragraph(str(assessment), styles["Body"]))

        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "<b>Disclaimer:</b> This analysis is based solely on data extracted from "
            "the company's annual report. It does not constitute financial advice. "
            "It does not account for current market price, analyst consensus, forward "
            "guidance, or macroeconomic conditions. Always do your own due diligence "
            "before making investment decisions.",
            styles["Disclaimer"]))

    story.append(PageBreak())

    # --- PAGE 6 — Strategy Statement ---
    story.append(Paragraph("Strategy Statement", styles["SectionHead"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(str(stmt), styles["StrategyStmt"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        "This analysis was generated using only information from the company's "
        "annual report. No external data sources were used.",
        styles["Body"]))

    # --- Build ---
    doc.build(story)
    return output_path


if __name__ == "__main__":
    test_data = {
        "company_name": "Test Corp",
        "fiscal_year": "2025",
        "strategy_map": {
            "final_objective": {"id": "fo1", "label": "Market leadership in cloud"},
            "intermediate_objectives": [
                {"id": "io1", "label": "Revenue growth 20% YoY"},
                {"id": "io2", "label": "Enterprise market share"},
            ],
            "value_propositions": [
                {"id": "vp1", "label": "Best-in-class reliability"},
                {"id": "vp2", "label": "Developer-friendly platform"},
            ],
            "activities": [
                {"id": "act1", "label": "R&D investment $800M"},
                {"id": "act2", "label": "Global sales operations"},
            ],
            "resources": [
                {"id": "res1", "label": "15,000 engineers"},
                {"id": "res2", "label": "Proprietary ML platform"},
                {"id": "res3", "label": "$5B cash reserves"},
            ],
            "edges": [
                {"from": "res1", "to": "act1", "rationale": "Engineers drive R&D"},
                {"from": "act1", "to": "vp2", "rationale": "R&D creates dev tools"},
                {"from": "vp1", "to": "io1", "rationale": "Reliability drives revenue"},
                {"from": "io1", "to": "fo1", "rationale": "Revenue growth leads to market leadership"},
            ],
        },
        "swot": {
            "strengths": ["Strong brand", "Cash reserves of $5B"],
            "weaknesses": ["High operating costs"],
            "opportunities": ["AI/ML market growth"],
            "threats": ["AWS and Azure competition"],
        },
        "strategy_statement": "Test Corp seeks to achieve market leadership in cloud.",
        "financial_health": {
            "profitability": {
                "gross_margin": {"value": 0.65, "prior_year": 0.62, "unit": "pct", "commentary": "Expanding margins from scale"},
                "net_margin": {"value": 0.12, "prior_year": 0.10, "unit": "pct", "commentary": "Healthy profitability"},
                "return_on_equity": {"value": 0.22, "prior_year": 0.19, "unit": "pct", "commentary": "Strong returns"},
            },
            "liquidity": {
                "current_ratio": {"value": 1.8, "prior_year": 1.6, "unit": "ratio", "commentary": "Comfortable liquidity"},
            },
            "leverage": {
                "debt_to_equity": {"value": 0.45, "prior_year": 0.50, "unit": "ratio", "commentary": "Deleveraging trend"},
            },
            "growth": {
                "revenue_growth": {"value": 0.12, "prior_year": None, "unit": "pct", "commentary": "Double digit growth"},
            },
            "efficiency": {
                "asset_turnover": {"value": 0.65, "prior_year": 0.60, "unit": "x", "commentary": "Improving"},
            },
            "cash_flow": {
                "free_cash_flow": {"value": 3100000000, "prior_year": 2900000000, "unit": "usd", "commentary": "Strong FCF generation"},
            },
            "key_financials": {
                "revenue": {"value": 42000000000, "prior_year": 37500000000, "unit": "usd"},
                "net_income": {"value": 5040000000, "prior_year": 3750000000, "unit": "usd"},
            },
            "overall_assessment": "Test Corp shows strong profitability with expanding margins and healthy free cash flow generation.",
        },
    }

    generate_pdf(test_data, "test_report.pdf")
    print("Test PDF generated: test_report.pdf")