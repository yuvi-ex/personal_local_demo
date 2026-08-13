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
WARNING = "#eda100"
SERIOUS = "#eb6834"
CRITICAL = "#e0304a"
HERO_BG = "linear-gradient(135deg, #eef1ff 0%, #f5f6fb 60%)"
INSIGHT_BG = "#101828"

GRADE_COLORS = {"A": GOOD, "B": AQUA, "C": WARNING, "D": SERIOUS, "F": CRITICAL}
KPI_ACCENTS = [VIOLET, BLUE, BLUE, GOOD, VIOLET, VIOLET]

GRADE_ORDER = ["A", "B", "C", "D", "F"]
ATTENDANCE_ORDER = ["<60%", "60-70%", "70-80%", "80-90%", "90-100%"]
STUDY_HOURS_ORDER = ["0-9 hrs/wk", "10-19 hrs/wk", "20-29 hrs/wk", "30+ hrs/wk"]
INCOME_ORDER = ["Low", "Medium", "High"]

FILTER_GROUPS = [
    ("department-filter", "Department", "Department"),
    ("gender-filter", "Gender", "Gender"),
    ("income-filter", "Family_Income_Level", "Family Income"),
    ("extracurricular-filter", "Extracurricular_Activities", "Extracurricular"),
]

CARD_STYLE = {
    "backgroundColor": SURFACE,
    "border": f"1px solid {HAIRLINE}",
    "borderRadius": "18px",
    "boxShadow": "0 2px 10px rgba(16,24,40,0.05)",
    "padding": "1.3rem 1.5rem",
}


def _stat_tile(label, value, accent, caption=None):
    children = [
        html.Div(style={"height": "3px", "backgroundColor": accent, "borderRadius": "3px 3px 0 0", "margin": "-1.1rem -1.3rem 1rem"}),
        html.Div(label, style={"fontSize": "11.5px", "fontWeight": 600, "letterSpacing": "0.04em", "textTransform": "uppercase", "color": INK_MUTED, "marginBottom": "0.5rem"}),
        html.Div(value, style={"fontSize": "22px", "fontWeight": 700, "color": INK_PRIMARY, "fontVariantNumeric": "tabular-nums", "lineHeight": 1.15}),
    ]
    if caption:
        children.append(html.Div(caption, style={"fontSize": "11.5px", "color": INK_MUTED, "marginTop": "0.3rem"}))
    return html.Div(children, style={**CARD_STYLE, "padding": "1.1rem 1.3rem"})


def _kpi_cards(summary_row):
    labels = ("Students Counted", "Average Overall Score", "Average Attendance", "Pass Rate", "Average Weekly Study Time", "Average Sleep / Night")
    if not summary_row or has_error(summary_row):
        return [_stat_tile(label, "—", accent) for label, accent in zip(labels, KPI_ACCENTS)]
    student_count = int(summary_row.get("STUDENT_COUNT") or 0)
    total_students = int(summary_row.get("TOTAL_STUDENTS") or 0)
    caption = None if student_count == total_students else f"of {total_students:,} total"
    values = (
        f"{student_count:,}",
        f"{(summary_row.get('AVG_TOTAL_SCORE') or 0):.1f}%",
        f"{(summary_row.get('AVG_ATTENDANCE') or 0):.1f}%",
        f"{(summary_row.get('PASS_RATE') or 0):.1f}%",
        f"{(summary_row.get('AVG_STUDY_HOURS') or 0):.1f} hrs",
        f"{(summary_row.get('AVG_SLEEP_HOURS') or 0):.1f} hrs",
    )
    captions = (caption, None, None, None, None, None)
    return [_stat_tile(label, value, accent, caption=cap) for label, value, accent, cap in zip(labels, values, KPI_ACCENTS, captions)]


def _empty_figure(message):
    figure = go.Figure()
    figure.add_annotation(text=message, showarrow=False, font={"family": FONT_FAMILY, "color": INK_MUTED, "size": 13})
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"t": 10, "r": 10, "b": 10, "l": 10},
    )
    return figure


