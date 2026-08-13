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

CONTRACT_PALETTE = [BLUE, ORANGE, AQUA]
PREDICTED_ACTUAL_COLORS = {"Predicted": VIOLET, "Actual": ORANGE}

FOOTNOTE = "Reflects the current snapshot of STARTER_KIT.CHURN_SCORES, scored by the STARTER_KIT.predict_churn UDF — figures update as the table changes."

ALL_VALUE = "__ALL__"

CARD_STYLE = {
    "backgroundColor": SURFACE,
    "border": f"1px solid {HAIRLINE}",
    "borderRadius": "18px",
    "boxShadow": "0 2px 10px rgba(16,24,40,0.05)",
    "padding": "1.3rem 1.5rem",
}


def _contract_colors(contracts):
    return {contract: CONTRACT_PALETTE[i % len(CONTRACT_PALETTE)] for i, contract in enumerate(contracts)}


def _risk_band_color(sort_order):
    # 10 bands, 0 (0-10%) = safest -> green, 9 (90-100%) = riskiest -> red.
    t = max(0.0, min(1.0, (sort_order or 0) / 9.0))
    r = int(15 + t * (224 - 15))
    g = int(157 - t * (157 - 48))
    b = int(88 - t * (88 - 74))
    return f"rgb({r},{g},{b})"


def _stat_tile(label, value, accent, value_color=None, caption=None):
    children = [
        html.Div(style={"height": "3px", "backgroundColor": accent, "borderRadius": "3px 3px 0 0", "margin": "-1.1rem -1.3rem 1rem"}),
        html.Div(label, style={"fontSize": "11.5px", "fontWeight": 600, "letterSpacing": "0.04em", "textTransform": "uppercase", "color": INK_MUTED, "marginBottom": "0.5rem"}),
        html.Div(value, style={"fontSize": "22px", "fontWeight": 700, "color": value_color or INK_PRIMARY, "fontVariantNumeric": "tabular-nums", "lineHeight": 1.15}),
    ]
    if caption:
        children.append(html.Div(caption, style={"fontSize": "11.5px", "color": INK_MUTED, "marginTop": "0.3rem"}))
    return html.Div(children, style={**CARD_STYLE, "padding": "1.1rem 1.3rem"})


def _kpi_cards(summary_row, risk_by_contract_rows):
    labels = ("Customers Shown", "High Risk (≥50%)", "Contract Types", "Avg Predicted Risk", "Actual Churn Rate", "Riskiest Contract")
    accents = (VIOLET, CRITICAL, BLUE, YELLOW, ORANGE, CRITICAL)
    if not summary_row or has_error(summary_row):
        return [_stat_tile(label, "—", accent) for label, accent in zip(labels, accents)]

    cust_count = int(summary_row.get("CUST_COUNT") or 0)
    total_custs = int(summary_row.get("TOTAL_CUSTS") or 0)
    count_caption = None if cust_count == total_custs else f"of {total_custs:,} total"

    high_risk_count = int(summary_row.get("HIGH_RISK_COUNT") or 0)
    high_risk_caption = f"{(high_risk_count / cust_count * 100):.0f}% of shown" if cust_count else None

    riskiest_contract_value = "—"
    if risk_by_contract_rows and not has_error(risk_by_contract_rows):
        best = max(risk_by_contract_rows, key=lambda r: r.get("VALUE") or -1e9)
        riskiest_contract_value = f"{best.get('LABEL')} ({(best.get('VALUE') or 0):.0f}%)"

    values = (
        f"{cust_count:,}",
        f"{high_risk_count:,}",
        f"{int(summary_row.get('CONTRACT_COUNT') or 0):,}",
        f"{(summary_row.get('AVG_PREDICTED_RISK_PCT') or 0):.1f}%",
        f"{(summary_row.get('ACTUAL_CHURN_RATE_PCT') or 0):.1f}%",
        riskiest_contract_value,
    )
    value_colors = (None, CRITICAL, None, None, None, None)
    captions = (count_caption, high_risk_caption, None, None, None, None)
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


def _contract_bar_figure(rows, contract_colors, *, source_file, x_title, value_prefix="", value_suffix="", decimals=0):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No customers match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("VALUE") or 0, reverse=True)
    labels = [row.get("LABEL") for row in ordered]
    values = [row.get("VALUE") or 0 for row in ordered]
    colors = [contract_colors.get(label, INK_MUTED) for label in labels]
    text_labels = [f"{value_prefix}{v:,.{decimals}f}{value_suffix}" for v in values]

    figure = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker={"color": colors, "cornerradius": 8, "line": {"width": 0}},
        text=text_labels, textposition="outside",
        textfont={"size": 12.5, "color": INK_SECONDARY, "family": FONT_FAMILY}, cliponaxis=False,
        hovertemplate=f"<b>%{{y}}</b><br>{x_title}: {value_prefix}%{{x:,.{decimals}f}}{value_suffix}<extra></extra>",
    ))
    _base_layout(figure, x_title=x_title, y_title="")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    high = max(values) if values else 0
    figure.update_xaxes(range=[0, high * 1.28 if high else 1])
    return figure


