from typing import Callable
import pandas as pd
import dash_html_components as html
import dash_core_components as dcc
import webviz_core_components as wcc
from webviz_config import WebvizConfigTheme
from webviz_subsurface._models import InplaceVolumesModel
from .filter_view import filter_layout
from .distribution_main_layout import distributions_main_layout, table_main_layout
from .selections_view import selections_layout, table_selections_layout
from .tornado_selections_view import tornado_selections_layout
from .tornado_layout import tornado_main_layout
from .src_comparison_layout import src_comparison_main_layout, src_comp_selections
from .set_layout import set_filter_layout, set_main_layout, set_selections_layout


def main_view(
    get_uuid: Callable,
    volumemodel: InplaceVolumesModel,
    theme: WebvizConfigTheme,
    disjoint_set_df: pd.DataFrame = None,
) -> dcc.Tabs:

    tabs = [
        wcc.Tab(
            label="Inplace distributions",
            value="voldist",
            children=tab_view_layout(
                main_layout=distributions_main_layout(
                    uuid=get_uuid("main-voldist"), volumemodel=volumemodel
                ),
                sidebar_layout=[
                    selections_layout(
                        uuid=get_uuid("selections"),
                        tab="voldist",
                        volumemodel=volumemodel,
                        theme=theme,
                    ),
                    filter_layout(
                        uuid=get_uuid("filters"),
                        tab="voldist",
                        volumemodel=volumemodel,
                        hide_selectors=["SENSTYPE"],
                    ),
                ],
            ),
        )
    ]
    tabs.append(
        wcc.Tab(
            label="Tables",
            value="table",
            children=tab_view_layout(
                main_layout=table_main_layout(
                    uuid=get_uuid("main-table"),
                ),
                sidebar_layout=[
                    table_selections_layout(
                        uuid=get_uuid("selections"),
                        tab="table",
                        volumemodel=volumemodel,
                    ),
                    filter_layout(
                        open_details=True,
                        uuid=get_uuid("filters"),
                        tab="table",
                        volumemodel=volumemodel,
                        hide_selectors=["SENSTYPE"],
                    ),
                ],
            ),
        )
    )
    if volumemodel.sensrun:
        tabs.append(
            wcc.Tab(
                label="Tornadoplots",
                value="tornado",
                children=tab_view_layout(
                    main_layout=tornado_main_layout(
                        uuid=get_uuid("main-tornado"),
                    ),
                    sidebar_layout=[
                        tornado_selections_layout(
                            uuid=get_uuid("selections"),
                            tab="tornado",
                            volumemodel=volumemodel,
                        ),
                        filter_layout(
                            open_details=True,
                            uuid=get_uuid("filters"),
                            tab="tornado",
                            volumemodel=volumemodel,
                            hide_selectors=[
                                "SENSCASE",
                                "SENSNAME",
                                "SENSTYPE",
                            ],
                        ),
                    ],
                ),
            )
        )
    if len(volumemodel.sources) > 1:
        tabs.append(
            wcc.Tab(
                label="Source comparison",
                value="src-comp",
                children=tab_view_layout(
                    main_layout=src_comparison_main_layout(get_uuid("main-src-comp")),
                    sidebar_layout=[
                        src_comp_selections(
                            uuid=get_uuid("selections"),
                            tab="src-comp",
                            volumemodel=volumemodel,
                        )
                    ]
                    + [
                        filter_layout(
                            open_details=True,
                            uuid=get_uuid("filters"),
                            tab="src-comp",
                            volumemodel=volumemodel,
                            hide_selectors=["SOURCE", "SENSTYPE"],
                        )
                    ],
                ),
            )
        )
    if len(volumemodel.ensembles) > 1:
        tabs.append(
            wcc.Tab(
                label="Ensemble comparison",
                value="ens-comp",
                children=tab_view_layout(
                    main_layout=[
                        html.Div(
                            "Under development - page for analyzing volume changes "
                            "and causes between ensembles (e.g between two model revision)",
                            style={"margin": "50px", "font-size": "20px"},
                        )
                    ],
                    sidebar_layout=filter_layout(
                        open_details=True,
                        uuid=get_uuid("filters"),
                        tab="ens-comp",
                        volumemodel=volumemodel,
                    ),
                ),
            )
        )
    if disjoint_set_df is not None:
        tabs.append(
            wcc.Tab(
                label="FIPNUM mapping QC",
                value="setinfo",
                children=tab_view_layout(
                    main_layout=set_main_layout(uuid=get_uuid("main-setinfo")),
                    sidebar_layout=[
                        set_selections_layout(
                            uuid=get_uuid("selections"), tab="setinfo"
                        ),
                        set_filter_layout(
                            uuid=get_uuid("filters"),
                            tab="setinfo",
                            disjoint_set_df=disjoint_set_df,
                        ),
                    ],
                ),
            )
        )

    return wcc.Tabs(
        id=get_uuid("tabs"),
        value="voldist" if not volumemodel.sensrun else "tornado",
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
