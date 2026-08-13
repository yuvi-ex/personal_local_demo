import importlib.util
from pathlib import Path

import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html


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

# --- Design tokens (validated palette; see dataviz skill references/palette.md) ---
FONT_FAMILY = "'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
INK_PRIMARY = "#101828"
INK_SECONDARY = "#4b5262"
INK_MUTED = "#8a90a0"
SURFACE = "#ffffff"
PAGE_PLANE = "#f5f6fb"
HAIRLINE = "#e7e9f2"
BASELINE = "#c7cbdb"

BLUE = "#2a5ce6"
BLUE_DEEP = "#1a3fb0"
ORANGE = "#eb6834"
AQUA = "#1baf9a"
YELLOW = "#eda100"
MAGENTA = "#e0559e"
VIOLET = "#6a4ce0"
GOOD = "#0f9d58"
CRITICAL = "#e0304a"
HERO_BG = "linear-gradient(135deg, #eef1ff 0%, #f5f6fb 60%)"
INSIGHT_BG = "#101828"

SEGMENT_ORDER = ["Nifty 50", "Nifty Bank", "Nifty Financial Services", "Nifty Midcap Select", "Nifty Next 50"]
SEGMENT_COLORS = {
    "Nifty 50": BLUE,
    "Nifty Bank": ORANGE,
    "Nifty Financial Services": AQUA,
    "Nifty Midcap Select": YELLOW,
    "Nifty Next 50": MAGENTA,
}

HORIZON_OPTIONS = [
    {"label": "Last 1 Year", "value": "1Y"},
    {"label": "Last 30 Days", "value": "30D"},
]
HORIZON_FIELD = {"1Y": "RET_1Y", "30D": "RET_30D"}
HORIZON_LABEL = {"1Y": "the last 1 year", "30D": "the last 30 days"}

SHORT_DISCLAIMER = "Educational tool, not investment advice."
FULL_DISCLAIMER = (
    "Built from how these segments actually moved recently. Past performance never guarantees future "
    "returns — please talk to a SEBI-registered investment adviser before investing real money."
)

CARD_STYLE = {
    "backgroundColor": SURFACE,
    "border": f"1px solid {HAIRLINE}",
    "borderRadius": "18px",
    "boxShadow": "0 2px 10px rgba(16,24,40,0.05)",
    "padding": "1.3rem 1.5rem",
}


def _format_inr(amount):
    amount = amount or 0
    negative = amount < 0
    whole = int(round(abs(amount)))
    text = str(whole)
    if len(text) <= 3:
        grouped = text
    else:
        last3 = text[-3:]
        rest = text[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        grouped = ",".join(groups) + "," + last3
    return ("-₹" if negative else "₹") + grouped


def _stat_tile(label, value, accent, value_color=None):
    return html.Div(
        [
            html.Div(style={"height": "3px", "backgroundColor": accent, "borderRadius": "3px 3px 0 0", "margin": "-1.3rem -1.5rem 1rem"}),
            html.Div(label, style={"fontSize": "11.5px", "fontWeight": 600, "letterSpacing": "0.04em", "textTransform": "uppercase", "color": INK_MUTED, "marginBottom": "0.5rem"}),
            html.Div(value, style={"fontSize": "24px", "fontWeight": 700, "color": value_color or INK_PRIMARY, "fontVariantNumeric": "tabular-nums", "lineHeight": 1.15}),
        ],
        style={**CARD_STYLE, "padding": "1.1rem 1.3rem"},
    )


def _kpi_cards(summary_rows, horizon_field, amount):
    labels = ("Segments Compared", "Best Performer", f"{_format_inr(amount)} Could Grow To", "Potential Profit", "Weakest Performer", "Most Actively Traded")
    neutral_accents = (VIOLET, GOOD, BLUE, GOOD, CRITICAL, VIOLET)
    if not summary_rows or has_error(summary_rows):
        return [_stat_tile(label, "—", accent) for label, accent in zip(labels, neutral_accents)]

    best = max(summary_rows, key=lambda r: r.get(horizon_field) or -1e9)
    worst = min(summary_rows, key=lambda r: r.get(horizon_field) or 1e9)
    most_active = max(summary_rows, key=lambda r: r.get("TURNOVER_CR") or -1e9)
    best_value = amount * (1 + (best.get(horizon_field) or 0) / 100)
    best_profit = best_value - amount
    worst_value = amount * (1 + (worst.get(horizon_field) or 0) / 100)

    values = (
        f"{len(summary_rows)} of {len(SEGMENT_ORDER)}",
        best.get("SEGMENT"),
        _format_inr(best_value),
        _format_inr(best_profit),
        f"{worst.get('SEGMENT')} ({_format_inr(worst_value)})",
        most_active.get("SEGMENT"),
    )
    profit_color = GOOD if best_profit >= 0 else CRITICAL
    accents = (VIOLET, GOOD, BLUE, profit_color, CRITICAL, VIOLET)
    value_colors = (None, GOOD, None, profit_color, CRITICAL, None)
    return [_stat_tile(label, value, accent, vc) for label, value, accent, vc in zip(labels, values, accents, value_colors)]


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
        margin={"t": 30, "r": 30, "b": 46, "l": 150},
        font={"family": FONT_FAMILY, "color": INK_SECONDARY, "size": 12.5},
        showlegend=show_legend,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0, "font": {"size": 12.5}},
        hoverlabel={"bgcolor": SURFACE, "bordercolor": HAIRLINE, "font": {"family": FONT_FAMILY, "color": INK_PRIMARY, "size": 12.5}},
        xaxis={"title": {"text": x_title, "font": {"size": 12.5, "color": INK_MUTED}}, "showgrid": True, "gridcolor": HAIRLINE, "zeroline": True, "zerolinecolor": BASELINE, "tickfont": {"color": INK_SECONDARY, "size": 12}},
        yaxis={"title": {"text": y_title, "font": {"size": 12.5, "color": INK_MUTED}}, "showgrid": False, "tickfont": {"color": INK_SECONDARY, "size": 12.5}},
    )
    return figure


