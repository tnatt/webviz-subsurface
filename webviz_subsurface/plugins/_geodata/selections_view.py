from typing import List, Optional
from dash import html
import webviz_core_components as wcc


def plot_selections_layout(
    uuid: str, responses, selectors, dframe, tab: str, amodel=None
) -> wcc.Selectors:
    return html.Div(
        children=[
            wcc.Selectors(
                label="PLOT CONTROLS",
                open_details=True,
                children=plot_selector_dropdowns(
                    uuid=uuid, tab=tab, responses=responses, selectors=selectors
                )
                + [display_analogue_data(uuid=uuid, tab=tab)],
            ),
            wcc.Selectors(
                label="⚙️ SETTINGS",
                open_details=False,
                children=[
                    histogram_options(uuid=uuid, tab=tab),
                    subplot_axis_range(uuid=uuid, tab=tab),
                ],
            ),
            wcc.Selectors(
                label="FILTERS",
                open_details=True,
                children=[
                    filter_dropdowns(
                        uuid=uuid, tab=tab, filters=selectors, dframe=dframe
                    ),
                ]
                + [analogue_filter_dropdowns(uuid=uuid, tab=tab, amodel=amodel)]
                if amodel is not None
                else [],
            ),
        ]
    )


def table_selections_layout(
    uuid: str, tab: str, responses, filters, dframe
) -> wcc.Selectors:
    return html.Div(
        children=[
            wcc.Selectors(
                label="TABLE CONTROLS",
                open_details=True,
                children=([table_data_selector(uuid=uuid)] if tab == "tables" else [])
                + [
                    wcc.Dropdown(
                        label="Table type",
                        id={"id": uuid, "tab": tab, "selector": "Table type"},
                        options=[
                            {"label": elm, "value": elm}
                            for elm in ["Statistics table", "Mean table", "Full table"]
                        ],
                        value="Mean table",
                        clearable=False,
                    ),
                    wcc.SelectWithLabel(
                        label="Group by",
                        id={"id": uuid, "tab": tab, "selector": "Group by"},
                        options=[{"label": elm, "value": elm} for elm in filters],
                        value=[x for x in filters if len(dframe[x].unique()) > 1],
                        size=min(10, len(filters)),
                    ),
                    wcc.SelectWithLabel(
                        label="Responses",
                        id={"id": uuid, "tab": tab, "selector": "table_responses"},
                        options=[{"label": i, "value": i} for i in responses],
                        value=responses,
                        size=min(20, len(responses)),
                    ),
                ],
            ),
            wcc.Selectors(
                label="FILTERS",
                open_details=True,
                children=[
                    html.Button(
                        "Reset all filters",
                        className="reset-filter-btn",
                        id={"id": uuid, "tab": tab, "element": "reset-filters"},
                    ),
                    html.Div(
                        id={"id": uuid, "tab": tab, "element": "filter_wrapper"},
                        children=filter_dropdowns(
                            uuid=uuid, tab=tab, filters=filters, dframe=dframe
                        ),
                    ),
                ],
            ),
        ]
    )


