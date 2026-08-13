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

# --- Design tokens ---
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

REGION_ORDER = ["AFRICA", "AMERICA", "ASIA", "EUROPE", "MIDDLE EAST"]
REGION_COLORS = {"AFRICA": BLUE, "AMERICA": ORANGE, "ASIA": AQUA, "EUROPE": YELLOW, "MIDDLE EAST": MAGENTA}

SEGMENT_ORDER = ["AUTOMOBILE", "BUILDING", "FURNITURE", "HOUSEHOLD", "MACHINERY"]
SEGMENT_LABELS = {s: s.capitalize() for s in SEGMENT_ORDER}
SEGMENT_COLORS = {"AUTOMOBILE": BLUE, "BUILDING": ORANGE, "FURNITURE": AQUA, "HOUSEHOLD": YELLOW, "MACHINERY": MAGENTA}

STATUS_OPTIONS = [{"label": "Open", "value": "O"}, {"label": "Completed", "value": "F"}, {"label": "In Progress", "value": "P"}]
STATUS_ORDER = ["O", "F", "P"]
STATUS_LABELS = {"O": "Open", "F": "Completed", "P": "In Progress"}
STATUS_COLORS = {"O": BLUE, "F": GOOD, "P": ORANGE}

SHIP_MODE_LABELS = {"REG AIR": "Regular Air", "FOB": "Freight (FOB)"}

SHORT_DISCLAIMER = "Sample order data — for demonstration."

CARD_STYLE = {
    "backgroundColor": SURFACE,
    "border": f"1px solid {HAIRLINE}",
    "borderRadius": "18px",
    "boxShadow": "0 2px 10px rgba(16,24,40,0.05)",
    "padding": "1.3rem 1.5rem",
}


def _format_usd(amount, decimals=0):
    amount = amount or 0
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.{decimals}f}"


def _friendly_label(value):
    return SHIP_MODE_LABELS.get(value, STATUS_LABELS.get(value, SEGMENT_LABELS.get(value, value)))


def _stat_tile(label, value, accent, value_color=None, caption=None):
    children = [
        html.Div(style={"height": "3px", "backgroundColor": accent, "borderRadius": "3px 3px 0 0", "margin": "-1.1rem -1.3rem 1rem"}),
        html.Div(label, style={"fontSize": "11.5px", "fontWeight": 600, "letterSpacing": "0.04em", "textTransform": "uppercase", "color": INK_MUTED, "marginBottom": "0.5rem"}),
        html.Div(value, style={"fontSize": "22px", "fontWeight": 700, "color": value_color or INK_PRIMARY, "fontVariantNumeric": "tabular-nums", "lineHeight": 1.15}),
    ]
    if caption:
        children.append(html.Div(caption, style={"fontSize": "11.5px", "color": INK_MUTED, "marginTop": "0.3rem"}))
    return html.Div(children, style={**CARD_STYLE, "padding": "1.1rem 1.3rem"})


def _kpi_cards(summary_row, region_rows):
    labels = ("Orders", "Total Sales", "Average Order", "Units Sold", "Average Discount", "Top Market")
    accents = (VIOLET, BLUE, BLUE, VIOLET, ORANGE, GOOD)
    if not summary_row or has_error(summary_row):
        return [_stat_tile(label, "—", accent) for label, accent in zip(labels, accents)]

    order_count = int(summary_row.get("ORDER_COUNT") or 0)
    total_orders_all = int(summary_row.get("TOTAL_ORDERS_ALL") or 0)
    order_caption = None if order_count == total_orders_all else f"of {total_orders_all:,} total"

    top_region = None
    top_share_caption = None
    if region_rows and not has_error(region_rows):
        total_region_revenue = sum(row.get("VALUE") or 0 for row in region_rows)
        best = max(region_rows, key=lambda r: r.get("VALUE") or -1e18)
        top_region = best.get("LABEL")
        if total_region_revenue:
            share = 100 * (best.get("VALUE") or 0) / total_region_revenue
            top_share_caption = f"{share:.0f}% of sales"

    values = (
        f"{order_count:,}",
        _format_usd(summary_row.get("TOTAL_REVENUE")),
        _format_usd(summary_row.get("AVG_ORDER_VALUE"), decimals=2),
        f"{(summary_row.get('UNITS_SOLD') or 0):,.0f}",
        f"{(summary_row.get('AVG_DISCOUNT_PCT') or 0):.1f}%",
        top_region or "—",
    )
    captions = (order_caption, None, None, None, None, top_share_caption)
    return [_stat_tile(label, value, accent, caption=caption) for label, value, accent, caption in zip(labels, values, accents, captions)]


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