def _risk_band_figure(rows, *, source_file):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No customers match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("SORT_ORDER") if row.get("SORT_ORDER") is not None else 0)
    labels = [row.get("LABEL") for row in ordered]
    values = [row.get("VALUE") or 0 for row in ordered]
    colors = [_risk_band_color(row.get("SORT_ORDER")) for row in ordered]
    text_labels = [f"{int(v)}" for v in values]

    figure = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker={"color": colors, "cornerradius": 8, "line": {"width": 0}},
        text=text_labels, textposition="outside",
        textfont={"size": 12.5, "color": INK_SECONDARY, "family": FONT_FAMILY}, cliponaxis=False,
        hovertemplate="<b>%{y} risk</b><br>Customers: %{x:,.0f}<extra></extra>",
    ))
    _base_layout(figure, x_title="Customers", y_title="")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    high = max(values) if values else 0
    figure.update_xaxes(range=[0, high * 1.28 if high else 1])
    return figure


def _predicted_vs_actual_figure(rows, *, source_file):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No customers match the selected filters.")
    labels = sorted({row.get("LABEL") for row in rows})

    figure = go.Figure()
    for category in ("Predicted", "Actual"):
        ys = []
        for label in labels:
            match = next((r for r in rows if r.get("LABEL") == label and r.get("CATEGORY") == category), None)
            ys.append(match.get("VALUE") if match else None)
        figure.add_trace(go.Bar(
            x=labels, y=ys, name=category,
            marker={"color": PREDICTED_ACTUAL_COLORS.get(category, INK_MUTED), "cornerradius": 8, "line": {"width": 0}},
            text=[f"{v:.1f}%" if v is not None else "" for v in ys], textposition="outside",
            textfont={"size": 12, "color": INK_SECONDARY}, cliponaxis=False,
            hovertemplate=f"<b>%{{x}}</b> ({category})<br>Rate: %{{y:.1f}}%<extra></extra>",
        ))
    _base_layout(figure, x_title="", y_title="Rate (%)", show_legend=True, height=340)
    figure.update_layout(barmode="group", margin={"t": 30, "r": 30, "b": 46, "l": 60})
    return figure


def _build_insight(risk_by_contract_rows, summary_row):
    if not risk_by_contract_rows or has_error(risk_by_contract_rows):
        return "Not enough data", "Select at least one contract type to see an insight."
    best = max(risk_by_contract_rows, key=lambda r: r.get("VALUE") or -1e9)
    headline = f"{best.get('LABEL')} contracts carry the highest churn risk — {(best.get('VALUE') or 0):.0f}% predicted probability on average"

    support = "A mix of contract lengths spreads churn exposure across the base."
    if summary_row and not has_error(summary_row):
        avg_predicted = summary_row.get("AVG_PREDICTED_RISK_PCT") or 0
        actual_rate = summary_row.get("ACTUAL_CHURN_RATE_PCT") or 0
        support = (
            f"Predicted risk across shown customers averages {avg_predicted:.1f}%, closely tracking the "
            f"actual churn rate of {actual_rate:.1f}% — a sign the model is well calibrated."
        )
    return headline, support


def _risk_badge(risk_pct):
    if risk_pct >= 70:
        color = CRITICAL
    elif risk_pct >= 40:
        color = YELLOW
    else:
        color = GOOD
    return html.Span(
        f"{risk_pct:.0f}%",
        style={
            "backgroundColor": color, "color": "#ffffff", "borderRadius": "999px",
            "padding": "0.15rem 0.6rem", "fontSize": "12px", "fontWeight": 700, "fontVariantNumeric": "tabular-nums",
        },
    )


