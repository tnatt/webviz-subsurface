from typing import Optional
import webviz_core_components as wcc
from dash import html
import plotly.graph_objects as go


def distributions_main_layout(uuid: str) -> html.Div:
    return wcc.Frame(
        color="white",
        highlight=False,
        style={"height": "91vh"},
        children=[
            html.Div(
                id={"id": uuid, "page": "custom"},
                style={"display": "block"},
                children=custom_plotting_main_layout(uuid),
            ),
            html.Div(
                id={"id": uuid, "page": "per_zr"},
                style={"display": "none"},
            ),
            html.Div(
                id={"id": uuid, "page": "conv"},
                style={"display": "none"},
            ),
        ],
    )


def table_main_layout(uuid: str) -> wcc.Frame:
    return wcc.Frame(
        id={"id": uuid, "wrapper": "table", "page": "table"},
        color="white",
        highlight=False,
        style={"height": "91vh"},
        children=[],
    )


def convergence_plot_layout(figure: go.Figure) -> wcc.Graph:
    return wcc.Graph(
        config={"displayModeBar": False}, style={"height": "85vh"}, figure=figure
    )


def custom_plotting_main_layout(uuid: str) -> list:
    return [
        wcc.RadioItems(
            id={"id": uuid, "element": "plot-table-select"},
            options=[
                {"label": "Plot with table", "value": "plot_and_table"},
                {"label": "Plot", "value": "plot"},
            ],
            value="plot_and_table",
            vertical=False,
        ),
        html.Div(id={"id": uuid, "wrapper": "plot-area", "page": "custom"}),
    ]


def custom_plotting_layout(figure: go.Figure, tables: Optional[list]) -> html.Div:
    height = "85vh" if tables is None else "44vh"
    layout = [
        wcc.Graph(
            config={"displayModeBar": False}, style={"height": height}, figure=figure
        )
    ]
    if tables is not None:
        layout.extend(
            [html.Div(table, style={"margin-top": "20px"}) for table in tables]
        )
    return html.Div(layout)


def plots_per_zone_region_layout(figures: list) -> list:
    height = "42vh" if len(figures) < 3 else "25vh"
    return [
        wcc.FlexBox(
            style={"height": height},
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
            ],
        )
        for piefig, barfig in figures
    ]