def _base_layout(figure, *, x_title, y_title, height=340):
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        bargap=0.35,
        margin={"t": 30, "r": 24, "b": 46, "l": 60},
        font={"family": FONT_FAMILY, "color": INK_SECONDARY, "size": 12.5},
        showlegend=False,
        hoverlabel={"bgcolor": SURFACE, "bordercolor": HAIRLINE, "font": {"family": FONT_FAMILY, "color": INK_PRIMARY, "size": 12.5}},
        xaxis={
            "title": {"text": x_title, "font": {"size": 12.5, "color": INK_MUTED}},
            "showgrid": False,
            "showline": True,
            "linecolor": BASELINE,
            "tickfont": {"color": INK_SECONDARY, "size": 12},
            "ticks": "",
        },
        yaxis={
            "title": {"text": y_title, "font": {"size": 12.5, "color": INK_MUTED}},
            "showgrid": True,
            "gridcolor": HAIRLINE,
            "gridwidth": 1,
            "zeroline": False,
            "tickfont": {"color": INK_SECONDARY, "size": 12.5},
            "rangemode": "tozero",
        },
    )
    return figure


def _vertical_bar_figure(rows, *, source_file, x_title, y_title, colors, decimals=1, value_suffix="%", category_order=None, flat_hint=False):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No students match the selected filters.")

    labels = [row.get("LABEL") for row in rows]
    values = [row.get("VALUE") or 0 for row in rows]
    if isinstance(colors, dict):
        bar_colors = [colors.get(label, INK_MUTED) for label in labels]
    else:
        bar_colors = colors
    text_labels = [f"{v:.{decimals}f}{value_suffix}" for v in values]

    figure = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker={"color": bar_colors, "cornerradius": 8, "line": {"width": 0}},
            text=text_labels,
            textposition="outside",
            textfont={"size": 12.5, "color": INK_SECONDARY, "family": FONT_FAMILY},
            cliponaxis=False,
            hovertemplate=f"<b>%{{x}}</b><br>{y_title}: %{{text}}<extra></extra>",
        )
    )
    _base_layout(figure, x_title=x_title, y_title=y_title)
    if category_order:
        figure.update_xaxes(categoryorder="array", categoryarray=category_order)
    max_value = max(values) if values else 0
    if flat_hint and max_value:
        figure.update_yaxes(range=[0, max_value * 1.25])
        figure.update_layout(bargap=0.08)
    else:
        figure.update_yaxes(range=[0, max_value * 1.18 if max_value else 1])
    return figure


def _horizontal_bar_figure(rows, *, source_file, x_title, color, decimals=1, value_suffix="%"):
    if has_error(rows):
        return _empty_figure(f"Query failed — {source_file}")
    if not rows:
        return _empty_figure("No students match the selected filters.")

    ordered = sorted(rows, key=lambda row: row.get("VALUE") or 0, reverse=True)
    labels = [row.get("LABEL") for row in ordered]
    values = [row.get("VALUE") or 0 for row in ordered]
    text_labels = [f"{v:.{decimals}f}{value_suffix}" for v in values]

    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker={"color": color, "cornerradius": 8, "line": {"width": 0}},
            text=text_labels,
            textposition="outside",
            textfont={"size": 12.5, "color": INK_SECONDARY, "family": FONT_FAMILY},
            cliponaxis=False,
            hovertemplate=f"<b>%{{y}}</b><br>{x_title}: %{{text}}<extra></extra>",
        )
    )
    _base_layout(figure, x_title=x_title, y_title="")
    figure.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels, showgrid=False)
    max_value = max(values) if values else 0
    figure.update_xaxes(range=[0, max_value * 1.25 if max_value else 1])
    return figure


def _filter_flag_and_list(selected, universe):
    selected = [v for v in (selected or []) if v]
    universe = [v for v in (universe or []) if v]
    if not universe:
        return 1, ["__none__"]
    if not selected or set(selected) >= set(universe):
        return 1, universe
    return 0, selected


def _filter_params(department, gender, income, extracurricular, filter_universe):
    filter_universe = filter_universe or {}
    d_flag, d_val = _filter_flag_and_list(department, filter_universe.get("Department"))
    g_flag, g_val = _filter_flag_and_list(gender, filter_universe.get("Gender"))
    i_flag, i_val = _filter_flag_and_list(income, filter_universe.get("Family_Income_Level"))
    e_flag, e_val = _filter_flag_and_list(extracurricular, filter_universe.get("Extracurricular_Activities"))
    return {
        "department_all": d_flag, "department": d_val,
        "gender_all": g_flag, "gender": g_val,
        "income_all": i_flag, "income": i_val,
        "extracurricular_all": e_flag, "extracurricular": e_val,
    }