def _segment_money_figure(summary_rows, *, amount, horizon_field):
    if has_error(summary_rows):
        return _empty_figure("Query failed — summary.sql")
    if not summary_rows:
        return _empty_figure("No segments selected.")
    ordered = sorted(summary_rows, key=lambda r: r.get(horizon_field) or 0, reverse=True)
    labels = [row.get("SEGMENT") for row in ordered]
    money_values = [amount * (1 + (row.get(horizon_field) or 0) / 100) for row in ordered]
    pct_values = [row.get(horizon_field) or 0 for row in ordered]
    colors = [SEGMENT_COLORS.get(label, INK_MUTED) for label in labels]
    text_labels = [_format_inr(v) for v in money_values]

    figure = go.Figure(go.Bar(
        x=money_values, y=labels, orientation="h",
        marker={"color": colors, "cornerradius": 8, "line": {"width": 0}},
        text=text_labels, textposition="outside",
        textfont={"size": 13, "color": INK_SECONDARY, "family": FONT_FAMILY}, cliponaxis=False,
        customdata=pct_values,
        hovertemplate="<b>%{y}</b><br>%{text}<br>Change: %{customdata:+.1f}%<extra></extra>",
    ))
    _base_layout(figure, x_title=f"What {_format_inr(amount)} becomes", y_title="")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    high = max(money_values) if money_values else amount
    low = min(0, min(money_values) if money_values else 0)
    span = (high - low) or 1
    figure.update_xaxes(range=[low, high + span * 0.28])
    return figure


def _horizon_compare_figure(summary_rows):
    if has_error(summary_rows):
        return _empty_figure("Query failed — summary.sql")
    if not summary_rows:
        return _empty_figure("No segments selected.")
    ordered = sorted(summary_rows, key=lambda r: r.get("RET_1Y") or 0, reverse=True)
    labels = [row.get("SEGMENT") for row in ordered]

    figure = go.Figure()
    for name, color, field in (("Last 1 Year", BLUE, "RET_1Y"), ("Last 30 Days", VIOLET, "RET_30D")):
        values = [row.get(field) or 0 for row in ordered]
        figure.add_trace(go.Bar(
            x=values, y=labels, orientation="h", name=name,
            marker={"color": color, "cornerradius": 6, "line": {"width": 0}},
            text=[f"{v:+.1f}%" for v in values], textposition="outside",
            textfont={"size": 11.5, "color": INK_SECONDARY}, cliponaxis=False,
            hovertemplate=f"<b>%{{y}}</b><br>{name}: %{{x:+.1f}}%<extra></extra>",
        ))
    _base_layout(figure, x_title="Change (%)", y_title="", show_legend=True, height=380)
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    all_values = [row.get("RET_1Y") or 0 for row in ordered] + [row.get("RET_30D") or 0 for row in ordered]
    high = max(all_values) if all_values else 0
    low = min(0, min(all_values) if all_values else 0)
    span = (high - low) or 1
    figure.update_xaxes(range=[low - span * 0.15, high + span * 0.15])
    return figure