def varviz_selections_layout(
    uuid: str, tab: str, filters, responses, dframe
) -> wcc.Selectors:
    return html.Div(
        children=[
            wcc.Selectors(
                label="SELECTORS",
                children=[
                    wcc.Dropdown(
                        label="x",
                        id={"id": uuid, "tab": tab, "selector": "x"},
                        options=[{"label": elm, "value": elm} for elm in responses],
                        value="correlation_range_minor",
                        clearable=False,
                    ),
                    wcc.Dropdown(
                        label="y",
                        id={"id": uuid, "tab": tab, "selector": "y"},
                        options=[{"label": elm, "value": elm} for elm in responses],
                        value="correlation_range_major",
                        clearable=False,
                    ),
                    wcc.Dropdown(
                        label="facet_col",
                        id={"id": uuid, "tab": tab, "selector": "facet_col"},
                        options=[{"label": elm, "value": elm} for elm in filters],
                        value=None,
                        clearable=True,
                    ),
                    wcc.Dropdown(
                        label="color",
                        id={"id": uuid, "tab": tab, "selector": "color"},
                        options=[
                            {"label": elm, "value": elm} for elm in responses + filters
                        ],
                        value="Crop box number",
                        clearable=True,
                    ),
                    wcc.Dropdown(
                        label="size",
                        id={"id": uuid, "tab": tab, "selector": "size"},
                        options=[
                            {"label": elm, "value": elm}
                            for elm in responses + ["Quality factor"]
                            if elm != "Azimuth"
                        ],
                        value=None,
                        clearable=True,
                    ),
                    wcc.Dropdown(
                        label="trendline",
                        id={"id": uuid, "tab": tab, "selector": "trendline"},
                        options=[
                            {"label": "Ordinary Least Square", "value": "ols"},
                            {"label": "Locally weighted smoothing", "value": "lowess"},
                        ],
                        value=None,
                        placeholder="Select algorithm",
                        clearable=True,
                    ),
                ],
            ),
            wcc.Selectors(
                label="FILTERS",
                open_details=True,
                children=[
                    filter_dropdowns(uuid=uuid, tab=tab, filters=filters, dframe=dframe)
                ],
            ),
        ]
    )


def filter_dropdowns(uuid: str, tab: str, filters, dframe) -> html.Div:
    """Makes dropdowns for each selector"""
    dropdowns: List[html.Div] = []

    for selector in filters:
        elements = list(dframe[selector].unique())
        if len(elements) > 1:
            dropdowns.append(
                html.Div(
                    children=wcc.SelectWithLabel(
                        label=selector.lower().capitalize(),
                        id={"id": uuid, "tab": tab, "filter": selector},
                        options=[{"label": i, "value": i} for i in elements],
                        value=elements,
                        multi=True,
                        size=min(15, len(elements)),
                    ),
                )
            )
    return html.Div(dropdowns)


def analogue_filter_dropdowns(uuid: str, tab: str, amodel) -> html.Div:
    """Makes dropdowns for each selector"""
    dropdowns: List[html.Div] = []

    for selector in amodel.selectors:
        elements = list(amodel.dframe[selector].unique())
        if len(elements) > 1:
            dropdowns.append(
                html.Div(
                    children=wcc.SelectWithLabel(
                        label=selector.lower().capitalize(),
                        id={"id": uuid, "tab": tab, "afilter": selector},
                        options=[{"label": i, "value": i} for i in elements],
                        value=elements,
                        multi=True,
                        size=min(15, len(elements)),
                    ),
                )
            )
    return html.Div(
        id={"id": uuid, "tab": tab, "element": "afilter_wrapper"},
        style={"display": "none"},
        children=[html.Label("Analogue filters:", className="webviz-underlined-label")]
        + dropdowns,
    )


def plot_selector_dropdowns(
    uuid: str, tab: str, responses, selectors
) -> List[html.Div]:
    """Makes dropdowns for each selector"""

    dropdowns: List[html.Div] = []
    value: Optional[str] = None

    for selector in ["plot_type", "x", "y", "facet_col", "color"]:
        if selector == "plot_type":
            elements = ["histogram", "scatter", "distribution", "box", "bar"]
            value = elements[0]
        if selector == "x":
            elements = responses
            value = elements[0]
        if selector == "y":
            elements = responses
            value = None
        if selector == "facet_col":
            elements = selectors
            value = None
        if selector == "color":
            elements = selectors
            value = None

        dropdowns.append(
            wcc.Dropdown(
                label=selector,
                id={"id": uuid, "tab": tab, "selector": selector},
                options=[{"label": elm, "value": elm} for elm in elements],
                value=value,
                clearable=selector in ["facet_col", "color", "y"],
            )
        )
    dropdowns.append(
        wcc.Dropdown(
            label="trendline",
            id={"id": uuid, "tab": tab, "selector": "trendline"},
            options=[
                {"label": "Ordinary Least Square", "value": "ols"},
                {"label": "Locally weighted smoothing", "value": "lowess"},
            ],
            value=None,
            placeholder="Select algorithm",
            clearable=True,
        )
    )
    return dropdowns


