from typing import Callable

from dash import html, dcc
import webviz_core_components as wcc

from .selections_view import (
    table_selections_layout,
    varviz_selections_layout,
    plot_selections_layout,
)


def main_view(
    get_uuid: Callable,
    responses,
    selectors,
    channel_dframe,
    variogram_dframe,
    variogram_filters,
    variogram_responses,
    analouge_dframe,
    analouge_selectors,
    analouge_responses,
) -> dcc.Tabs:

    tabs = [
        wcc.Tab(
            label="Plots",
            value="plots",
            children=tab_view_layout(
                main_layout=wcc.Frame(
                    color="white",
                    highlight=False,
                    style={"height": "91vh"},
                    children=[
                        wcc.RadioItems(
                            vertical=False,
                            id=get_uuid("main-plots-display-option"),
                            options=[
                                {
                                    "label": "Plot with table",
                                    "value": "plot_with_table",
                                },
                                {
                                    "label": "Plot",
                                    "value": "plot",
                                },
                                {
                                    "label": "Table",
                                    "value": "table",
                                },
                            ],
                            value="plot_with_table",
                        ),
                        html.Div(id=get_uuid("main-plots")),
                    ],
                ),
                sidebar_layout=[
                    plot_selections_layout(
                        uuid=get_uuid("selections-plots"),
                        responses=responses,
                        selectors=selectors,
                        dframe=channel_dframe,
                    )
                ],
            ),
        ),
        wcc.Tab(
            label="Tables",
            value="tables",
            children=tab_view_layout(
                main_layout=wcc.Frame(
                    color="white",
                    highlight=False,
                    style={"height": "91vh"},
                    children=html.Div(id=get_uuid("main-table")),
                ),
                sidebar_layout=[
                    table_selections_layout(
                        uuid=get_uuid("selections-table"),
                        responses=responses,
                        filters=selectors,
                        dframe=channel_dframe,
                    )
                ],
            ),
        ),
        wcc.Tab(
            label="Variogram visualization",
            value="varviz",
            children=tab_view_layout(
                main_layout=wcc.FlexBox(
                    [
                        wcc.Frame(
                            style={"flex": 5, "height": "91vh"},
                            children=wcc.Graph(
                                style={"height": "91vh"}, id=get_uuid("varviz-scatter")
                            ),
                        ),
                        wcc.Frame(
                            id=get_uuid("varviz-image-wrapper"),
                            style={"flex": 2, "height": "91vh"},
                            children=[],
                        ),
                    ]
                ),
                sidebar_layout=[
                    varviz_selections_layout(
                        uuid=get_uuid("selections-varviz"),
                        dframe=variogram_dframe,
                        filters=variogram_filters,
                        responses=variogram_responses,
                    )
                ],
            ),
        ),
        wcc.Tab(
            label="Analouge data",
            value="analouge",
            children=tab_view_layout(
                main_layout=wcc.Frame(
                    color="white",
                    highlight=False,
                    style={"height": "91vh"},
                    children=html.Div(id=get_uuid("main-table-analouge")),
                ),
                sidebar_layout=[
                    table_selections_layout(
                        uuid=get_uuid("selections-table-analouge"),
                        responses=analouge_responses,
                        filters=analouge_selectors,
                        dframe=analouge_dframe,
                    )
                ],
            ),
        ),
    ]

    return wcc.Tabs(
        id=get_uuid("tabs"),
        value="tables",
        style={"width": "100%"},
        persistence=True,
        children=tabs,
    )


def tab_view_layout(main_layout: list, sidebar_layout: list) -> wcc.FlexBox:
    return wcc.FlexBox(
        children=[
            wcc.Frame(
                style={"flex": 1, "height": "91vh"},
                children=sidebar_layout,
            ),
            html.Div(
                style={"flex": 6, "height": "91vh"},
                children=main_layout,
            ),
        ]
    )