def _stock_movers_figure(constituent_rows, *, amount, horizon_field):
    if has_error(constituent_rows):
        return _empty_figure("Query failed — constituents.sql")
    if not constituent_rows:
        return _empty_figure("No stocks match the selected filters.")
    ranked = sorted(constituent_rows, key=lambda r: r.get(horizon_field) or 0, reverse=True)
    top = ranked[:5]
    bottom = list(reversed(ranked[-5:])) if len(ranked) > 5 else []
    seen = {row.get("SYMBOL") for row in top}
    bottom = [row for row in bottom if row.get("SYMBOL") not in seen]
    picked = sorted(top + bottom, key=lambda r: r.get(horizon_field) or 0, reverse=True)
    labels = [row.get("SYMBOL") for row in picked]

    figure = go.Figure()
    for name, color, predicate in (("Gained value", GOOD, lambda v: v >= 0), ("Lost value", CRITICAL, lambda v: v < 0)):
        xs = []
        texts = []
        for row in picked:
            pct = row.get(horizon_field) or 0
            if predicate(pct):
                money = amount * (1 + pct / 100)
                xs.append(money)
                texts.append(_format_inr(money))
            else:
                xs.append(None)
                texts.append("")
        figure.add_trace(go.Bar(
            x=xs, y=labels, orientation="h", name=name,
            marker={"color": color, "cornerradius": 8, "line": {"width": 0}},
            text=texts, textposition="outside",
            textfont={"size": 12, "color": INK_SECONDARY}, cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
        ))
    _base_layout(figure, x_title=f"What {_format_inr(amount)} becomes", y_title="", show_legend=True, height=420)
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    all_money = [amount * (1 + (row.get(horizon_field) or 0) / 100) for row in picked]
    high = max(all_money) if all_money else amount
    low = min(all_money) if all_money else 0
    span = (high - low) or 1
    figure.update_xaxes(range=[low - span * 0.12, high + span * 0.12])
    return figure


def _turnover_figure(summary_rows):
    if has_error(summary_rows):
        return _empty_figure("Query failed — summary.sql")
    if not summary_rows:
        return _empty_figure("No segments selected.")
    ordered = sorted(summary_rows, key=lambda r: r.get("TURNOVER_CR") or 0, reverse=True)
    labels = [row.get("SEGMENT") for row in ordered]
    values = [row.get("TURNOVER_CR") or 0 for row in ordered]
    colors = [SEGMENT_COLORS.get(label, INK_MUTED) for label in labels]
    text_labels = [f"₹{v:,.0f} Cr/day" for v in values]

    figure = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker={"color": colors, "cornerradius": 8, "line": {"width": 0}},
        text=text_labels, textposition="outside",
        textfont={"size": 12.5, "color": INK_SECONDARY}, cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    ))
    _base_layout(figure, x_title="₹ Crores traded per day", y_title="")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    high = max(values) if values else 0
    figure.update_xaxes(range=[0, high * 1.3 if high else 1])
    return figure


def _build_insight(summary_rows, horizon_field, horizon_label, amount):
    if not summary_rows or has_error(summary_rows):
        return "Not enough data", "Select at least one segment to see an insight."
    best = max(summary_rows, key=lambda r: r.get(horizon_field) or -1e9)
    worst = min(summary_rows, key=lambda r: r.get(horizon_field) or 1e9)
    best_value = amount * (1 + (best.get(horizon_field) or 0) / 100)
    best_profit = best_value - amount
    worst_value = amount * (1 + (worst.get(horizon_field) or 0) / 100)
    worst_profit = worst_value - amount

    if best_profit >= 0:
        headline = f"{best.get('SEGMENT')} turned {_format_inr(amount)} into {_format_inr(best_value)} — a {_format_inr(best_profit)} profit"
    else:
        headline = f"Even the best, {best.get('SEGMENT')}, turned {_format_inr(amount)} into just {_format_inr(best_value)}"

    if worst.get("SEGMENT") == best.get("SEGMENT"):
        support = "Past performance never guarantees the future — spreading across segments beats betting on one."
    elif worst_profit < 0:
        support = f"{worst.get('SEGMENT')} was weakest, shrinking to {_format_inr(worst_value)}. Spreading across segments beats betting on one."
    else:
        support = f"Even {worst.get('SEGMENT')}, the weakest, still grew to {_format_inr(worst_value)}."
    return headline, support


