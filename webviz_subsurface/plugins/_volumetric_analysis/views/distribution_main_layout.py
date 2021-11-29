from typing import Optional
import webviz_core_components as wcc
from dash import html
import plotly.graph_objects as go


def distributions_main_layout(uuid: str) -> html.Div:
    return html.Div(
        children=[
            html.Div(
                id={"id": uuid, "page": "custom"},
                style={"display": "block"},
                children=custom_plotting_main_layout(uuid),
            ),
            html.Div(id={"id": uuid, "page": "per_zr"}, style={"display": "none"}),
            html.Div(
                id={"id": uuid, "page": "conv"},
                style={"display": "none"},
                children=convergence_plot_layout(uuid),
            ),
        ]
    )


def table_main_layout(uuid: str) -> html.Div:
    return wcc.Frame(
        id={"id": uuid, "wrapper": "table", "page": "table"},
        color="white",
        highlight=False,
        style={"height": "91vh"},
        children=[],
    )


def convergence_plot_layout(uuid: str) -> html.Div:
    return wcc.Frame(
        color="white",
        highlight=False,
        style={"height": "91vh"},
        children=[
            wcc.Graph(
                id={"id": uuid, "element": "plot", "page": "conv"},
                config={"displayModeBar": False},
                style={"height": "85vh"},
            )
        ],
    )


def custom_plotting_main_layout(uuid: str) -> html.Div:
    return wcc.Frame(
        color="white",
        highlight=False,
        style={"height": "91vh"},
        children=[
            wcc.RadioItems(
                id={"id": uuid, "element": "plot-table-select"},
                options=[
                    {"label": "Plot with table", "value": "plot_and_table"},
                    {"label": "Plot", "value": "plot"},
                ],
                value="plot",
                vertical=False,
            ),
            html.Div(id={"id": uuid, "wrapper": "plot-area", "page": "custom"}),
        ],
    )


def custom_plotting_layout(figure: go.Figure, table: Optional[list]) -> html.Div:
    height = "85vh" if table is None else "44vh"
    layout = [
        wcc.Graph(
            config={"displayModeBar": False}, style={"height": height}, figure=figure
        )
    ]
    if table is not None:
        layout.append(table)
    return html.Div(layout)


def plots_per_zone_region_layout(figures: list) -> list:
    height = "42vh" if len(figures) < 3 else "25vh"
    return [
        wcc.Frame(
            color="white",
            highlight=False,
            style={"height": height},
            children=wcc.FlexBox(
                children=[
                    html.Div(
                        style={"flex": 1},
                        children=wcc.Graph(
                            config={"displayModeBar": False},
                            style={"height": height},
                            figure=piefig,
                        ),
                    ),
                    html.Div(
                        style={"flex": 3},
                        children=wcc.Graph(
                            config={"displayModeBar": False},
                            style={"height": height},
                            figure=barfig,
                        ),
                    ),
                ]
            ),
        )
        for piefig, barfig in figures
    ]
