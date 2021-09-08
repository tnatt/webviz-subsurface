import dash_html_components as html
import dash_core_components as dcc
import webviz_core_components as wcc
from webviz_subsurface._models import InplaceVolumesModel


def src_comparison_main_layout(uuid: str) -> html.Div:
    return html.Div(src_comparison_layout(uuid))


def src_comparison_layout(uuid: str) -> html.Div:
    return html.Div(
        children=[
            wcc.Frame(
                color="white",
                highlight=False,
                style={"height": "91vh"},
                children=[
                    html.Div(
                        style={"margin-bottom": "20px"},
                        children=wcc.RadioItems(
                            vertical=False,
                            id={"id": uuid, "element": "display-option"},
                            options=[
                                {
                                    "label": "QC plots",
                                    "value": "plots",
                                },
                                {
                                    "label": "Difference table for selected response",
                                    "value": "table",
                                },
                                {
                                    "label": "Difference table for multiple responses",
                                    "value": "info table",
                                },
                            ],
                            value="plots",
                        ),
                    ),
                    html.Div(id={"id": uuid, "wrapper": "table"}),
                ],
            )
        ]
    )


def src_comp_qc_plots_layout(
    fig_dif_vs_real,
    fig_corr,
    fig_diff_vs_response,
    barfig,
):

    return html.Div(
        children=[
            html.Div(
                children=wcc.Graph(
                    config={"displayModeBar": False},
                    style={"height": "22vh"},
                    figure=fig_dif_vs_real,
                )
            ),
            wcc.FlexBox(
                style={"height": "32vh"},
                children=[
                    wcc.FlexColumn(
                        children=wcc.Graph(
                            config={"displayModeBar": False},
                            style={"height": "31vh"},
                            figure=fig_diff_vs_response,
                        )
                    ),
                    wcc.FlexColumn(
                        children=wcc.Graph(
                            config={"displayModeBar": False},
                            style={"height": "31vh"},
                            figure=fig_corr,
                        )
                    ),
                ],
            ),
            wcc.Frame(
                style={"height": "31vh"},
                children=[
                    wcc.Header("Data outside acceptance criteria"),
                    wcc.Graph(
                        config={"displayModeBar": False},
                        style={"height": "25vh"},
                        figure=barfig,
                    )
                    if barfig is not None
                    else html.Div("All groups accepted"),
                ],
            ),
        ]
    )


def src_comp_table_layout(table, table_type, selections, filter_info):
    header = (
        (
            f"Table showing differences for {selections['Response']} "
            f"({selections['value2']} - {selections['value1']}):"
        )
        if table_type == "table"
        else "Table showing differences in percent for multiple responses:"
    )

    return html.Div(
        children=[
            wcc.Header(header),
            html.Div(
                style={"margin-bottom": "20px", "font-weight": "bold"},
                children=f"{filter_info.capitalize()} {selections['filters'][filter_info][0]}",
            ),
            table,
        ]
    )


def settings_layout(uuid: str, tab: str) -> wcc.Selectors:
    return wcc.Selectors(
        label="⚙️ SETTINGS",
        open_details=False,
        children=[
            diff_mode_selector(uuid, tab),
            colorby_selector(uuid, tab),
            axis_focus_selector(uuid, tab),
            remove_zero_responses(uuid, tab),
            remove_accepted(uuid, tab),
        ],
    )


def src_comp_selections(
    uuid: str, volumemodel: InplaceVolumesModel, tab: str, compare_on: str
) -> html.Div:
    """Layout for selecting tornado data"""
    elements = volumemodel.sources if compare_on == "SOURCE" else volumemodel.ensembles

    return html.Div(
        children=[
            wcc.Selectors(
                label="PLOT CONROLS",
                open_details=True,
                children=[
                    source_selector(
                        uuid,
                        tab,
                        label=f"{compare_on.capitalize()} A",
                        selector_label="value1",
                        value=elements[0],
                        elements=elements,
                    ),
                    source_selector(
                        uuid,
                        tab,
                        label=f"{compare_on.capitalize()} B",
                        selector_label="value2",
                        value=elements[1] if compare_on == "SOURCE" else elements[-1],
                        elements=elements,
                    ),
                    response_selector(volumemodel, uuid, tab),
                    group_by_selector(volumemodel, uuid, tab),
                    acceptance_controls(uuid, tab),
                ],
            ),
            settings_layout(uuid, tab),
        ]
    )