def _build_scenarios(summary_rows, horizon_field, amount):
    if not summary_rows or has_error(summary_rows):
        return []
    by_segment = {row.get("SEGMENT"): row for row in summary_rows}
    scenarios = []

    if "Nifty 50" in by_segment:
        row = by_segment["Nifty 50"]
        value = amount * (1 + (row.get(horizon_field) or 0) / 100)
        scenarios.append({
            "title": "Play It Safe", "subtitle": "Nifty 50",
            "desc": "India's 50 biggest companies — the calmest option.",
            "value": value, "profit": value - amount, "color": SEGMENT_COLORS["Nifty 50"],
        })

    best = max(summary_rows, key=lambda r: r.get(horizon_field) or -1e9)
    if best.get("SEGMENT") != "Nifty 50" or "Nifty 50" not in by_segment:
        value = amount * (1 + (best.get(horizon_field) or 0) / 100)
        scenarios.append({
            "title": "Go For Growth", "subtitle": best.get("SEGMENT"),
            "desc": "This period's top performer — more reward, more risk.",
            "value": value, "profit": value - amount, "color": SEGMENT_COLORS.get(best.get("SEGMENT"), INK_MUTED),
        })

    avg_return = sum((row.get(horizon_field) or 0) for row in summary_rows) / len(summary_rows)
    value = amount * (1 + avg_return / 100)
    scenarios.append({
        "title": "Spread It Out", "subtitle": f"{len(summary_rows)} segments, equal split",
        "desc": "A little in each pick — smooths out the bumps.",
        "value": value, "profit": value - amount, "color": VIOLET,
    })
    return scenarios


