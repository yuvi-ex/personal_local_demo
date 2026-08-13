import importlib.util
from pathlib import Path

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html


_HELPER_SPEC = importlib.util.spec_from_file_location(
    "dash_server_generated_exasol_helper",
    Path(__file__).with_name("dash_server_exasol.py"),
)
assert _HELPER_SPEC is not None and _HELPER_SPEC.loader is not None
_HELPER_MODULE = importlib.util.module_from_spec(_HELPER_SPEC)
_HELPER_SPEC.loader.exec_module(_HELPER_MODULE)
load_row = _HELPER_MODULE.load_row
load_rows = _HELPER_MODULE.load_rows
has_error = _HELPER_MODULE.has_error
render_error_panel = _HELPER_MODULE.render_error_panel

# --- Design tokens (shared across this project's dashboards) ---
FONT_FAMILY = "'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
INK_PRIMARY = "#101828"
INK_SECONDARY = "#4b5262"
INK_MUTED = "#8a90a0"
SURFACE = "#ffffff"
PAGE_PLANE = "#f5f6fb"
HAIRLINE = "#e7e9f2"
BASELINE = "#c7cbdb"

BLUE = "#2a5ce6"
ORANGE = "#eb6834"
AQUA = "#1baf9a"
YELLOW = "#eda100"
MAGENTA = "#e0559e"
VIOLET = "#6a4ce0"
GOOD = "#0f9d58"
CRITICAL = "#e0304a"
HERO_BG = "linear-gradient(135deg, #eef1ff 0%, #f5f6fb 60%)"
INSIGHT_BG = "#101828"

CATEGORY_ORDER = [
    "Broad Market Equity", "Sectoral / Thematic Equity", "International Equity",
    "Gold", "Silver", "Debt / Liquid",
]
CATEGORY_COLORS = {
    "Broad Market Equity": BLUE,
    "Sectoral / Thematic Equity": ORANGE,
    "International Equity": AQUA,
    "Gold": YELLOW,
    "Silver": MAGENTA,
    "Debt / Liquid": GOOD,
}

BASE_WEIGHTS = {
    "Broad Market Equity": 0.45,
    "Sectoral / Thematic Equity": 0.15,
    "International Equity": 0.10,
    "Gold": 0.15,
    "Silver": 0.05,
    "Debt / Liquid": 0.10,
}

SHORT_DISCLAIMER = "Educational tool, not investment advice."
FULL_DISCLAIMER = (
    "Built from a single-day NSE market snapshot; past returns do not predict future performance. "
    "Please consult a SEBI-registered investment adviser before investing."
)

ALL_VALUE = "__ALL__"

CARD_STYLE = {
    "backgroundColor": SURFACE,
    "border": f"1px solid {HAIRLINE}",
    "borderRadius": "18px",
    "boxShadow": "0 2px 10px rgba(16,24,40,0.05)",
    "padding": "1.3rem 1.5rem",
}


def _stat_tile(label, value, accent, value_color=None, caption=None):
    children = [
        html.Div(style={"height": "3px", "backgroundColor": accent, "borderRadius": "3px 3px 0 0", "margin": "-1.1rem -1.3rem 1rem"}),
        html.Div(label, style={"fontSize": "11.5px", "fontWeight": 600, "letterSpacing": "0.04em", "textTransform": "uppercase", "color": INK_MUTED, "marginBottom": "0.5rem"}),
        html.Div(value, style={"fontSize": "22px", "fontWeight": 700, "color": value_color or INK_PRIMARY, "fontVariantNumeric": "tabular-nums", "lineHeight": 1.15}),
    ]
    if caption:
        children.append(html.Div(caption, style={"fontSize": "11.5px", "color": INK_MUTED, "marginTop": "0.3rem"}))
    return html.Div(children, style={**CARD_STYLE, "padding": "1.1rem 1.3rem"})


