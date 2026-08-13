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

DEPARTMENT_PALETTE = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, VIOLET]
STATUS_COLORS = {"Active": GOOD, "Inactive": CRITICAL}

FOOTNOTE = "Reflects the current snapshot of STARTER_KIT.EMPLOYEES — figures update as the table changes."

ALL_VALUE = "__ALL__"

CARD_STYLE = {
    "backgroundColor": SURFACE,
    "border": f"1px solid {HAIRLINE}",
    "borderRadius": "18px",
    "boxShadow": "0 2px 10px rgba(16,24,40,0.05)",
    "padding": "1.3rem 1.5rem",
}


def _department_colors(departments):
    return {dept: DEPARTMENT_PALETTE[i % len(DEPARTMENT_PALETTE)] for i, dept in enumerate(departments)}


def _stat_tile(label, value, accent, value_color=None, caption=None):
    children = [
        html.Div(style={"height": "3px", "backgroundColor": accent, "borderRadius": "3px 3px 0 0", "margin": "-1.1rem -1.3rem 1rem"}),
        html.Div(label, style={"fontSize": "11.5px", "fontWeight": 600, "letterSpacing": "0.04em", "textTransform": "uppercase", "color": INK_MUTED, "marginBottom": "0.5rem"}),
        html.Div(value, style={"fontSize": "22px", "fontWeight": 700, "color": value_color or INK_PRIMARY, "fontVariantNumeric": "tabular-nums", "lineHeight": 1.15}),
    ]
    if caption:
        children.append(html.Div(caption, style={"fontSize": "11.5px", "color": INK_MUTED, "marginTop": "0.3rem"}))
    return html.Div(children, style={**CARD_STYLE, "padding": "1.1rem 1.3rem"})


def _kpi_cards(summary_row, headcount_rows):
    labels = ("Employees Shown", "Active", "Departments", "Avg Salary", "Avg Tenure", "Top Department")
    accents = (VIOLET, GOOD, BLUE, GOOD, VIOLET, GOOD)
    if not summary_row or has_error(summary_row):
        return [_stat_tile(label, "—", accent) for label, accent in zip(labels, accents)]

    emp_count = int(summary_row.get("EMP_COUNT") or 0)
    total_emps = int(summary_row.get("TOTAL_EMPS") or 0)
    count_caption = None if emp_count == total_emps else f"of {total_emps:,} total"

    active_count = int(summary_row.get("ACTIVE_COUNT") or 0)
    active_caption = f"{(active_count / emp_count * 100):.0f}% of shown" if emp_count else None

    top_department_value = "—"
    if headcount_rows and not has_error(headcount_rows):
        best = max(headcount_rows, key=lambda r: r.get("VALUE") or -1e9)
        top_department_value = f"{best.get('LABEL')} ({int(best.get('VALUE') or 0)})"

    values = (
        f"{emp_count:,}",
        f"{active_count:,}",
        f"{int(summary_row.get('DEPT_COUNT') or 0):,}",
        f"${(summary_row.get('AVG_SALARY') or 0):,.0f}",
        f"{(summary_row.get('AVG_TENURE_YEARS') or 0):.1f} yrs",
        top_department_value,
    )
    value_colors = (None, GOOD, None, None, None, None)
    captions = (count_caption, active_caption, None, None, None, None)
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


def _department_bar_figure(rows, dept_colors, *, source_file, x_title, value_prefix="", value_suffix="", decimals=0):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No employees match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("VALUE") or 0, reverse=True)
    labels = [row.get("LABEL") for row in ordered]
    values = [row.get("VALUE") or 0 for row in ordered]
    colors = [dept_colors.get(label, INK_MUTED) for label in labels]
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


def _hires_trend_figure(rows, *, source_file):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No employees match the selected filters.")
    ordered = sorted(rows, key=lambda row: row.get("LABEL") or "")
    years = [row.get("LABEL") for row in ordered]
    values = [row.get("VALUE") or 0 for row in ordered]

    figure = go.Figure(go.Bar(
        x=years, y=values,
        marker={"color": BLUE, "cornerradius": 8, "line": {"width": 0}},
        text=[f"{int(v)}" for v in values], textposition="outside",
        textfont={"size": 12.5, "color": INK_SECONDARY, "family": FONT_FAMILY}, cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Hires: %{y}<extra></extra>",
    ))
    _base_layout(figure, x_title="Hire Year", y_title="Employees Hired", height=340)
    figure.update_layout(margin={"t": 30, "r": 30, "b": 46, "l": 60})
    high = max(values) if values else 0
    figure.update_yaxes(range=[0, high * 1.28 if high else 1])
    return figure