def _scenario_card(scenario):
    profit = scenario["profit"]
    profit_color = GOOD if profit >= 0 else CRITICAL
    profit_label = f"+{_format_inr(profit)} profit" if profit >= 0 else f"{_format_inr(profit)} loss"
    return html.Div(
        [
            html.Div(style={"height": "4px", "backgroundColor": scenario["color"], "borderRadius": "4px 4px 0 0", "margin": "-1.1rem -1.3rem 0.85rem"}),
            html.Div(scenario["title"], style={"fontSize": "14.5px", "fontWeight": 700, "color": INK_PRIMARY}),
            html.Div(scenario["subtitle"], style={"fontSize": "12px", "fontWeight": 600, "color": scenario["color"], "marginTop": "0.1rem", "marginBottom": "0.6rem"}),
            html.Div(scenario["desc"], style={"fontSize": "12px", "color": INK_MUTED, "marginBottom": "0.85rem", "lineHeight": 1.4}),
            html.Div(_format_inr(scenario["value"]), style={"fontSize": "23px", "fontWeight": 700, "color": INK_PRIMARY, "fontVariantNumeric": "tabular-nums"}),
            html.Div(profit_label, style={"fontSize": "12.5px", "fontWeight": 600, "color": profit_color, "marginTop": "0.15rem"}),
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
    style = {"flex": flex, "minWidth": "180px", "padding": "0 1.4rem"}
    if divider:
        style["borderLeft"] = f"1px solid {HAIRLINE}"
    return html.Div(
        [
            html.Div(title, style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.06em", "color": INK_MUTED, "marginBottom": "0.55rem"}),
            *children,
        ],
        style=style,
    )


def create_dash_app(server, url_base_pathname, metadata):
    app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/",
        requests_pathname_prefix=url_base_pathname.rstrip("/") + "/",
        title=metadata.get("title", "Nifty Wealth Advisor"),
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
            dcc.Interval(id="refresh", interval=60_000, n_intervals=0),
            html.Div(
                [
                    html.Div(
                        [
                            html.H1(
                                metadata.get("title", "Nifty Wealth Advisor"),
                                style={"margin": 0, "fontSize": "30px", "fontWeight": 800, "color": INK_PRIMARY, "letterSpacing": "-0.02em"},
                            ),
                            html.P(
                                "What your money could be worth across 5 Nifty segments — in rupees, not just percentages.",
                                style={"margin": "0.4rem 0 0", "fontSize": "14.5px", "color": INK_SECONDARY, "maxWidth": "640px"},
                            ),
                        ]
                    ),
                    html.Div(SHORT_DISCLAIMER, style={"fontSize": "12px", "color": INK_MUTED, "fontWeight": 600, "whiteSpace": "nowrap", "alignSelf": "center"}),
                ],
                style={
                    "display": "flex", "justifyContent": "space-between", "alignItems": "flex-end", "flexWrap": "wrap", "gap": "1rem",
                    "background": HERO_BG, "border": f"1px solid {HAIRLINE}", "borderRadius": "20px",
                    "padding": "1.6rem 1.8rem", "marginBottom": "1.5rem",
                },
            ),
            html.Div(
                [
                    _filter_group(
                        "MARKET SEGMENTS",
                        [dcc.Checklist(
                            id="segment-filter",
                            options=[{"label": s, "value": s} for s in SEGMENT_ORDER],
                            value=list(SEGMENT_ORDER),
                            inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                            labelStyle={"marginRight": "16px", "fontSize": "13.5px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                            style={"display": "flex", "flexWrap": "wrap", "rowGap": "0.35rem"},
                        )],
                        flex="2 1 420px", divider=False,
                    ),
                    _filter_group(
                        "TIME PERIOD",
                        [dcc.RadioItems(
                            id="horizon-filter", options=HORIZON_OPTIONS, value="1Y",
                            inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                            labelStyle={"marginRight": "16px", "fontSize": "13.5px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                        )],
                        flex="1 1 220px",
                    ),
                    _filter_group(
                        "INVEST AMOUNT (₹)",
                        [dcc.Input(id="invest-amount", type="number", value=50000, min=500, step=500, style={"fontSize": "15px", "padding": "0.45rem 0.7rem", "borderRadius": "9px", "border": f"1px solid {HAIRLINE}", "width": "150px"})],
                        flex="1 1 180px",
                    ),
                    html.Div(
                        html.Button(
                            "Reset", id="reset-filters", n_clicks=0,
                            style={"border": "none", "backgroundColor": "transparent", "color": BLUE, "fontSize": "13px", "fontWeight": 700, "cursor": "pointer", "padding": 0},
                        ),
                        style={"flex": "0 0 auto", "alignSelf": "center", "paddingLeft": "0.5rem"},
                    ),
                ],
                style={**CARD_STYLE, "display": "flex", "flexWrap": "wrap", "alignItems": "flex-start", "padding": "1.2rem 1rem", "marginBottom": "0.6rem"},
            ),
            html.Div(id="filter-caption", style={"fontSize": "12.5px", "color": INK_MUTED, "margin": "0 0.4rem 1rem"}),
            html.Div(
                id="insight-panel",
                style={
                    "backgroundColor": INSIGHT_BG, "borderRadius": "18px", "padding": "1.2rem 1.5rem", "marginBottom": "1.5rem",
                },
            ),
            html.Div(id="kpi-row", style={"display": "grid", "gridTemplateColumns": "repeat(6, minmax(0, 1fr))", "gap": "0.85rem", "marginBottom": "1.5rem"}),
            html.Div(
                [_chart_card("segment-money-chart", "Which segment grew your money the most?", "What your investment is worth today, by segment", flex="1 1 100%")],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"},
            ),
            html.Div(
                [
                    _chart_card("horizon-compare-chart", "1 year vs 30 days", "Consistent performers are the safer bet"),
                    _chart_card("turnover-chart", "Where people trade the most", "More activity, easier to buy and sell"),
                ],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"},
            ),
            html.Div(
                [_chart_card("stock-movers-chart", "Best & worst individual stocks", "Single stocks swing far more than a whole segment", flex="1 1 100%")],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.5rem"},
            ),
            html.Div(
                [
                    html.H3("If you invest today", style={"margin": 0, "fontSize": "18px", "fontWeight": 700, "color": INK_PRIMARY}),
                    html.P("Three simple ways to use your money.", style={"margin": "0.2rem 0 1rem", "fontSize": "12.5px", "color": INK_MUTED}),
                    html.Div(id="scenario-cards", style={"display": "flex", "flexWrap": "wrap", "gap": "1rem"}),
                ],
                style={**CARD_STYLE, "marginBottom": "1rem"},
            ),
            html.Div(FULL_DISCLAIMER, style={"fontSize": "11.5px", "color": INK_MUTED, "textAlign": "center", "margin": "0.5rem 1rem 0", "lineHeight": 1.5}),
            html.Div(id="error-panel"),
        ],
        style={"fontFamily": FONT_FAMILY, "margin": "0 auto", "maxWidth": "1360px", "padding": "2rem 2rem 3rem", "backgroundColor": PAGE_PLANE, "minHeight": "100vh"},
    )

    @app.callback(
        Output("segment-filter", "value", allow_duplicate=True),
        Output("horizon-filter", "value", allow_duplicate=True),
        Output("invest-amount", "value", allow_duplicate=True),
        Input("reset-filters", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_filters(_n_clicks):
        return list(SEGMENT_ORDER), "1Y", 50000

    @app.callback(
        Output("filter-caption", "children"),
        Output("insight-panel", "children"),
        Output("kpi-row", "children"),
        Output("segment-money-chart", "figure"),
        Output("horizon-compare-chart", "figure"),
        Output("turnover-chart", "figure"),
        Output("stock-movers-chart", "figure"),
        Output("scenario-cards", "children"),
        Output("error-panel", "children"),
        Input("refresh", "n_intervals"),
        Input("segment-filter", "value"),
        Input("horizon-filter", "value"),
        Input("invest-amount", "value"),
    )
    def refresh_dashboard(_n_intervals, segment_value, horizon_value, amount_value):
        selected = [s for s in (segment_value or []) if s in SEGMENT_ORDER]
        if not selected or len(selected) == len(SEGMENT_ORDER):
            segment_all, segment_list = 1, list(SEGMENT_ORDER)
        else:
            segment_all, segment_list = 0, selected
        horizon = horizon_value if horizon_value in HORIZON_FIELD else "1Y"
        horizon_field = HORIZON_FIELD[horizon]
        horizon_label = HORIZON_LABEL[horizon]
        amount = amount_value if isinstance(amount_value, (int, float)) and amount_value and amount_value > 0 else 50000

        params = {"segment_all": segment_all, "segment": segment_list}

        summary_rows = load_rows(server, metadata, __file__, "queries/business/summary.sql", params=params)
        constituent_rows = load_rows(server, metadata, __file__, "queries/business/constituents.sql", params=params)

        errors = []
        for label, payload in (("summary", summary_rows), ("constituents", constituent_rows)):
            if has_error(payload):
                errors.append(f"{label}: {payload[0]['_error']}")

        if has_error(summary_rows):
            caption = "Couldn't load the segments for the current filters."
        else:
            caption = f"Comparing {len(summary_rows)} of {len(SEGMENT_ORDER)} Nifty segments · {horizon_label}"

        headline, support = _build_insight(summary_rows, horizon_field, horizon_label, amount)
        insight_children = [
            html.Div("KEY INSIGHT", style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.08em", "color": "#93a1e8", "marginBottom": "0.4rem"}),
            html.Div(headline, style={"fontSize": "17px", "fontWeight": 700, "color": "#ffffff", "lineHeight": 1.35}),
            html.Div(support, style={"fontSize": "13px", "color": "#c3c9e8", "marginTop": "0.4rem", "lineHeight": 1.5}),
        ]

        kpi_cards = _kpi_cards(summary_rows, horizon_field, amount)
        money_figure = _segment_money_figure(summary_rows, amount=amount, horizon_field=horizon_field)
        horizon_figure = _horizon_compare_figure(summary_rows)
        turnover_figure = _turnover_figure(summary_rows)
        movers_figure = _stock_movers_figure(constituent_rows, amount=amount, horizon_field=horizon_field)

        scenarios = _build_scenarios(summary_rows, horizon_field, amount)
        scenario_cards = [_scenario_card(s) for s in scenarios] if scenarios else [
            html.Div("No scenarios available for the current filters.", style={"color": INK_MUTED})
        ]

        error_panel = render_error_panel("\n".join(errors)) if errors else None
        return (
            caption, insight_children, kpi_cards, money_figure, horizon_figure, turnover_figure,
            movers_figure, scenario_cards, error_panel,
        )

    return app