def _kpi_cards(summary_row, category_rows):
    labels = ("ETFs Tracked", "Avg 1-Year Return", "Avg 30-Day Return", "Total Daily Turnover", "Avg NAV Tracking Diff", "Top Category (1Y)")
    accents = (VIOLET, GOOD, GOOD, BLUE, VIOLET, GOOD)
    if not summary_row or has_error(summary_row):
        return [_stat_tile(label, "—", accent) for label, accent in zip(labels, accents)]

    etf_count = int(summary_row.get("ETF_COUNT") or 0)
    total_etfs = int(summary_row.get("TOTAL_ETFS") or 0)
    count_caption = None if etf_count == total_etfs else f"of {total_etfs:,} total"

    top_category_value = "—"
    if category_rows and not has_error(category_rows):
        best = max(category_rows, key=lambda r: r.get("VALUE") or -1e9)
        top_category_value = f"{best.get('LABEL')} ({(best.get('VALUE') or 0):+.0f}%)"

    avg_1y = summary_row.get("AVG_1Y") or 0
    avg_30d = summary_row.get("AVG_30D") or 0
    color_1y = GOOD if avg_1y >= 0 else CRITICAL
    color_30d = GOOD if avg_30d >= 0 else CRITICAL

    values = (
        f"{etf_count:,}",
        f"{avg_1y:+.1f}%",
        f"{avg_30d:+.1f}%",
        f"₹{(summary_row.get('TOTAL_TURNOVER_CR') or 0):,.0f} Cr",
        f"{(summary_row.get('AVG_ABS_PREMIUM') or 0):.2f}%",
        top_category_value,
    )
    value_colors = (None, color_1y, color_30d, None, None, None)
    captions = (count_caption, None, None, None, None, None)
    return [_stat_tile(label, value, accent, vc, cap) for label, value, accent, vc, cap in zip(labels, values, accents, value_colors, captions)]


def _empty_figure(message):
    figure = go.Figure()
    figure.add_annotation(text=message, showarrow=False, font={"family": FONT_FAMILY, "color": INK_MUTED, "size": 13})
    figure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320, xaxis={"visible": False}, yaxis={"visible": False}, margin={"t": 10, "r": 10, "b": 10, "l": 10})
    return figure


def _base_layout(figure, *, x_title, y_title, height=340, show_legend=False):
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        bargap=0.35,
        margin={"t": 30, "r": 30, "b": 46, "l": 130},
        font={"family": FONT_FAMILY, "color": INK_SECONDARY, "size": 12.5},
        showlegend=show_legend,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0, "font": {"size": 12.5}},
        hoverlabel={"bgcolor": SURFACE, "bordercolor": HAIRLINE, "font": {"family": FONT_FAMILY, "color": INK_PRIMARY, "size": 12.5}},
        xaxis={"title": {"text": x_title, "font": {"size": 12.5, "color": INK_MUTED}}, "showgrid": True, "gridcolor": HAIRLINE, "zeroline": True, "zerolinecolor": BASELINE, "tickfont": {"color": INK_SECONDARY, "size": 12}},
        yaxis={"title": {"text": y_title, "font": {"size": 12.5, "color": INK_MUTED}}, "showgrid": False, "tickfont": {"color": INK_SECONDARY, "size": 12.5}},
    )
    return figure


def _category_bar_figure(rows, *, source_file, x_title, value_suffix="%", decimals=1, signed=True):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No ETFs match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("VALUE") or 0, reverse=True)
    labels = [row.get("LABEL") for row in ordered]
    values = [row.get("VALUE") or 0 for row in ordered]
    colors = [CATEGORY_COLORS.get(label, INK_MUTED) for label in labels]
    sign = "+" if signed else ""
    text_labels = [f"{v:{sign}.{decimals}f}{value_suffix}" for v in values]

    figure = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker={"color": colors, "cornerradius": 8, "line": {"width": 0}},
        text=text_labels, textposition="outside",
        textfont={"size": 12.5, "color": INK_SECONDARY, "family": FONT_FAMILY}, cliponaxis=False,
        hovertemplate=f"<b>%{{y}}</b><br>{x_title}: %{{x:{sign}.{decimals}f}}{value_suffix}<extra></extra>",
    ))
    _base_layout(figure, x_title=x_title, y_title="")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    high = max(values) if values else 0
    low = min(0, min(values) if values else 0)
    span = (high - low) or 1
    figure.update_xaxes(range=[low - span * 0.05, high + span * 0.28])
    return figure