def _build_insight(grade_rows, study_hours_rows):
    if not grade_rows or has_error(grade_rows):
        return "Not enough data", "Select at least one filter combination to see an insight."
    total = sum(row.get("VALUE") or 0 for row in grade_rows)
    low = sum((row.get("VALUE") or 0) for row in grade_rows if row.get("LABEL") in ("D", "F"))
    high = sum((row.get("VALUE") or 0) for row in grade_rows if row.get("LABEL") in ("A", "B"))
    if not total:
        return "Not enough data", "Select at least one filter combination to see an insight."
    pct_low = 100 * low / total
    pct_high = 100 * high / total
    headline = f"{pct_low:.0f}% of students land in D or F territory — only {pct_high:.0f}% reach an A or B"

    support = "Add more filters to see how attendance and study time change the picture."
    if study_hours_rows and not has_error(study_hours_rows):
        values = [row.get("VALUE") or 0 for row in study_hours_rows]
        spread = max(values) - min(values) if values else 0
        if spread < 2:
            support = f"Weekly study time barely moves the needle — scores stay within {spread:.1f} points no matter how much students study."
        else:
            best = max(study_hours_rows, key=lambda row: row.get("VALUE") or 0)
            worst = min(study_hours_rows, key=lambda row: row.get("VALUE") or 0)
            support = f"Studying does help here — the {best.get('LABEL')} group scores {spread:.1f} points above the {worst.get('LABEL')} group."
    return headline, support


def _chart_card(graph_id, title, subtitle, *, flex="1 1 420px"):
    return html.Div(
        [
            html.H4(title, style={"margin": 0, "fontSize": "16px", "fontWeight": 700, "color": INK_PRIMARY}),
            html.P(subtitle, style={"margin": "0.2rem 0 0", "fontSize": "12.5px", "color": INK_MUTED}),
            dcc.Graph(
                id=graph_id,
                config={"displayModeBar": False, "responsive": True},
                style={"marginTop": "0.4rem", "height": "340px", "width": "100%"},
            ),
        ],
        style={**CARD_STYLE, "flex": flex, "minWidth": "380px"},
    )