def display_analogue_data(uuid: str, tab: str) -> html.Div:
    return html.Div(
        style={"margin-top": "10px"},
        children=[
            html.Label("Observation controls:", className="webviz-underlined-label"),
            wcc.Checklist(
                id={"id": uuid, "tab": tab, "selector": "Analogue data"},
                options=[{"label": "Analogue data", "value": "Show"}],
                value=[],
            ),
            wcc.Checklist(
                id={"id": uuid, "tab": tab, "selector": "SMDA data"},
                options=[{"label": "SMDA data", "value": "Show"}],
                value=[],
            ),
            wcc.RadioItems(
                label="Color analogue data:",
                id={"id": uuid, "tab": tab, "selector": "Analogue color"},
                options=[
                    {"label": "Outcrop", "value": "Outcrop"},
                    {"label": "No color", "value": None},
                ],
                labelStyle={"display": "inline-flex", "margin-right": "5px"},
                value=None,
            ),
        ],
    )


def subplot_axis_range(uuid: str, tab: str) -> html.Div:
    axis_matches_layout = []
    for axis in ["X axis", "Y axis"]:
        axis_matches_layout.append(
            html.Div(
                children=wcc.Checklist(
                    id={"id": uuid, "tab": tab, "selector": f"{axis} matches"},
                    options=[{"label": f"Equal {axis} range", "value": "Equal"}],
                    value=["Equal"],
                )
            )
        )
    return html.Div(
        children=[
            html.Span("Subplot options:", style={"font-weight": "bold"}),
            html.Div(style={"margin-bottom": "10px"}, children=axis_matches_layout),
        ]
    )


def histogram_options(uuid: str, tab: str) -> html.Div:
    return html.Div(
        children=[
            wcc.RadioItems(
                label="Barmode:",
                id={"id": uuid, "tab": tab, "selector": "barmode"},
                options=[
                    {"label": "overlay", "value": "overlay"},
                    {"label": "group", "value": "group"},
                    {"label": "stack", "value": "stack"},
                ],
                labelStyle={"display": "inline-flex", "margin-right": "5px"},
                value="overlay",
            ),
            wcc.RadioItems(
                label="Histogram p90/mean/p10 lines:",
                id={"id": uuid, "tab": tab, "selector": "statlines"},
                options=[
                    {"label": "none", "value": None},
                    {"label": "mean", "value": "mean"},
                    {"label": "all", "value": "all"},
                ],
                labelStyle={"display": "inline-flex", "margin-right": "5px"},
                value=None,
            ),
            wcc.Slider(
                label="Histogram bins:",
                id={"id": uuid, "tab": tab, "selector": "nbins"},
                value=15,
                min=1,
                max=30,
            ),
        ]
    )


def main_display_selector(uuid):
    return wcc.RadioItems(
        vertical=False,
        id=uuid,
        options=[
            {"label": "Plot with table", "value": "plot_with_table"},
            {"label": "Plot", "value": "plot"},
        ],
        value="plot_with_table",
    )


def table_data_selector(uuid):
    return html.Div(
        style={"margin-bottom": "10px"},
        children=wcc.RadioItems(
            label="Data source",
            #  vertical=False,
            id={"id": uuid, "element": "table-data"},
            options=[
                {"label": "Digital Models: Channels", "value": "DM - Channels"},
                {"label": "Digital Models: Varigram", "value": "DM - Variogram"},
                {"label": "Analogue Data", "value": "Safari"},
                {"label": "SMDA Data", "value": "SMDA"},
            ],
            value="DM - Channels",
        ),
    )