def _liquid_etfs_figure(rows, *, source_file):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No ETFs match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("VALUE") or 0, reverse=True)
    labels = [row.get("LABEL") for row in ordered]

    figure = go.Figure()
    seen_categories = []
    for row in ordered:
        category = row.get("CATEGORY")
        if category not in seen_categories:
            seen_categories.append(category)
    for category in seen_categories:
        xs = [row.get("VALUE") or 0 if row.get("CATEGORY") == category else None for row in ordered]
        figure.add_trace(go.Bar(
            x=xs, y=labels, orientation="h", name=category,
            marker={"color": CATEGORY_COLORS.get(category, INK_MUTED), "cornerradius": 8, "line": {"width": 0}},
            text=[f"₹{v:.0f} Cr" if v is not None else "" for v in xs], textposition="outside",
            textfont={"size": 12, "color": INK_SECONDARY}, cliponaxis=False,
            hovertemplate=f"<b>%{{y}}</b> ({category})<br>Daily turnover: ₹%{{x:.1f}} Cr<extra></extra>",
        ))
    _base_layout(figure, x_title="Daily Turnover (₹ Crores)", y_title="", show_legend=True)
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    all_values = [row.get("VALUE") or 0 for row in ordered]
    high = max(all_values) if all_values else 0
    figure.update_xaxes(range=[0, high * 1.28 if high else 1])
    return figure


def _movers_figure(rows, *, source_file):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No ETFs match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("VALUE") or 0, reverse=True)
    labels = [row.get("LABEL") for row in ordered]

    figure = go.Figure()
    for name, color, predicate in (("Gained", GOOD, lambda v: v >= 0), ("Declined", CRITICAL, lambda v: v < 0)):
        xs = [row.get("VALUE") if predicate(row.get("VALUE") or 0) else None for row in ordered]
        figure.add_trace(go.Bar(
            x=xs, y=labels, orientation="h", name=name,
            marker={"color": color, "cornerradius": 8, "line": {"width": 0}},
            text=[f"{v:+.0f}%" if v is not None else "" for v in xs], textposition="outside",
            textfont={"size": 12, "color": INK_SECONDARY}, cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>1-Year change: %{x:+.1f}%<extra></extra>",
        ))
    _base_layout(figure, x_title="1-Year Change (%)", y_title="", show_legend=True, height=420)
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    all_values = [row.get("VALUE") or 0 for row in ordered]
    high = max(all_values) if all_values else 0
    low = min(0, min(all_values) if all_values else 0)
    span = (high - low) or 1
    figure.update_xaxes(range=[low - span * 0.12, high + span * 0.12])
    return figure


def _allocation_figure(allocation_rows):
    if not allocation_rows:
        return _empty_figure("No allocation available for the selected filters.")
    figure = go.Figure()
    for row in allocation_rows:
        category = row.get("CATEGORY")
        pct = row.get("WEIGHT", 0) * 100
        figure.add_trace(go.Bar(
            x=[pct], y=["SIP Allocation"], orientation="h", name=category,
            marker={"color": CATEGORY_COLORS.get(category, INK_MUTED), "line": {"width": 1, "color": SURFACE}},
            text=[f"{category} {pct:.0f}%"], textposition="inside", insidetextanchor="middle",
            textfont={"size": 12, "color": "#ffffff"},
            hovertemplate=f"<b>{category}</b><br>Allocation: {pct:.0f}%<extra></extra>",
        ))
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=170, barmode="stack",
        margin={"t": 10, "r": 10, "b": 10, "l": 10}, showlegend=False,
        font={"family": FONT_FAMILY, "color": INK_SECONDARY, "size": 12.5},
        xaxis={"visible": False, "range": [0, 100]}, yaxis={"visible": False},
    )
    return figure


