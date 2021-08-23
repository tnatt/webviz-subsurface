import dash_html_components as html
import dash_core_components as dcc
import webviz_core_components as wcc
from webviz_subsurface._models import InplaceVolumesModel


def src_comparison_main_layout(uuid: str) -> html.Div:
    return html.Div(
        id={"id": uuid, "page": "src-comp"},
        style={"display": "block"},
        children=src_comparison_layout(uuid),
    )


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
                                {"label": "Table", "value": "table"},
                            ],
                            value="plots",
                        ),
                    ),
                    html.Div(id={"id": uuid, "wrapper": "table", "page": "src-comp"}),
                ],
            )
        ]
    )


def src_comp_qc_plots_layout(
    fig_dif_vs_real,
    fig_corr,
    fig_diff_vs_response,
    fig_distribution,
    non_accepted_count_group,
    non_accepted_count_real,
    selectors,
    response,
    source1,
    source2,
):
    selectors = selectors if selectors else ["Total"]

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
                            figure=fig_corr,
                        )
                    ),
                    wcc.FlexColumn(
                        children=wcc.Graph(
                            config={"displayModeBar": False},
                            style={"height": "31vh"},
                            figure=fig_diff_vs_response,
                        )
                    ),
                ],
            ),
            wcc.FlexBox(
                style={"height": "32vh"},
                children=[
                    wcc.FlexColumn(
                        children=wcc.Graph(
                            config={"displayModeBar": False},
                            style={"height": "31vh"},
                            figure=fig_distribution,
                        )
                    ),
                    wcc.FlexColumn(
                        wcc.Frame(
                            style={"height": "25vh"},
                            children=[
                                wcc.Header(
                                    f"Summary - {response} differences {source1} vs {source2}"
                                ),
                                html.Div(f"Data for group: {' '.join(selectors)}"),
                                html.Div(
                                    f"Groups outside acceptance criteria: {non_accepted_count_group}"
                                ),
                                html.Div(
                                    f"Realizations outside acceptance criteria: {non_accepted_count_real}"
                                ),
                                html.Div("See table for more details"),
                            ],
                        ),
                    ),
                ],
            ),
        ]
    )


def settings_layout(uuid: str, tab: str) -> wcc.Selectors:
    return wcc.Selectors(
        label="⚙️ SETTINGS",
        open_details=True,
        children=[
            diff_mode_selector(uuid, tab),
            sort_selector(uuid, tab),
            colorby_selector(uuid, tab),
            axis_focus_selector(uuid, tab),
        ],
    )


def src_comp_selections(
    uuid: str, volumemodel: InplaceVolumesModel, tab: str
) -> html.Div:
    """Layout for selecting tornado data"""
    return html.Div(
        children=[
            wcc.Selectors(
                label="PLOT CONROLS",
                open_details=True,
                children=[
                    source_selector(
                        volumemodel,
                        uuid,
                        tab,
                        label="Source A",
                        value=volumemodel.sources[0],
                    ),
                    source_selector(
                        volumemodel,
                        uuid,
                        tab,
                        label="Source B",
                        value=volumemodel.sources[1],
                    ),
                    response_selector(volumemodel, uuid, tab),
                    group_by_selector(volumemodel, uuid, tab),
                    acceptance_controls(uuid, tab),
                ],
            ),
            settings_layout(uuid, tab),
        ]
    )


def sort_selector(uuid: str, tab: str) -> html.Div:
    return wcc.Checklist(
        id={"id": uuid, "tab": tab, "selector": "Sort"},
        options=[{"label": "Sort table on difference (absolute)", "value": "sort"}],
        value=["sort"],
    )


def axis_focus_selector(uuid: str, tab: str) -> html.Div:
    return wcc.Checklist(
        id={"id": uuid, "tab": tab, "selector": "Axis focus"},
        options=[{"label": "Focus REAL plot on non-accepted", "value": "focus"}],
        value=["focus"],
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
                    wcc.Label("Disregard response values below:"),
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
    volumemodel: InplaceVolumesModel,
    uuid: str,
    tab: str,
    label: str,
    value: str,
) -> wcc.Dropdown:

    return wcc.Dropdown(
        label=label,
        id={"id": uuid, "tab": tab, "selector": label},
        options=[{"label": src, "value": src} for src in volumemodel.sources],
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
            options=[{"label": i, "value": i} for i in volumemodel.volume_columns],
            value=volumemodel.volume_columns[0],
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