def axis_focus_selector(uuid: str, tab: str) -> html.Div:
    return wcc.Checklist(
        id={"id": uuid, "tab": tab, "selector": "Axis focus"},
        options=[{"label": "Focus diff plots on non-accepted", "value": "focus"}],
        value=["focus"],
    )


def remove_zero_responses(uuid: str, tab: str) -> html.Div:
    return wcc.Checklist(
        id={"id": uuid, "tab": tab, "selector": "Remove zeros"},
        options=[{"label": "Remove data with no volume", "value": "remove"}],
        value=["remove"],
    )


def remove_accepted(uuid: str, tab: str) -> html.Div:
    return wcc.Checklist(
        id={"id": uuid, "tab": tab, "selector": "Remove accepted"},
        options=[{"label": "Remove accepted data from table", "value": "remove"}],
        value=[],
    )


def diff_mode_selector(uuid: str, tab: str):
    return wcc.RadioItems(
        label="Show difference in",
        id={"id": uuid, "tab": tab, "selector": "Diff mode"},
        options=[
            {"label": "Percent", "value": "diff (%)"},
            {"label": "True value", "value": "diff"},
        ],
        labelStyle={"display": "inline-flex", "margin-right": "5px"},
        value="diff (%)",
    )


def acceptance_controls(uuid: str, tab: str) -> html.Div:
    return html.Div(
        style={"margin-top": "20px"},
        children=[
            html.Label("Acceptance controls", className="webviz-underlined-label"),
            html.Div(
                children=[
                    wcc.Label("Accepted absolute diff (%):"),
                    dcc.Input(
                        id={"id": uuid, "tab": tab, "selector": "Accept value"},
                        type="number",
                        required=True,
                        value=5,
                        persistence=True,
                        persistence_type="session",
                    ),
                ],
            ),
            html.Div(
                children=[
                    wcc.Label("Ignore response values below:"),
                    dcc.Input(
                        id={"id": uuid, "tab": tab, "selector": "Ignore value"},
                        type="number",
                        required=True,
                        value=0,
                        persistence=True,
                        persistence_type="session",
                        debounce=True,
                    ),
                ]
            ),
        ],
    )


def source_selector(
    uuid: str,
    tab: str,
    label: str,
    selector_label: str,
    value: str,
    elements: list,
) -> wcc.Dropdown:

    return wcc.Dropdown(
        label=label,
        id={"id": uuid, "tab": tab, "selector": selector_label},
        options=[{"label": src, "value": src} for src in elements],
        value=value,
        clearable=False,
    )


def response_selector(
    volumemodel: InplaceVolumesModel,
    uuid: str,
    tab: str,
) -> html.Div:
    return html.Div(
        style={"margin-top": "10px"},
        children=wcc.Dropdown(
            id={
                "id": uuid,
                "tab": tab,
                "selector": "Response",
            },
            label="Response",
            options=[{"label": i, "value": i} for i in volumemodel.responses],
            value=volumemodel.volume_columns[0],
            clearable=False,
        ),
    )


def colorby_selector(
    uuid: str,
    tab: str,
) -> html.Div:
    return html.Div(
        style={"margin": "10px 0px"},
        children=wcc.RadioItems(
            label="Color plots on",
            id={"id": uuid, "tab": tab, "selector": "Color by"},
            options=[
                {"label": "Accepted", "value": "accepted"},
                {"label": "1st groupby", "value": "groups"},
            ],
            labelStyle={"display": "inline-flex", "margin-right": "5px"},
            value="accepted",
        ),
    )


def group_by_selector(
    volumemodel: InplaceVolumesModel,
    uuid: str,
    tab: str,
) -> html.Div:
    available_selectors = [
        x
        for x in ["FIPNUM", "SET", "REGION", "ZONE", "REAL"]
        if x in volumemodel.selectors
    ]
    return html.Div(
        style={"margin-top": "10px"},
        children=wcc.Dropdown(
            label="Group by",
            id={"id": uuid, "tab": tab, "selector": "Group by"},
            options=[{"label": elm, "value": elm} for elm in available_selectors],
            value=[available_selectors[0]],
            multi=True,
            clearable=False,
        ),
    )