def _build_insight(category_rows, tracking_rows):
    if not category_rows or has_error(category_rows):
        return "Not enough data", "Select at least one category to see an insight."
    best = max(category_rows, key=lambda r: r.get("VALUE") or -1e9)
    broad = next((r for r in category_rows if r.get("LABEL") == "Broad Market Equity"), None)
    headline = f"{best.get('LABEL')} led the past year with a {(best.get('VALUE') or 0):+.0f}% average return"
    if broad and broad is not best:
        headline += f", ahead of Broad Market Equity's {(broad.get('VALUE') or 0):+.0f}%"

    support = "Strong trailing returns can tempt you to chase them — past performance never guarantees what comes next."
    if tracking_rows and not has_error(tracking_rows):
        intl = next((r for r in tracking_rows if r.get("LABEL") == "International Equity"), None)
        if intl and (intl.get("VALUE") or 0) > 3:
            support += f" International Equity ETFs also trade about {(intl.get('VALUE') or 0):.1f}% away from NAV — check the premium before buying."
    return headline, support


def _build_allocation(recommendation_rows, sip_amount):
    if not recommendation_rows or has_error(recommendation_rows):
        return []
    present = [row.get("CATEGORY") for row in recommendation_rows]
    total_weight = sum(BASE_WEIGHTS.get(cat, 0.0) for cat in present)
    if total_weight <= 0:
        equal = 1.0 / len(present)
        weights = {cat: equal for cat in present}
    else:
        weights = {cat: BASE_WEIGHTS.get(cat, 0.0) / total_weight for cat in present}
    allocation = []
    for row in recommendation_rows:
        category = row.get("CATEGORY")
        weight = weights.get(category, 0.0)
        allocation.append({**row, "WEIGHT": weight, "AMOUNT": weight * sip_amount})
    allocation.sort(key=lambda r: r["WEIGHT"], reverse=True)
    return allocation


