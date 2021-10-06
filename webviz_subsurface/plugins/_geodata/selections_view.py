from typing import List, Optional
from dash import html
import webviz_core_components as wcc
from webviz_config import WebvizConfigTheme


def plot_selections_layout(uuid: str, responses, selectors, dframe) -> wcc.Selectors:
    return html.Div(
        children=[
            wcc.Selectors(
                label="PLOT CONTROLS",
                open_details=True,
                children=plot_selector_dropdowns(
                    uuid=uuid, responses=responses, selectors=selectors
                ),
            ),
            wcc.Selectors(
                label="FILTERS",
                open_details=True,
                children=[
                    filter_dropdowns(uuid=uuid, filters=selectors, dframe=dframe)
                ],
            ),
        ]
    )


def table_selections_layout(uuid: str, responses, filters, dframe) -> wcc.Selectors:
    return html.Div(
        children=[
            wcc.Selectors(
                label="TABLE CONTROLS",
                open_details=True,
                children=[
                    wcc.Dropdown(
                        label="Table type",
                        id={"id": uuid, "selector": "Table type"},
                        options=[
                            {"label": elm, "value": elm}
                            for elm in ["Statistics table", "Mean table"]
                        ],
                        value="Mean table",
                        clearable=False,
                    ),
                    wcc.Dropdown(
                        label="Group by",
                        id={"id": uuid, "selector": "Group by"},
                        options=[{"label": elm, "value": elm} for elm in filters],
                        value=filters,
                        multi=True,
                    ),
                    wcc.SelectWithLabel(
                        label="Responses",
                        id={
                            "id": uuid,
                            "selector": "table_responses",
                        },
                        options=[{"label": i, "value": i} for i in responses],
                        value=responses,
                        size=min(
                            20,
                            len(responses),
                        ),
                    ),
                ],
            ),
            wcc.Selectors(
                label="FILTERS",
                open_details=True,
                children=[filter_dropdowns(uuid=uuid, filters=filters, dframe=dframe)],
            ),
        ]
    )


def varviz_selections_layout(uuid: str, filters, responses, dframe) -> wcc.Selectors:
    return html.Div(
        children=[
            wcc.Selectors(
                label="SELECTORS",
                children=[
                    wcc.Dropdown(
                        label="x",
                        id={"id": uuid, "selector": "x"},
                        options=[{"label": elm, "value": elm} for elm in responses],
                        value="correlation_range_minor",
                        clearable=False,
                    ),
                    wcc.Dropdown(
                        label="y",
                        id={"id": uuid, "selector": "y"},
                        options=[{"label": elm, "value": elm} for elm in responses],
                        value="correlation_range_major",
                        clearable=False,
                    ),
                    wcc.Dropdown(
                        label="Subplots",
                        id={"id": uuid, "selector": "facet_col"},
                        options=[{"label": elm, "value": elm} for elm in filters],
                        value=None,
                        clearable=True,
                    ),
                    wcc.Dropdown(
                        label="color",
                        id={"id": uuid, "selector": "color"},
                        options=[
                            {"label": elm, "value": elm} for elm in responses + filters
                        ],
                        value="Crop box number",
                        clearable=True,
                    ),
                    wcc.Dropdown(
                        label="size",
                        id={"id": uuid, "selector": "size"},
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
                        id={"id": uuid, "selector": "trendline"},
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
                children=[filter_dropdowns(uuid=uuid, filters=filters, dframe=dframe)],
            ),
        ]
    )


def filter_dropdowns(uuid: str, filters, dframe) -> html.Div:
    """Makes dropdowns for each selector"""
    dropdowns: List[html.Div] = []

    for selector in filters:
        elements = list(dframe[selector].unique())
        dropdowns.append(
            html.Div(
                children=wcc.SelectWithLabel(
                    label=selector.lower().capitalize(),
                    id={"id": uuid, "filter": selector},
                    options=[{"label": i, "value": i} for i in elements],
                    value=elements,
                    multi=True,
                    size=min(15, len(elements)),
                ),
            )
        )
    return html.Div(dropdowns)


def plot_selector_dropdowns(uuid: str, responses, selectors) -> List[html.Div]:
    """Makes dropdowns for each selector"""

    dropdowns: List[html.Div] = []
    value: Optional[str] = None

    for selector in [
        "Plot type",
        "X Response",
        "Y Response",
        "Subplots",
        "Color by",
    ]:
        if selector == "Plot type":
            elements = ["histogram", "scatter", "distribution", "box", "bar"]
            value = elements[0]
        if selector == "X Response":
            elements = responses
            value = elements[0]
        if selector == "Y Response":
            elements = responses
            value = None
        if selector == "Subplots":
            elements = selectors
            value = None
        if selector == "Color by":
            elements = selectors
            value = None

        dropdowns.append(
            wcc.Dropdown(
                label=selector,
                id={"id": uuid, "selector": selector},
                options=[{"label": elm, "value": elm} for elm in elements],
                value=value,
                clearable=selector in ["Subplots", "Color by", "Y Response"],
            )
        )
    dropdowns.append(
        wcc.Dropdown(
            label="Trendline",
            id={"id": uuid, "selector": "trendline"},
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


def settings_layout(uuid: str, theme: WebvizConfigTheme, tab: str) -> wcc.Selectors:

    theme_colors = theme.plotly_theme.get("layout", {}).get("colorway", [])
    return wcc.Selectors(
        label="⚙️ SETTINGS",
        open_details=False,
        children=[
            remove_fluid_annotation(uuid=uuid, tab=tab),
            subplot_xaxis_range(uuid=uuid, tab=tab),
            histogram_options(uuid=uuid, tab=tab),
            html.Span("Colors", style={"font-weight": "bold"}),
            wcc.ColorScales(
                id={"id": uuid, "tab": tab, "settings": "Colorscale"},
                colorscale=theme_colors,
                fixSwatches=True,
                nSwatches=12,
            ),
        ],
    )


def subplot_xaxis_range(uuid: str, tab: str) -> html.Div:
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


def table_sync_option(uuid: str, tab: str) -> html.Div:
    return html.Div(
        style={"margin-bottom": "10px"},
        children=wcc.Checklist(
            id={"id": uuid, "tab": tab, "selector": "sync_table"},
            options=[{"label": "Sync table with plot", "value": "Sync"}],
            value=["Sync"],
        ),
    )


def remove_fluid_annotation(uuid: str, tab: str) -> html.Div:
    return html.Div(
        style={"margin-bottom": "10px"},
        children=wcc.Checklist(
            id={"id": uuid, "tab": tab, "selector": "Fluid annotation"},
            options=[{"label": "Show fluid annotation", "value": "Show"}],
            value=["Show"],
        ),
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
            wcc.Slider(
                label="Histogram bins:",
                id={"id": uuid, "tab": tab, "selector": "hist_bins"},
                value=15,
                min=1,
                max=30,
            ),
        ]
    )