def _status_by_department_figure(rows, dept_colors, *, source_file):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No employees match the selected filters.")
    totals = {}
    for row in rows:
        totals[row.get("LABEL")] = totals.get(row.get("LABEL"), 0) + (row.get("VALUE") or 0)
    labels = sorted(totals, key=lambda label: totals[label], reverse=True)

    figure = go.Figure()
    for status in ("Active", "Inactive"):
        xs = []
        for label in labels:
            match = next((r for r in rows if r.get("LABEL") == label and r.get("CATEGORY") == status), None)
            xs.append(match.get("VALUE") if match else None)
        figure.add_trace(go.Bar(
            x=xs, y=labels, orientation="h", name=status,
            marker={"color": STATUS_COLORS.get(status, INK_MUTED), "cornerradius": 8, "line": {"width": 0}},
            text=[f"{int(v)}" if v is not None else "" for v in xs], textposition="inside", insidetextanchor="middle",
            textfont={"size": 12, "color": "#ffffff"}, cliponaxis=False,
            hovertemplate=f"<b>%{{y}}</b> ({status})<br>Employees: %{{x}}<extra></extra>",
        ))
    _base_layout(figure, x_title="Employees", y_title="", show_legend=True, height=340)
    figure.update_layout(barmode="stack")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    return figure


def _build_insight(headcount_rows, status_rows):
    if not headcount_rows or has_error(headcount_rows):
        return "Not enough data", "Select at least one department to see an insight."
    best = max(headcount_rows, key=lambda r: r.get("VALUE") or -1e9)
    total = sum(r.get("VALUE") or 0 for r in headcount_rows)
    share = (best.get("VALUE") or 0) / total * 100 if total else 0
    headline = f"{best.get('LABEL')} leads headcount with {int(best.get('VALUE') or 0)} employees ({share:.0f}% of those shown)"

    support = "A balanced spread across departments reduces key-person risk on any single team."
    if status_rows and not has_error(status_rows):
        inactive_depts = sorted({r.get("LABEL") for r in status_rows if r.get("CATEGORY") == "Inactive"})
        if inactive_depts:
            support = f"Inactive employees are currently concentrated in {', '.join(inactive_depts)} — worth a look if that's unexpected attrition."
    return headline, support