def _recommendation_card(row, sip_amount):
    category = row.get("CATEGORY")
    accent = CATEGORY_COLORS.get(category, INK_MUTED)
    pct = row.get("WEIGHT", 0) * 100
    amount = row.get("AMOUNT", 0)
    asset = row.get("ASSET") or ""
    return html.Div(
        [
            html.Div(style={"height": "4px", "backgroundColor": accent, "borderRadius": "4px 4px 0 0", "margin": "-1.1rem -1.3rem 0.85rem"}),
            html.Div(category.upper(), style={"fontSize": "11px", "fontWeight": 700, "letterSpacing": "0.04em", "color": INK_MUTED}),
            html.Div(row.get("SYMBOL"), style={"fontSize": "19px", "fontWeight": 700, "color": INK_PRIMARY, "marginTop": "0.15rem"}),
            html.Div(asset, style={"fontSize": "12px", "color": INK_MUTED, "marginBottom": "0.75rem", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"}),
            html.Div(
                [
                    html.Div(f"{pct:.0f}% allocation", style={"fontSize": "12px", "color": INK_SECONDARY}),
                    html.Div(f"₹{amount:,.0f} / month", style={"fontSize": "18px", "fontWeight": 700, "color": accent, "fontVariantNumeric": "tabular-nums"}),
                ],
                style={"marginBottom": "0.6rem"},
            ),
            html.Div(
                [
                    html.Span(f"1Y: {(row.get('RET_365D') or 0):+.1f}%", style={"marginRight": "0.9rem"}),
                    html.Span(f"Turnover: ₹{(row.get('VALUE_CR') or 0):.0f} Cr/day", style={"marginRight": "0.9rem"}),
                    html.Span(f"Tracking diff: {(row.get('ABS_PREMIUM_PCT') or 0):.2f}%"),
                ],
                style={"fontSize": "11px", "color": INK_MUTED},
            ),
        ],
        style={**CARD_STYLE, "padding": "1.1rem 1.3rem", "flex": "1 1 240px", "minWidth": "220px"},
    )


def _chart_card(graph_id, title, subtitle, *, flex="1 1 420px"):
    return html.Div(
        [
            html.H4(title, style={"margin": 0, "fontSize": "16px", "fontWeight": 700, "color": INK_PRIMARY}),
            html.P(subtitle, style={"margin": "0.2rem 0 0", "fontSize": "12.5px", "color": INK_MUTED}),
            dcc.Graph(id=graph_id, config={"displayModeBar": False, "responsive": True}, style={"marginTop": "0.4rem", "height": "360px", "width": "100%"}),
        ],
        style={**CARD_STYLE, "flex": flex, "minWidth": "380px"},
    )


def _filter_group(title, children, *, flex, divider=True):
    style = {"flex": flex, "minWidth": "200px", "padding": "0 1.4rem"}
    if divider:
        style["borderLeft"] = f"1px solid {HAIRLINE}"
    return html.Div([html.Div(title, style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.06em", "color": INK_MUTED, "marginBottom": "0.55rem"}), *children], style=style)


def create_dash_app(server, url_base_pathname, metadata):
    app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/",
        requests_pathname_prefix=url_base_pathname.rstrip("/") + "/",
        title=metadata.get("title", "ETF SIP Advisor"),
    )
    app.index_string = """<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>html, body { margin: 0; padding: 0; }</style>
</head>
<body>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>"""

    app.layout = html.Div(
        [
            dcc.Interval(id="init-load", interval=1, max_intervals=1),
            dcc.Interval(id="refresh", interval=60_000, n_intervals=0),
            dcc.Store(id="filter-universe"),
            html.Div(
                [
                    html.Div(
                        [
                            html.H1(metadata.get("title", "ETF SIP Advisor"), style={"margin": 0, "fontSize": "30px", "fontWeight": 800, "color": INK_PRIMARY, "letterSpacing": "-0.02em"}),
                            html.P("Category performance, liquidity, and NAV tracking across NSE-listed ETFs.", style={"margin": "0.4rem 0 0", "fontSize": "14.5px", "color": INK_SECONDARY, "maxWidth": "640px"}),
                        ]
                    ),
                    html.Div(SHORT_DISCLAIMER, style={"fontSize": "12px", "color": INK_MUTED, "fontWeight": 600, "whiteSpace": "nowrap", "alignSelf": "center"}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-end", "flexWrap": "wrap", "gap": "1rem", "background": HERO_BG, "border": f"1px solid {HAIRLINE}", "borderRadius": "20px", "padding": "1.6rem 1.8rem", "marginBottom": "1.5rem"},
            ),
            html.Div(
                [
                    _filter_group("CATEGORY", [dcc.Checklist(
                        id="category-filter", options=[], value=[],
                        inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                        labelStyle={"marginRight": "14px", "fontSize": "13px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                        style={"display": "flex", "flexWrap": "wrap", "rowGap": "0.3rem"},
                    )], flex="2.2 1 420px", divider=False),
                    _filter_group("LIQUIDITY", [dcc.Checklist(
                        id="liquid-only-filter", options=[{"label": "Only liquid ETFs (≥ ₹1 Cr/day)", "value": "liquid"}], value=["liquid"],
                        inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                        labelStyle={"fontSize": "13px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                    )], flex="1.4 1 260px"),
                    html.Div(html.Button("Reset", id="reset-filters", n_clicks=0, style={"border": "none", "backgroundColor": "transparent", "color": BLUE, "fontSize": "13px", "fontWeight": 700, "cursor": "pointer", "padding": 0}), style={"flex": "0 0 auto", "alignSelf": "center", "paddingLeft": "0.5rem"}),
                ],
                style={**CARD_STYLE, "display": "flex", "flexWrap": "wrap", "alignItems": "flex-start", "padding": "1.2rem 1rem", "marginBottom": "0.6rem"},
            ),
            html.Div(id="filter-caption", style={"fontSize": "12.5px", "color": INK_MUTED, "margin": "0 0.4rem 1rem"}),
            html.Div(id="insight-panel", style={"backgroundColor": INSIGHT_BG, "borderRadius": "18px", "padding": "1.2rem 1.5rem", "marginBottom": "1.5rem"}),
            html.Div(id="kpi-row", style={"display": "grid", "gridTemplateColumns": "repeat(6, minmax(0, 1fr))", "gap": "0.85rem", "marginBottom": "1.5rem"}),
            html.Div(
                [
                    _chart_card("category-performance-chart", "1-year return by category", "Which asset class delivered the best return"),
                    _chart_card("top-liquid-chart", "Most liquid ETFs", "Highest daily turnover — safest to transact"),
                ],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"},
            ),
            html.Div([_chart_card("movers-chart", "Best & worst 1-year performers", "Top 5 gainers and top 5 decliners among filtered ETFs", flex="1 1 100%")], style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"}),
            html.Div([_chart_card("tracking-quality-chart", "NAV tracking: premium / discount", "Average distance from NAV — lower means tighter tracking")], style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.5rem"}),
            html.Div(
                [
                    html.H3("Suggested SIP allocation", style={"margin": 0, "fontSize": "18px", "fontWeight": 700, "color": INK_PRIMARY}),
                    html.P("A diversified split across your selected categories, using the most liquid ETF in each.", style={"margin": "0.2rem 0 1rem", "fontSize": "12.5px", "color": INK_MUTED}),
                    html.Div(
                        [
                            html.Label("Monthly SIP Amount (₹)", style={"fontSize": "11px", "fontWeight": 700, "letterSpacing": "0.05em", "color": INK_MUTED, "display": "block", "marginBottom": "0.4rem"}),
                            dcc.Input(id="sip-amount", type="number", value=20000, min=500, step=500, style={"fontSize": "15px", "padding": "0.45rem 0.7rem", "borderRadius": "9px", "border": f"1px solid {HAIRLINE}", "width": "160px"}),
                        ],
                        style={"marginBottom": "1rem"},
                    ),
                    dcc.Graph(id="allocation-chart", config={"displayModeBar": False, "responsive": True}, style={"height": "170px", "width": "100%", "marginBottom": "1rem"}),
                    html.Div(id="recommendation-cards", style={"display": "flex", "flexWrap": "wrap", "gap": "1rem"}),
                ],
                style={**CARD_STYLE, "marginBottom": "1rem"},
            ),
            html.Div(FULL_DISCLAIMER, style={"fontSize": "11.5px", "color": INK_MUTED, "textAlign": "center", "margin": "0.5rem 1rem 0", "lineHeight": 1.5}),
            html.Div(id="error-panel"),
        ],
        style={"fontFamily": FONT_FAMILY, "margin": "0 auto", "maxWidth": "1360px", "padding": "2rem 2rem 3rem", "backgroundColor": PAGE_PLANE, "minHeight": "100vh"},
    )

    @app.callback(
        Output("category-filter", "options"),
        Output("category-filter", "value"),
        Output("filter-universe", "data"),
        Input("init-load", "n_intervals"),
    )
    def populate_filters(_n_intervals):
        rows = load_rows(server, metadata, __file__, "queries/business/filter_options.sql")
        categories = [] if has_error(rows) else [row.get("VALUE") for row in rows]
        ordered = [c for c in CATEGORY_ORDER if c in categories] + [c for c in categories if c not in CATEGORY_ORDER]
        options = [{"label": c, "value": c} for c in ordered]
        return options, list(ordered), {"categories": ordered}

    @app.callback(
        Output("category-filter", "value", allow_duplicate=True),
        Output("liquid-only-filter", "value", allow_duplicate=True),
        Input("reset-filters", "n_clicks"),
        State("filter-universe", "data"),
        prevent_initial_call=True,
    )
    def reset_filters(_n_clicks, filter_universe):
        categories = (filter_universe or {}).get("categories", [])
        return list(categories), ["liquid"]

    @app.callback(
        Output("filter-caption", "children"),
        Output("insight-panel", "children"),
        Output("kpi-row", "children"),
        Output("category-performance-chart", "figure"),
        Output("top-liquid-chart", "figure"),
        Output("movers-chart", "figure"),
        Output("tracking-quality-chart", "figure"),
        Output("allocation-chart", "figure"),
        Output("recommendation-cards", "children"),
        Output("error-panel", "children"),
        Input("refresh", "n_intervals"),
        Input("category-filter", "value"),
        Input("liquid-only-filter", "value"),
        Input("sip-amount", "value"),
        State("filter-universe", "data"),
    )
    def refresh_dashboard(_n_intervals, category_value, liquid_only_value, sip_amount, filter_universe):
        universe = (filter_universe or {}).get("categories", [])
        selected = [c for c in (category_value or []) if c]
        if not selected or set(selected) >= set(universe):
            category_all, category_list = 1, (universe or ["__none__"])
        else:
            category_all, category_list = 0, selected
        liquid_only = 1 if "liquid" in (liquid_only_value or []) else 0
        sip_amount = sip_amount if isinstance(sip_amount, (int, float)) and sip_amount and sip_amount > 0 else 20000

        params = {"category_all": category_all, "category": category_list, "liquid_only": liquid_only}

        summary_row = load_row(server, metadata, __file__, "queries/business/summary.sql", params=params)
        category_rows = load_rows(server, metadata, __file__, "queries/business/category_performance.sql", params=params)
        top_liquid_rows = load_rows(server, metadata, __file__, "queries/business/top_liquid.sql", params=params)
        movers_rows = load_rows(server, metadata, __file__, "queries/business/top_movers.sql", params=params)
        tracking_rows = load_rows(server, metadata, __file__, "queries/business/tracking_quality.sql", params=params)
        recommendation_rows = load_rows(server, metadata, __file__, "queries/business/recommendations.sql", params=params)

        errors = []
        for label, payload in (
            ("summary", summary_row), ("category_performance", category_rows), ("top_liquid", top_liquid_rows),
            ("top_movers", movers_rows), ("tracking_quality", tracking_rows), ("recommendations", recommendation_rows),
        ):
            if has_error(payload):
                error_row = payload[0] if isinstance(payload, list) else payload
                errors.append(f"{label}: {error_row['_error']}")

        if has_error(summary_row):
            caption = "Unable to load summary for the current filters."
        else:
            etf_count = int((summary_row or {}).get("ETF_COUNT") or 0)
            total_etfs = int((summary_row or {}).get("TOTAL_ETFS") or 0)
            caption = f"Showing {etf_count:,} of {total_etfs:,} ETFs"

        headline, support = _build_insight(category_rows, tracking_rows)
        insight_children = [
            html.Div("KEY INSIGHT", style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.08em", "color": "#93a1e8", "marginBottom": "0.4rem"}),
            html.Div(headline, style={"fontSize": "17px", "fontWeight": 700, "color": "#ffffff", "lineHeight": 1.35}),
            html.Div(support, style={"fontSize": "13px", "color": "#c3c9e8", "marginTop": "0.4rem", "lineHeight": 1.5}),
        ]

        kpi_cards = _kpi_cards(summary_row, category_rows)
        category_figure = _category_bar_figure(category_rows, source_file="category_performance.sql", x_title="Average 1-Year Return")
        liquid_figure = _liquid_etfs_figure(top_liquid_rows, source_file="top_liquid.sql")
        movers_figure = _movers_figure(movers_rows, source_file="top_movers.sql")
        tracking_figure = _category_bar_figure(tracking_rows, source_file="tracking_quality.sql", x_title="Avg Distance from NAV", decimals=2, signed=False)

        allocation_rows = _build_allocation(recommendation_rows, sip_amount)
        allocation_figure = _allocation_figure(allocation_rows)
        recommendation_cards = [_recommendation_card(row, sip_amount) for row in allocation_rows] if allocation_rows else [
            html.Div("No recommendation available for the current filters.", style={"color": INK_MUTED})
        ]

        error_panel = render_error_panel("\n".join(errors)) if errors else None
        return (
            caption, insight_children, kpi_cards, category_figure, liquid_figure, movers_figure,
            tracking_figure, allocation_figure, recommendation_cards, error_panel,
        )

    return app