def _horizontal_revenue_figure(rows, *, source_file, x_title, color_map=None, single_color=None, decimals=0):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No sales match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("VALUE") or 0, reverse=True)
    raw_labels = [row.get("LABEL") for row in ordered]
    labels = [_friendly_label(label) for label in raw_labels]
    values = [row.get("VALUE") or 0 for row in ordered]
    if color_map:
        colors = [color_map.get(label, VIOLET) for label in raw_labels]
    else:
        colors = single_color or BLUE
    text_labels = [_format_usd(v, decimals) for v in values]

    figure = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker={"color": colors, "cornerradius": 8, "line": {"width": 0}},
        text=text_labels, textposition="outside",
        textfont={"size": 12.5, "color": INK_SECONDARY, "family": FONT_FAMILY}, cliponaxis=False,
        hovertemplate=f"<b>%{{y}}</b><br>{x_title}: %{{text}}<extra></extra>",
    ))
    _base_layout(figure, x_title=x_title, y_title="")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    high = max(values) if values else 0
    low = min(0, min(values) if values else 0)
    span = (high - low) or 1
    figure.update_xaxes(range=[low, high + span * 0.28])
    return figure


def _year_trend_figure(rows, *, source_file):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No sales match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("LABEL") or 0)
    labels = [str(int(row.get("LABEL"))) for row in ordered]
    values = [row.get("VALUE") or 0 for row in ordered]
    text_labels = [_format_usd(v) for v in values]

    figure = go.Figure(go.Bar(
        x=labels, y=values,
        marker={"color": BLUE, "cornerradius": 8, "line": {"width": 0}},
        text=text_labels, textposition="outside",
        textfont={"size": 12, "color": INK_SECONDARY, "family": FONT_FAMILY}, cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Sales: %{text}<extra></extra>",
    ))
    _base_layout(figure, x_title="Order Year", y_title="Sales ($)", height=360)
    figure.update_xaxes(categoryorder="array", categoryarray=labels)
    high = max(values) if values else 0
    figure.update_yaxes(range=[0, high * 1.22 if high else 1])
    return figure