def _top_risk_table(rows):
    if has_error(rows):
        return render_error_panel(rows[0]["_error"])
    if not rows:
        return html.Div("No customers match the current filters.", style={"color": INK_MUTED})

    header = html.Tr([
        html.Th(col, style={"textAlign": "left", "padding": "0.5rem 0.75rem", "fontSize": "11px", "color": INK_MUTED, "textTransform": "uppercase", "letterSpacing": "0.03em", "borderBottom": f"1px solid {HAIRLINE}"})
        for col in ("Customer", "Tenure (mo)", "Monthly Charges", "Contract", "Actual Churn", "Predicted Risk")
    ])
    body_rows = []
    for row in rows:
        risk_pct = row.get("CHURN_RISK_PCT") or 0
        body_rows.append(html.Tr([
            html.Td(row.get("CUSTOMER_ID"), style={"padding": "0.5rem 0.75rem", "fontSize": "13px", "color": INK_PRIMARY}),
            html.Td(f"{int(row.get('TENURE_MONTHS') or 0)}", style={"padding": "0.5rem 0.75rem", "fontSize": "13px", "color": INK_SECONDARY}),
            html.Td(f"${(row.get('MONTHLY_CHARGES') or 0):,.2f}", style={"padding": "0.5rem 0.75rem", "fontSize": "13px", "color": INK_SECONDARY}),
            html.Td(row.get("CONTRACT"), style={"padding": "0.5rem 0.75rem", "fontSize": "13px", "color": INK_SECONDARY}),
            html.Td(row.get("ACTUAL_CHURN"), style={"padding": "0.5rem 0.75rem", "fontSize": "13px", "color": INK_SECONDARY}),
            html.Td(_risk_badge(risk_pct), style={"padding": "0.5rem 0.75rem"}),
        ], style={"borderBottom": f"1px solid {HAIRLINE}"}))
    return html.Table([html.Thead(header), html.Tbody(body_rows)], style={"width": "100%", "borderCollapse": "collapse"})


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
        title=metadata.get("title", "Churn Insights"),
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
                            html.H1(metadata.get("title", "Churn Insights"), style={"margin": 0, "fontSize": "30px", "fontWeight": 800, "color": INK_PRIMARY, "letterSpacing": "-0.02em"}),
                            html.P("Predicted churn risk from STARTER_KIT.predict_churn, scored across STARTER_KIT.CHURN_SCORES.", style={"margin": "0.4rem 0 0", "fontSize": "14.5px", "color": INK_SECONDARY, "maxWidth": "640px"}),
                        ]
                    ),
                    html.Div("Live model scoring, in-database.", style={"fontSize": "12px", "color": INK_MUTED, "fontWeight": 600, "whiteSpace": "nowrap", "alignSelf": "center"}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-end", "flexWrap": "wrap", "gap": "1rem", "background": HERO_BG, "border": f"1px solid {HAIRLINE}", "borderRadius": "20px", "padding": "1.6rem 1.8rem", "marginBottom": "1.5rem"},
            ),
            html.Div(
                [
                    _filter_group("CONTRACT", [dcc.Checklist(
                        id="contract-filter", options=[], value=[],
                        inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                        labelStyle={"marginRight": "14px", "fontSize": "13px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                        style={"display": "flex", "flexWrap": "wrap", "rowGap": "0.3rem"},
                    )], flex="2.2 1 420px", divider=False),
                    _filter_group("RISK", [dcc.Checklist(
                        id="high-risk-only-filter", options=[{"label": "High risk only (≥50%)", "value": "high_risk"}], value=[],
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
                    _chart_card("risk-by-contract-chart", "Predicted churn risk by contract", "Average predicted probability, by contract type"),
                    _chart_card("risk-band-chart", "Customers by risk band", "How many customers fall in each 10%-wide risk band"),
                ],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"},
            ),
            html.Div([_chart_card("predicted-vs-actual-chart", "Predicted vs. actual churn rate", "How closely the model's average predicted risk tracks real outcomes, by contract", flex="1 1 100%")], style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.5rem"}),
            html.Div(
                [
                    html.H3("Highest-risk customers", style={"margin": 0, "fontSize": "18px", "fontWeight": 700, "color": INK_PRIMARY}),
                    html.P("The 25 customers with the highest predicted churn probability in the current filter.", style={"margin": "0.2rem 0 1rem", "fontSize": "12.5px", "color": INK_MUTED}),
                    html.Div(id="top-risk-table"),
                ],
                style={**CARD_STYLE, "marginBottom": "1rem"},
            ),
            html.Div(FOOTNOTE, style={"fontSize": "11.5px", "color": INK_MUTED, "textAlign": "center", "margin": "0.5rem 1rem 0", "lineHeight": 1.5}),
            html.Div(id="error-panel"),
        ],
        style={"fontFamily": FONT_FAMILY, "margin": "0 auto", "maxWidth": "1360px", "padding": "2rem 2rem 3rem", "backgroundColor": PAGE_PLANE, "minHeight": "100vh"},
    )

    @app.callback(
        Output("contract-filter", "options"),
        Output("contract-filter", "value"),
        Output("filter-universe", "data"),
        Input("init-load", "n_intervals"),
    )
    def populate_filters(_n_intervals):
        rows = load_rows(server, metadata, __file__, "queries/business/filter_options.sql")
        contracts = [] if has_error(rows) else [row.get("VALUE") for row in rows]
        return [{"label": c, "value": c} for c in contracts], list(contracts), {"contracts": contracts}

    @app.callback(
        Output("contract-filter", "value", allow_duplicate=True),
        Output("high-risk-only-filter", "value", allow_duplicate=True),
        Input("reset-filters", "n_clicks"),
        State("filter-universe", "data"),
        prevent_initial_call=True,
    )
    def reset_filters(_n_clicks, filter_universe):
        contracts = (filter_universe or {}).get("contracts", [])
        return list(contracts), []

    @app.callback(
        Output("filter-caption", "children"),
        Output("insight-panel", "children"),
        Output("kpi-row", "children"),
        Output("risk-by-contract-chart", "figure"),
        Output("risk-band-chart", "figure"),
        Output("predicted-vs-actual-chart", "figure"),
        Output("top-risk-table", "children"),
        Output("error-panel", "children"),
        Input("refresh", "n_intervals"),
        Input("contract-filter", "value"),
        Input("high-risk-only-filter", "value"),
        State("filter-universe", "data"),
    )
    def refresh_dashboard(_n_intervals, contract_value, high_risk_only_value, filter_universe):
        universe = (filter_universe or {}).get("contracts", [])
        selected = [c for c in (contract_value or []) if c]
        if not selected or set(selected) >= set(universe):
            contract_all, contract_list = 1, (universe or ["__none__"])
        else:
            contract_all, contract_list = 0, selected
        high_risk_only = 1 if "high_risk" in (high_risk_only_value or []) else 0

        params = {"contract_all": contract_all, "contract": contract_list, "high_risk_only": high_risk_only}

        summary_row = load_row(server, metadata, __file__, "queries/business/summary.sql", params=params)
        risk_by_contract_rows = load_rows(server, metadata, __file__, "queries/business/risk_by_contract.sql", params=params)
        risk_band_rows = load_rows(server, metadata, __file__, "queries/business/count_by_risk_band.sql", params=params)
        predicted_vs_actual_rows = load_rows(server, metadata, __file__, "queries/business/predicted_vs_actual_by_contract.sql", params=params)
        top_risk_rows = load_rows(server, metadata, __file__, "queries/business/top_risk_customers.sql", params=params)

        errors = []
        for label, payload in (
            ("summary", summary_row), ("risk_by_contract", risk_by_contract_rows), ("count_by_risk_band", risk_band_rows),
            ("predicted_vs_actual_by_contract", predicted_vs_actual_rows), ("top_risk_customers", top_risk_rows),
        ):
            if has_error(payload):
                error_row = payload[0] if isinstance(payload, list) else payload
                errors.append(f"{label}: {error_row['_error']}")

        if has_error(summary_row):
            caption = "Unable to load summary for the current filters."
        else:
            cust_count = int((summary_row or {}).get("CUST_COUNT") or 0)
            total_custs = int((summary_row or {}).get("TOTAL_CUSTS") or 0)
            caption = f"Showing {cust_count:,} of {total_custs:,} customers"

        headline, support = _build_insight(risk_by_contract_rows, summary_row)
        insight_children = [
            html.Div("KEY INSIGHT", style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.08em", "color": "#93a1e8", "marginBottom": "0.4rem"}),
            html.Div(headline, style={"fontSize": "17px", "fontWeight": 700, "color": "#ffffff", "lineHeight": 1.35}),
            html.Div(support, style={"fontSize": "13px", "color": "#c3c9e8", "marginTop": "0.4rem", "lineHeight": 1.5}),
        ]

        contract_colors = _contract_colors(universe or [row.get("LABEL") for row in (risk_by_contract_rows if not has_error(risk_by_contract_rows) else [])])

        kpi_cards = _kpi_cards(summary_row, risk_by_contract_rows)
        risk_by_contract_figure = _contract_bar_figure(risk_by_contract_rows, contract_colors, source_file="risk_by_contract.sql", x_title="Predicted Risk", value_suffix="%")
        risk_band_figure = _risk_band_figure(risk_band_rows, source_file="count_by_risk_band.sql")
        predicted_vs_actual_figure = _predicted_vs_actual_figure(predicted_vs_actual_rows, source_file="predicted_vs_actual_by_contract.sql")
        top_risk_table = _top_risk_table(top_risk_rows)

        error_panel = render_error_panel("\n".join(errors)) if errors else None
        return (
            caption, insight_children, kpi_cards, risk_by_contract_figure, risk_band_figure,
            predicted_vs_actual_figure, top_risk_table, error_panel,
        )

    return app
