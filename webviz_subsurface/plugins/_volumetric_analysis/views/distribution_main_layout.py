import webviz_core_components as wcc
from dash import html


def distributions_main_layout(uuid: str) -> html.Div:
    return html.Div(
        children=[
            html.Div(
                id={"id": uuid, "page": "custom"},
                style={"display": "none"},
                children=custom_plotting_layout(uuid),
            ),
            html.Div(
                id={"id": uuid, "page": "1p1t"},
                style={"display": "block"},
                children=one_plot_one_table_layout(uuid),
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


def custom_plotting_layout(uuid: str) -> html.Div:
    return wcc.Frame(
        color="white",
        highlight=False,
        style={"height": "91vh"},
        children=[
            wcc.RadioItems(
                id={"id": uuid, "element": "plot-table-select"},
                options=[
                    {"label": "Plot", "value": "graph"},
                    {"label": "Table", "value": "table"},
                ],
                value="graph",
                vertical=False,
            ),
            html.Div(
                id={"id": uuid, "wrapper": "graph", "page": "custom"},
                style={"display": "inline"},
                children=wcc.Graph(
                    id={"id": uuid, "element": "graph", "page": "custom"},
                    config={"displayModeBar": False},
                    style={"height": "85vh"},
                ),
            ),
            html.Div(
                id={"id": uuid, "wrapper": "table", "page": "custom"},
                style={"display": "none"},
            ),
        ],
    )


def one_plot_one_table_layout(uuid: str) -> html.Div:
    return html.Div(
        children=[
            wcc.Frame(
                color="white",
                highlight=False,
                style={"height": "44vh"},
                children=wcc.Graph(
                    id={"id": uuid, "element": "graph", "page": "1p1t"},
                    config={"displayModeBar": False},
                    style={"height": "44vh"},
                ),
            ),
            wcc.Frame(
                color="white",
                highlight=False,
                style={"height": "44vh"},
                id={"id": uuid, "wrapper": "table", "page": "1p1t"},
                children=[],
            ),
        ]
    )


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