def _filter_group(title, filter_id, *, flex, divider=True):
    style = {"flex": flex, "minWidth": "200px", "padding": "0 1.4rem"}
    if divider:
        style["borderLeft"] = f"1px solid {HAIRLINE}"
    return html.Div(
        [
            html.Div(title.upper(), style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.06em", "color": INK_MUTED, "marginBottom": "0.55rem"}),
            dcc.Checklist(
                id=filter_id,
                options=[],
                value=[],
                inputStyle={"accentColor": BLUE, "marginRight": "6px", "width": "14px", "height": "14px", "cursor": "pointer", "verticalAlign": "middle"},
                labelStyle={"marginRight": "14px", "fontSize": "13px", "color": INK_PRIMARY, "cursor": "pointer", "display": "inline-flex", "alignItems": "center"},
                style={"display": "flex", "flexWrap": "wrap", "rowGap": "0.3rem"},
            ),
        ],
        style=style,
    )


def create_dash_app(server, url_base_pathname, metadata):
    app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/",
        requests_pathname_prefix=url_base_pathname.rstrip("/") + "/",
        title=metadata.get("title", "Student Performance"),
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
                    html.H1(metadata.get("title", "Student Performance") + " Insights", style={"margin": 0, "fontSize": "30px", "fontWeight": 800, "color": INK_PRIMARY, "letterSpacing": "-0.02em"}),
                    html.P("A quick look at how students are doing — grades, effort, and outcomes across departments.", style={"margin": "0.4rem 0 0", "fontSize": "14.5px", "color": INK_SECONDARY, "maxWidth": "640px"}),
                ],
                style={"background": HERO_BG, "border": f"1px solid {HAIRLINE}", "borderRadius": "20px", "padding": "1.6rem 1.8rem", "marginBottom": "1.5rem"},
            ),
            html.Div(
                [
                    _filter_group("Department", "department-filter", flex="1.3 1 260px", divider=False),
                    _filter_group("Gender", "gender-filter", flex="1 1 200px"),
                    _filter_group("Family Income", "income-filter", flex="1 1 220px"),
                    _filter_group("Extracurricular", "extracurricular-filter", flex="1 1 200px"),
                    html.Div(html.Button("Reset", id="reset-filters", n_clicks=0, style={"border": "none", "backgroundColor": "transparent", "color": BLUE, "fontSize": "13px", "fontWeight": 700, "cursor": "pointer", "padding": 0}), style={"flex": "0 0 auto", "alignSelf": "center", "paddingLeft": "0.5rem"}),
                ],
                style={**CARD_STYLE, "display": "flex", "flexWrap": "wrap", "alignItems": "flex-start", "padding": "1.2rem 1rem", "marginBottom": "0.6rem"},
            ),
            html.Div(id="filter-caption", style={"fontSize": "12.5px", "color": INK_MUTED, "margin": "0 0.4rem 1rem"}),
            html.Div(id="insight-panel", style={"backgroundColor": INSIGHT_BG, "borderRadius": "18px", "padding": "1.2rem 1.5rem", "marginBottom": "1.5rem"}),
            html.Div(id="kpi-row", style={"display": "grid", "gridTemplateColumns": "repeat(6, minmax(0, 1fr))", "gap": "0.85rem", "marginBottom": "1.5rem"}),
            html.Div(
                [
                    _chart_card("grade-distribution-chart", "How students are grading out", "Count of students per letter grade"),
                    _chart_card("department-chart", "Average score by subject area", "Which department scores highest on average"),
                    _chart_card("components-chart", "Where students are strongest and weakest", "Average score across each assessment type"),
                    _chart_card("attendance-chart", "Does attendance affect performance?", "Average score by attendance band"),
                    _chart_card("study-hours-chart", "Does studying more pay off?", "Average score by weekly study time", flex="1 1 100%"),
                    _chart_card("income-chart", "Is there a score gap by family income?", "Average score by family income level"),
                ],
                style={"display": "flex", "flexWrap": "wrap", "gap": "1.1rem"},
            ),
            html.Div(id="error-panel", style={"marginTop": "1.25rem"}),
        ],
        style={
            "fontFamily": FONT_FAMILY,
            "margin": "0 auto",
            "maxWidth": "1360px",
            "padding": "2rem 2rem 3rem",
            "backgroundColor": PAGE_PLANE,
            "minHeight": "100vh",
        },
    )

    @app.callback(
        [Output(filter_id, "options") for filter_id, _c, _t in FILTER_GROUPS]
        + [Output(filter_id, "value") for filter_id, _c, _t in FILTER_GROUPS]
        + [Output("filter-universe", "data")],
        Input("init-load", "n_intervals"),
    )
    def populate_filters(_n_intervals):
        rows = load_rows(server, metadata, __file__, "queries/business/filter_options.sql")
        by_dimension = {}
        if not has_error(rows):
            for row in rows:
                by_dimension.setdefault(row.get("DIMENSION"), []).append(row.get("VALUE"))

        options_list = []
        values_list = []
        for _filter_id, column, _title in FILTER_GROUPS:
            distinct_values = by_dimension.get(column, [])
            options_list.append([{"label": value, "value": value} for value in distinct_values])
            values_list.append(list(distinct_values))
        return options_list + values_list + [by_dimension]

    @app.callback(
        [Output(filter_id, "value", allow_duplicate=True) for filter_id, _c, _t in FILTER_GROUPS],
        Input("reset-filters", "n_clicks"),
        State("filter-universe", "data"),
        prevent_initial_call=True,
    )
    def reset_filters(_n_clicks, filter_universe):
        filter_universe = filter_universe or {}
        return [list(filter_universe.get(column, [])) for _filter_id, column, _title in FILTER_GROUPS]

    @app.callback(
        Output("filter-caption", "children"),
        Output("insight-panel", "children"),
        Output("kpi-row", "children"),
        Output("grade-distribution-chart", "figure"),
        Output("department-chart", "figure"),
        Output("components-chart", "figure"),
        Output("attendance-chart", "figure"),
        Output("study-hours-chart", "figure"),
        Output("income-chart", "figure"),
        Output("error-panel", "children"),
        Input("refresh", "n_intervals"),
        Input("department-filter", "value"),
        Input("gender-filter", "value"),
        Input("income-filter", "value"),
        Input("extracurricular-filter", "value"),
        State("filter-universe", "data"),
    )
    def refresh_dashboard(_n_intervals, department, gender, income, extracurricular, filter_universe):
        params = _filter_params(department, gender, income, extracurricular, filter_universe)

        summary_row = load_row(server, metadata, __file__, "queries/business/summary.sql", params=params)
        grade_rows = load_rows(server, metadata, __file__, "queries/business/grade_distribution.sql", params=params)
        department_rows = load_rows(server, metadata, __file__, "queries/business/scores_by_department.sql", params=params)
        components_row = load_row(server, metadata, __file__, "queries/business/score_components.sql", params=params)
        attendance_rows = load_rows(server, metadata, __file__, "queries/business/attendance_band.sql", params=params)
        study_hours_rows = load_rows(server, metadata, __file__, "queries/business/study_hours_band.sql", params=params)
        income_rows = load_rows(server, metadata, __file__, "queries/business/income_level.sql", params=params)

        errors = []
        for label, payload in (
            ("summary", summary_row), ("grade_distribution", grade_rows), ("scores_by_department", department_rows),
            ("score_components", components_row), ("attendance_band", attendance_rows),
            ("study_hours_band", study_hours_rows), ("income_level", income_rows),
        ):
            if has_error(payload):
                error_row = payload[0] if isinstance(payload, list) else payload
                errors.append(f"{label}: {error_row['_error']}")

        if has_error(summary_row):
            caption = "Unable to load summary for the current filters."
        else:
            student_count = int((summary_row or {}).get("STUDENT_COUNT") or 0)
            total_students = int((summary_row or {}).get("TOTAL_STUDENTS") or 0)
            caption = f"Showing {student_count:,} of {total_students:,} students"

        component_rows = []
        if not has_error(components_row) and components_row:
            component_rows = [
                {"LABEL": "Midterm", "VALUE": components_row.get("AVG_MIDTERM") or 0},
                {"LABEL": "Final", "VALUE": components_row.get("AVG_FINAL") or 0},
                {"LABEL": "Assignments", "VALUE": components_row.get("AVG_ASSIGNMENTS") or 0},
                {"LABEL": "Quizzes", "VALUE": components_row.get("AVG_QUIZZES") or 0},
                {"LABEL": "Participation", "VALUE": components_row.get("AVG_PARTICIPATION") or 0},
                {"LABEL": "Projects", "VALUE": components_row.get("AVG_PROJECTS") or 0},
            ]
        elif has_error(components_row):
            component_rows = components_row

        headline, support = _build_insight(grade_rows, study_hours_rows)
        insight_children = [
            html.Div("KEY INSIGHT", style={"fontSize": "10.5px", "fontWeight": 700, "letterSpacing": "0.08em", "color": "#93a1e8", "marginBottom": "0.4rem"}),
            html.Div(headline, style={"fontSize": "17px", "fontWeight": 700, "color": "#ffffff", "lineHeight": 1.35}),
            html.Div(support, style={"fontSize": "13px", "color": "#c3c9e8", "marginTop": "0.4rem", "lineHeight": 1.5}),
        ]

        kpi_cards = _kpi_cards(summary_row)
        grade_figure = _vertical_bar_figure(
            grade_rows, source_file="grade_distribution.sql", x_title="Grade", y_title="Number of Students",
            colors=GRADE_COLORS, decimals=0, value_suffix="", category_order=GRADE_ORDER,
        )
        department_figure = _horizontal_bar_figure(
            department_rows, source_file="scores_by_department.sql", x_title="Average Overall Score (%)", color=VIOLET,
        )
        components_figure = _vertical_bar_figure(
            component_rows, source_file="score_components.sql", x_title="Assessment Type", y_title="Average Score (%)",
            colors=BLUE,
        )
        attendance_figure = _vertical_bar_figure(
            attendance_rows, source_file="attendance_band.sql", x_title="Attendance Band", y_title="Average Overall Score (%)",
            colors=AQUA, category_order=ATTENDANCE_ORDER,
        )
        study_hours_figure = _vertical_bar_figure(
            study_hours_rows, source_file="study_hours_band.sql", x_title="Weekly Study Time", y_title="Average Overall Score (%)",
            colors=AQUA, category_order=STUDY_HOURS_ORDER, flat_hint=True,
        )
        income_figure = _vertical_bar_figure(
            income_rows, source_file="income_level.sql", x_title="Family Income Level", y_title="Average Overall Score (%)",
            colors=ORANGE, category_order=INCOME_ORDER,
        )

        error_panel = render_error_panel("\n".join(errors)) if errors else None
        return (
            caption, insight_children, kpi_cards, grade_figure, department_figure,
            components_figure, attendance_figure, study_hours_figure, income_figure, error_panel,
        )

    return app