def _department_card(row):
    department = row.get("DEPARTMENT")
    accent = row.get("_ACCENT", INK_MUTED)
    headcount = int(row.get("HEADCOUNT") or 0)
    active_count = int(row.get("ACTIVE_COUNT") or 0)
    avg_salary = row.get("AVG_SALARY") or 0
    avg_tenure = row.get("AVG_TENURE_YEARS") or 0
    earliest_hire = row.get("EARLIEST_HIRE") or "—"
    return html.Div(
        [
            html.Div(style={"height": "4px", "backgroundColor": accent, "borderRadius": "4px 4px 0 0", "margin": "-1.1rem -1.3rem 0.85rem"}),
            html.Div(department.upper(), style={"fontSize": "11px", "fontWeight": 700, "letterSpacing": "0.04em", "color": INK_MUTED}),
            html.Div(f"{headcount} employee{'s' if headcount != 1 else ''}", style={"fontSize": "19px", "fontWeight": 700, "color": INK_PRIMARY, "marginTop": "0.15rem", "marginBottom": "0.75rem"}),
            html.Div(
                [
                    html.Div(f"{active_count} active / {headcount - active_count} inactive", style={"fontSize": "12px", "color": INK_SECONDARY}),
                    html.Div(f"${avg_salary:,.0f} avg salary", style={"fontSize": "18px", "fontWeight": 700, "color": accent, "fontVariantNumeric": "tabular-nums"}),
                ],
                style={"marginBottom": "0.6rem"},
            ),
            html.Div(
                [
                    html.Span(f"Avg tenure: {avg_tenure:.1f} yrs", style={"marginRight": "0.9rem"}),
                    html.Span(f"Longest-tenured since: {earliest_hire}"),
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
        title=metadata.get("title", "Employee Insights"),
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
                            html.H1(metadata.get("title", "Employee Insights"), style={"margin": 0, "fontSize": "30px", "fontWeight": 800, "color": INK_PRIMARY, "letterSpacing": "-0.02em"}),
                            html.P("Headcount, compensation, and tenure across STARTER_KIT.EMPLOYEES.", style={"margin": "0.4rem 0 0", "fontSize": "14.5px", "color": INK_SECONDARY, "maxWidth": "640px"}),
                        ]
                    ),
                    html.Div("Internal workforce snapshot.", style={"fontSize": "12px", "color": INK_MUTED, "fontWeight": 600, "whiteSpace": "nowrap", "alignSelf": "center"}),
                ],
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-end", "flexWrap": "wrap", "gap": "1rem", "background": HERO_BG, "border": f"1px solid {HAIRLINE}", "borderRadius": "20px", "padding": "1.6rem 1.8rem", "marginBottom": "1.5rem"},
            ),
            html.Div(
                [
                    _filter_group("DEPARTMENT", [dcc.Checklist(
                        id="department-filter", options=[], value=[],
                        inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                        labelStyle={"marginRight": "14px", "fontSize": "13px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                        style={"display": "flex", "flexWrap": "wrap", "rowGap": "0.3rem"},
                    )], flex="2.2 1 420px", divider=False),
                    _filter_group("STATUS", [dcc.Checklist(
                        id="active-only-filter", options=[{"label": "Active employees only", "value": "active"}], value=[],
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
                    _chart_card("headcount-chart", "Headcount by department", "Where the current workforce is concentrated"),
                    _chart_card("salary-chart", "Average salary by department", "Which teams are paid the most, on average"),
                ],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"},
            ),
            html.Div([_chart_card("hires-trend-chart", "Hiring trend by year", "How headcount has grown over time", flex="1 1 100%")], style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.1rem"}),
            html.Div([_chart_card("status-chart", "Employee status by department", "Active vs. inactive headcount, by team")], style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem", "marginBottom": "1.5rem"}),
            html.Div(
                [
                    html.H3("Department snapshot", style={"margin": 0, "fontSize": "18px", "fontWeight": 700, "color": INK_PRIMARY}),
                    html.P("Headcount, pay, and tenure for each department in the current filter.", style={"margin": "0.2rem 0 1rem", "fontSize": "12.5px", "color": INK_MUTED}),
                    html.Div(id="department-cards", style={"display": "flex", "flexWrap": "wrap", "gap": "1rem"}),
                ],
                style={**CARD_STYLE, "marginBottom": "1rem"},
            ),
            html.Div(FOOTNOTE, style={"fontSize": "11.5px", "color": INK_MUTED, "textAlign": "center", "margin": "0.5rem 1rem 0", "lineHeight": 1.5}),
            html.Div(id="error-panel"),
        ],
        style={"fontFamily": FONT_FAMILY, "margin": "0 auto", "maxWidth": "1360px", "padding": "2rem 2rem 3rem", "backgroundColor": PAGE_PLANE, "minHeight": "100vh"},
    )

    @app.callback(
        Output("department-filter", "options"),
        Output("department-filter", "value"),
        Output("filter-universe", "data"),
        Input("init-load", "n_intervals"),
    )
    def populate_filters(_n_intervals):
        rows = load_rows(server, metadata, __file__, "queries/business/filter_options.sql")
        departments = [] if has_error(rows) else [row.get("VALUE") for row in rows]
        return [{"label": d, "value": d} for d in departments], list(departments), {"departments": departments}

    @app.callback(
        Output("department-filter", "value", allow_duplicate=True),
        Output("active-only-filter", "value", allow_duplicate=True),
        Input("reset-filters", "n_clicks"),
        State("filter-universe", "data"),
        prevent_initial_call=True,
    )
    def reset_filters(_n_clicks, filter_universe):
        departments = (filter_universe or {}).get("departments", [])
        return list(departments), []

    @app.callback(
        Output("filter-caption", "children"),
        Output("insight-panel", "children"),
        Output("kpi-row", "children"),
        Output("headcount-chart", "figure"),
        Output("salary-chart", "figure"),
        Output("hires-trend-chart", "figure"),
        Output("status-chart", "figure"),
        Output("department-cards", "children"),
        Output("error-panel", "children"),
        Input("refresh", "n_intervals"),
        Input("department-filter", "value"),
        Input("active-only-filter", "value"),
        State("filter-universe", "data"),
    )
    def refresh_dashboard(_n_intervals, department_value, active_only_value, filter_universe):
        universe = (filter_universe or {}).get("departments", [])
        selected = [d for d in (department_value or []) if d]
        if not selected or set(selected) >= set(universe):
            department_all, department_list = 1, (universe or ["__none__"])
        else:
            department_all, department_list = 0, selected
        active_only = 1 if "active" in (active_only_value or []) else 0

        params = {"department_all": department_all, "department": department_list, "active_only": active_only}

        summary_row = load_row(server, metadata, __file__, "queries/business/summary.sql", params=params)
        headcount_rows = load_rows(server, metadata, __file__, "queries/business/department_headcount.sql", params=params)
        salary_rows = load_rows(server, metadata, __file__, "queries/business/department_salary.sql", params=params)
        hires_rows = load_rows(server, metadata, __file__, "queries/business/hires_by_year.sql", params=params)
        status_rows = load_rows(server, metadata, __file__, "queries/business/status_by_department.sql", params=params)
        snapshot_rows = load_rows(server, metadata, __file__, "queries/business/department_snapshot.sql", params=params)

        errors = []
        for label, payload in (
            ("summary", summary_row), ("department_headcount", headcount_rows), ("department_salary", salary_rows),
            ("hires_by_year", hires_rows), ("status_by_department", status_rows), ("department_snapshot", snapshot_rows),
        ):
            if has_error(payload):
                error_row = payload[0] if isinstance(payload, list) else payload
                errors.append(f"{label}: {error_row['_error']}")

        if has_error(summary_row):
            caption = "Unable to load summary for the current filters."
        else:
            emp_count = int((summary_row or {}).get("EMP_COUNT") or 0)
            total_emps = int((summary_row or {}).get("TOTAL_EMPS") or 0)
            caption = f"Showing {emp_count:,} of {total_emps:,} employees"

        headline, support = _build_insight(headcount_rows, status_rows)
        insight_children = [
            html.Div("KEY INSIGHT", style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.08em", "color": "#93a1e8", "marginBottom": "0.4rem"}),
            html.Div(headline, style={"fontSize": "17px", "fontWeight": 700, "color": "#ffffff", "lineHeight": 1.35}),
            html.Div(support, style={"fontSize": "13px", "color": "#c3c9e8", "marginTop": "0.4rem", "lineHeight": 1.5}),
        ]

        dept_colors = _department_colors(universe or [row.get("LABEL") for row in (headcount_rows if not has_error(headcount_rows) else [])])

        kpi_cards = _kpi_cards(summary_row, headcount_rows)
        headcount_figure = _department_bar_figure(headcount_rows, dept_colors, source_file="department_headcount.sql", x_title="Headcount")
        salary_figure = _department_bar_figure(salary_rows, dept_colors, source_file="department_salary.sql", x_title="Average Salary", value_prefix="$")
        hires_figure = _hires_trend_figure(hires_rows, source_file="hires_by_year.sql")
        status_figure = _status_by_department_figure(status_rows, dept_colors, source_file="status_by_department.sql")

        department_cards = []
        if snapshot_rows and not has_error(snapshot_rows):
            for row in snapshot_rows:
                department_cards.append(_department_card({**row, "_ACCENT": dept_colors.get(row.get("DEPARTMENT"), INK_MUTED)}))
        if not department_cards:
            department_cards = [html.Div("No departments match the current filters.", style={"color": INK_MUTED})]

        error_panel = render_error_panel("\n".join(errors)) if errors else None
        return (
            caption, insight_children, kpi_cards, headcount_figure, salary_figure, hires_figure,
            status_figure, department_cards, error_panel,
        )

    return app
