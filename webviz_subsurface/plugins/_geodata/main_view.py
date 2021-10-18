from typing import Callable

from dash import html, dcc
import webviz_core_components as wcc

from .selections_view import (
    table_selections_layout,
    varviz_selections_layout,
    plot_selections_layout,
    main_display_selector,
)


def main_view(get_uuid: Callable, cmodel, vmodel, amodel, smdamodel) -> dcc.Tabs:

    tabs = [
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
                        uuid=get_uuid("ui"),
                        tab="tables",
                        responses=cmodel.responses,
                        filters=cmodel.selectors,
                        dframe=cmodel.dframe,
                    )
                ],
            ),
        ),
        wcc.Tab(
            label="Channel visualization",
            value="plots",
            children=tab_view_layout(
                main_layout=wcc.Frame(
                    color="white",
                    highlight=False,
                    style={"height": "91vh"},
                    children=[
                        main_display_selector(
                            uuid=get_uuid("main-plots-display-option")
                        ),
                        html.Div(id=get_uuid("main-plots")),
                    ],
                ),
                sidebar_layout=[
                    plot_selections_layout(
                        uuid=get_uuid("ui"),
                        tab="plots",
                        responses=cmodel.responses,
                        selectors=cmodel.selectors,
                        dframe=cmodel.dframe,
                        amodel=amodel,
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
                            children=[
                                main_display_selector(
                                    uuid=get_uuid("main-varviz-display-option")
                                ),
                                html.Div(id=get_uuid("varviz-main")),
                            ],
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
                        uuid=get_uuid("ui"),
                        tab="varviz",
                        dframe=vmodel.dframe,
                        filters=vmodel.selectors,
                        responses=vmodel.responses,
                    )
                ],
            ),
        ),
        wcc.Tab(
            label="Analogue data",
            value="analogue",
            children=tab_view_layout(
                main_layout=wcc.Frame(
                    color="white",
                    highlight=False,
                    style={"height": "91vh"},
                    children=html.Div(id=get_uuid("main-table-analogue")),
                ),
                sidebar_layout=[
                    table_selections_layout(
                        uuid=get_uuid("ui"),
                        tab="analogue",
                        responses=amodel.responses,
                        filters=amodel.selectors,
                        dframe=amodel.dframe,
                    )
                ],
            ),
        ),
        wcc.Tab(
            label="SMDA data",
            value="smda",
            children=tab_view_layout(
                main_layout=wcc.Frame(
                    color="white",
                    highlight=False,
                    style={"height": "91vh"},
                    children=html.Div(id=get_uuid("main-table-smda")),
                ),
                sidebar_layout=[
                    table_selections_layout(
                        uuid=get_uuid("ui"),
                        tab="smda",
                        responses=smdamodel.responses,
                        filters=smdamodel.selectors,
                        dframe=smdamodel.dframe,
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