def _build_insight(region_rows, segment_rows):
    if not region_rows or has_error(region_rows):
        return "Not enough data", "Select at least one region to see an insight."
    total = sum(row.get("VALUE") or 0 for row in region_rows)
    top_region_row = max(region_rows, key=lambda r: r.get("VALUE") or -1e18)
    top_region = top_region_row.get("LABEL")
    top_region_revenue = top_region_row.get("VALUE") or 0
    share = 100 * top_region_revenue / total if total else 0
    headline = f"{top_region} is your top market — {_format_usd(top_region_revenue)} in sales ({share:.0f}% of total)"

    support = "Add more filters to compare specific markets and customer types."
    if segment_rows and not has_error(segment_rows):
        top_segment_row = max(segment_rows, key=lambda r: r.get("VALUE") or -1e18)
        support = f"{_friendly_label(top_segment_row.get('LABEL'))} is your top customer type, at {_format_usd(top_segment_row.get('VALUE') or 0)} in sales."
    return headline, support


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
        title=metadata.get("title", "Sales Insights"),
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
            html.Div(
                [
                    html.Div(
                        [
                            html.H1(metadata.get("title", "Sales Insights"), style={"margin": 0, "fontSize": "30px", "fontWeight": 800, "color": INK_PRIMARY, "letterSpacing": "-0.02em"}),
                            html.P("Revenue, orders, and top markets — in plain dollars, not codes.", style={"margin": "0.4rem 0 0", "fontSize": "14.5px", "color": INK_SECONDARY, "maxWidth": "640px"}),
                        ]
                    ),
                    html.Div(SHORT_DISCLAIMER, style={"fontSize": "12px", "color": INK_MUTED, "fontWeight": 600, "whiteSpace": "nowrap", "alignSelf": "center"}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-end", "flexWrap": "wrap", "gap": "1rem", "background": HERO_BG, "border": f"1px solid {HAIRLINE}", "borderRadius": "20px", "padding": "1.6rem 1.8rem", "marginBottom": "1.5rem"},
            ),
            html.Div(
                [
                    _filter_group("REGION", [dcc.Checklist(
                        id="region-filter", options=[{"label": r.title(), "value": r} for r in REGION_ORDER], value=list(REGION_ORDER),
                        inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                        labelStyle={"marginRight": "14px", "fontSize": "13px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                        style={"display": "flex", "flexWrap": "wrap", "rowGap": "0.3rem"},
                    )], flex="1.6 1 320px", divider=False),
                    _filter_group("CUSTOMER TYPE", [dcc.Checklist(
                        id="segment-filter", options=[{"label": SEGMENT_LABELS[s], "value": s} for s in SEGMENT_ORDER], value=list(SEGMENT_ORDER),
                        inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                        labelStyle={"marginRight": "14px", "fontSize": "13px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                        style={"display": "flex", "flexWrap": "wrap", "rowGap": "0.3rem"},
                    )], flex="1.6 1 320px"),
                    _filter_group("ORDER STATUS", [dcc.Checklist(
                        id="status-filter", options=STATUS_OPTIONS, value=list(STATUS_ORDER),
                        inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                        labelStyle={"marginRight": "14px", "fontSize": "13px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                        style={"display": "flex", "flexWrap": "wrap", "rowGap": "0.3rem"},
                    )], flex="1 1 220px"),
                    _filter_group("ORDER YEARS", [dcc.RangeSlider(
                        id="year-filter", min=1992, max=1998, step=1, value=[1992, 1998],
                        marks={y: str(y) for y in range(1992, 1999)},
                        tooltip={"placement": "bottom", "always_visible": False},
                    )], flex="1.6 1 300px"),
                    html.Div(html.Button("Reset", id="reset-filters", n_clicks=0, style={"border": "none", "backgroundColor": "transparent", "color": BLUE, "fontSize": "13px", "fontWeight": 700, "cursor": "pointer", "padding": 0}), style={"flex": "0 0 auto", "alignSelf": "center", "paddingLeft": "0.5rem"}),
                ],
                style={**CARD_STYLE, "display": "flex", "flexWrap": "wrap", "alignItems": "flex-start", "padding": "1.2rem 1rem", "marginBottom": "0.6rem"},
            ),
            html.Div(id="filter-caption", style={"fontSize": "12.5px", "color": INK_MUTED, "margin": "0 0.4rem 1rem"}),
            html.Div(id="insight-panel", style={"backgroundColor": INSIGHT_BG, "borderRadius": "18px", "padding": "1.2rem 1.5rem", "marginBottom": "1.5rem"}),
            html.Div(id="kpi-row", style={"display": "grid", "gridTemplateColumns": "repeat(6, minmax(0, 1fr))", "gap": "0.85rem", "marginBottom": "1.5rem"}),
            html.Div([_chart_card("year-trend-chart", "Sales over time", "Total sales by order year", flex="1 1 100%")], style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"}),
            html.Div(
                [
                    _chart_card("region-chart", "Sales by region", "Which part of the world buys the most"),
                    _chart_card("country-chart", "Top 10 countries", "Your biggest individual markets"),
                ],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"},
            ),
            html.Div(
                [
                    _chart_card("segment-chart", "Sales by customer type", "Which kind of customer buys the most"),
                    _chart_card("status-chart", "Sales by order status", "How much of your business is completed vs. in progress"),
                ],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"},
            ),
            html.Div([_chart_card("shipping-chart", "Sales by shipping method", "How goods are delivered to customers", flex="1 1 100%")], style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"}),
            html.Div(id="error-panel"),
        ],
        style={"fontFamily": FONT_FAMILY, "margin": "0 auto", "maxWidth": "1360px", "padding": "2rem 2rem 3rem", "backgroundColor": PAGE_PLANE, "minHeight": "100vh"},
    )

    @app.callback(
        Output("year-filter", "min"),
        Output("year-filter", "max"),
        Output("year-filter", "value"),
        Output("year-filter", "marks"),
        Input("init-load", "n_intervals"),
    )
    def populate_year_bounds(_n_intervals):
        row = load_row(server, metadata, __file__, "queries/business/filter_bounds.sql")
        if not row or has_error(row):
            return 1992, 1998, [1992, 1998], {y: str(y) for y in range(1992, 1999)}
        min_year = int(row.get("MIN_YEAR") or 1992)
        max_year = int(row.get("MAX_YEAR") or 1998)
        return min_year, max_year, [min_year, max_year], {y: str(y) for y in range(min_year, max_year + 1)}

    @app.callback(
        Output("region-filter", "value", allow_duplicate=True),
        Output("segment-filter", "value", allow_duplicate=True),
        Output("status-filter", "value", allow_duplicate=True),
        Output("year-filter", "value", allow_duplicate=True),
        Input("reset-filters", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_filters(_n_clicks):
        return list(REGION_ORDER), list(SEGMENT_ORDER), list(STATUS_ORDER), [1992, 1998]

    @app.callback(
        Output("filter-caption", "children"),
        Output("insight-panel", "children"),
        Output("kpi-row", "children"),
        Output("year-trend-chart", "figure"),
        Output("region-chart", "figure"),
        Output("country-chart", "figure"),
        Output("segment-chart", "figure"),
        Output("status-chart", "figure"),
        Output("shipping-chart", "figure"),
        Output("error-panel", "children"),
        Input("refresh", "n_intervals"),
        Input("region-filter", "value"),
        Input("segment-filter", "value"),
        Input("status-filter", "value"),
        Input("year-filter", "value"),
    )
    def refresh_dashboard(_n_intervals, region_value, segment_value, status_value, year_value):
        def _flag_and_list(selected, universe):
            selected = [v for v in (selected or []) if v in universe]
            if not selected or len(selected) == len(universe):
                return 1, list(universe)
            return 0, selected

        region_all, region_list = _flag_and_list(region_value, REGION_ORDER)
        segment_all, segment_list = _flag_and_list(segment_value, SEGMENT_ORDER)
        status_all, status_list = _flag_and_list(status_value, STATUS_ORDER)
        year_min, year_max = (year_value or [1992, 1998])[:2]

        params = {
            "region_all": region_all, "region": region_list,
            "segment_all": segment_all, "segment": segment_list,
            "status_all": status_all, "status": status_list,
            "year_min": int(year_min), "year_max": int(year_max),
        }

        summary_row = load_row(server, metadata, __file__, "queries/business/summary.sql", params=params)
        year_rows = load_rows(server, metadata, __file__, "queries/business/year_trend.sql", params=params)
        breakdown_rows = load_rows(server, metadata, __file__, "queries/business/breakdowns.sql", params=params)
        country_rows = load_rows(server, metadata, __file__, "queries/business/country_revenue.sql", params=params)

        errors = []
        for label, payload in (("summary", summary_row), ("year_trend", year_rows), ("breakdowns", breakdown_rows), ("country_revenue", country_rows)):
            if has_error(payload):
                error_row = payload[0] if isinstance(payload, list) else payload
                errors.append(f"{label}: {error_row['_error']}")

        breakdown_ok = bool(breakdown_rows) and not has_error(breakdown_rows)
        region_rows = [r for r in breakdown_rows if breakdown_ok and r.get("DIMENSION") == "Region"]
        segment_rows = [r for r in breakdown_rows if breakdown_ok and r.get("DIMENSION") == "Segment"]
        status_rows = [r for r in breakdown_rows if breakdown_ok and r.get("DIMENSION") == "Status"]
        shipping_rows = [r for r in breakdown_rows if breakdown_ok and r.get("DIMENSION") == "Shipping"]

        if has_error(summary_row):
            caption = "Couldn't load sales for the current filters."
        else:
            order_count = int((summary_row or {}).get("ORDER_COUNT") or 0)
            total_orders_all = int((summary_row or {}).get("TOTAL_ORDERS_ALL") or 0)
            caption = f"Showing {order_count:,} of {total_orders_all:,} orders · {int(year_min)}–{int(year_max)}"

        headline, support = _build_insight(region_rows, segment_rows)
        insight_children = [
            html.Div("KEY INSIGHT", style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.08em", "color": "#93a1e8", "marginBottom": "0.4rem"}),
            html.Div(headline, style={"fontSize": "17px", "fontWeight": 700, "color": "#ffffff", "lineHeight": 1.35}),
            html.Div(support, style={"fontSize": "13px", "color": "#c3c9e8", "marginTop": "0.4rem", "lineHeight": 1.5}),
        ]

        kpi_cards = _kpi_cards(summary_row, region_rows)
        year_figure = _year_trend_figure(year_rows, source_file="year_trend.sql")
        region_figure = _horizontal_revenue_figure(region_rows, source_file="breakdowns.sql", x_title="Sales ($)", color_map=REGION_COLORS)
        country_figure = _horizontal_revenue_figure(country_rows, source_file="country_revenue.sql", x_title="Sales ($)", single_color=VIOLET)
        segment_figure = _horizontal_revenue_figure(segment_rows, source_file="breakdowns.sql", x_title="Sales ($)", color_map=SEGMENT_COLORS)
        status_figure = _horizontal_revenue_figure(status_rows, source_file="breakdowns.sql", x_title="Sales ($)", color_map=STATUS_COLORS)
        shipping_figure = _horizontal_revenue_figure(shipping_rows, source_file="breakdowns.sql", x_title="Sales ($)", single_color=AQUA)

        error_panel = render_error_panel("\n".join(errors)) if errors else None
        return (
            caption, insight_children, kpi_cards, year_figure, region_figure, country_figure,
            segment_figure, status_figure, shipping_figure, error_panel,
        )

    return app
