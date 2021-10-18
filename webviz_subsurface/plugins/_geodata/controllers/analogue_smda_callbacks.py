from typing import Callable

from dash import Input, Output, State, ALL, callback, html
from dash.exceptions import PreventUpdate
import webviz_core_components as wcc

from webviz_subsurface._figures import create_figure
from ..utils import make_table


def analogue_smda_callbacks(get_uuid: Callable, amodel, smdamodel):
    @callback(
        Output(get_uuid("main-table-analogue"), "children"),
        Input({"id": get_uuid("ui"), "tab": "analogue", "selector": ALL}, "value"),
        Input({"id": get_uuid("ui"), "tab": "analogue", "filter": ALL}, "value"),
        Input(get_uuid("tabs"), "value"),
        State({"id": get_uuid("ui"), "tab": "analogue", "selector": ALL}, "id"),
        State({"id": get_uuid("ui"), "tab": "analogue", "filter": ALL}, "id"),
    )
    def update_analogue_table(
        table_selections: list,
        table_filters: list,
        selected_tab,
        selector_ids,
        filter_ids,
    ) -> list:

        if selected_tab != "analogue":
            raise PreventUpdate

        selections = {
            id_value["selector"]: value
            for id_value, value in zip(selector_ids, table_selections)
        }
        filters = {
            id_value["filter"]: value
            for id_value, value in zip(filter_ids, table_filters)
        }

        dframe = amodel.dframe.copy()
        for filt, values in filters.items():
            dframe = dframe.loc[dframe[filt].isin(values)]

        scatter = create_figure(
            plot_type="scatter",
            data_frame=dframe,
            x="channel height mean",
            y="channel width mean",
            color="Outcrop",
            color_discrete_map=amodel.colors,
            opacity=0.6,
        ).update_layout(
            margin={"l": 100, "r": 20, "t": 20, "b": 20},
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )

        bardf = dframe.groupby("Outcrop").mean().reset_index()
        barfig = create_outcrop_barfig(
            bardf, y="channel width mean", x="Outcrop", colors=amodel.colors
        )
        barfig2 = create_outcrop_barfig(
            bardf, y="channel height mean", x="Outcrop", colors=amodel.colors
        )

        return html.Div(
            children=[
                wcc.FlexBox(
                    style={"height": "50vh"},
                    children=[
                        wcc.FlexColumn(
                            flex=1,
                            children=html.Div(
                                [
                                    wcc.Graph(
                                        config={"displayModeBar": False},
                                        style={"height": "24vh"},
                                        figure=barfig,
                                    ),
                                    wcc.Graph(
                                        config={"displayModeBar": False},
                                        style={"height": "24vh"},
                                        figure=barfig2,
                                    ),
                                ]
                            ),
                        ),
                        wcc.FlexColumn(
                            flex=2,
                            children=wcc.Graph(
                                config={"displayModeBar": False},
                                style={"height": "48vh"},
                                figure=scatter,
                            ),
                        ),
                    ],
                ),
                make_table(
                    dframe,
                    selections["table_responses"],
                    tab="analogue",
                    table_type=selections["Table type"],
                    groups=selections["Group by"],
                    height="80vh",
                    selectors=amodel.selectors,
                ),
            ]
        )

    @callback(
        Output(get_uuid("main-table-smda"), "children"),
        Input({"id": get_uuid("ui"), "tab": "smda", "selector": ALL}, "value"),
        Input({"id": get_uuid("ui"), "tab": "smda", "filter": ALL}, "value"),
        Input(get_uuid("tabs"), "value"),
        State({"id": get_uuid("ui"), "tab": "smda", "selector": ALL}, "id"),
        State({"id": get_uuid("ui"), "tab": "smda", "filter": ALL}, "id"),
    )
    def update_smda_table(
        table_selections: list,
        table_filters: list,
        selected_tab,
        selector_ids,
        filter_ids,
    ) -> list:

        if selected_tab != "smda":
            raise PreventUpdate

        selections = {
            id_value["selector"]: value
            for id_value, value in zip(selector_ids, table_selections)
        }
        filters = {
            id_value["filter"]: value
            for id_value, value in zip(filter_ids, table_filters)
        }

        dframe = smdamodel.dframe.copy()
        for filt, values in filters.items():
            dframe = dframe.loc[dframe[filt].isin(values)]

        scatter = create_figure(
            plot_type="box",
            data_frame=dframe,
            x="thickness_md",
            #    y="identifier",
            color="identifier",
            color_discrete_map=smdamodel.colors,
            opacity=0.6,
        ).update_layout(
            showlegend=False,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
        )

        bardf = dframe.groupby("identifier").mean().reset_index()
        barfig = create_outcrop_barfig(
            bardf, y="thickness_md", x="identifier", colors=smdamodel.colors
        ).update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin={"l": 100, "r": 20, "t": 20, "b": 20},
        )

        return html.Div(
            children=[
                wcc.FlexBox(
                    style={"height": "50vh"},
                    children=[
                        wcc.FlexColumn(
                            flex=1,
                            children=html.Div(
                                [
                                    wcc.Graph(
                                        config={"displayModeBar": False},
                                        style={"height": "48vh"},
                                        figure=scatter,
                                    )
                                ]
                            ),
                        ),
                        wcc.FlexColumn(
                            flex=2,
                            children=wcc.Graph(
                                config={"displayModeBar": False},
                                style={"height": "48vh"},
                                figure=barfig,
                            ),
                        ),
                    ],
                ),
                make_table(
                    dframe,
                    selections["table_responses"],
                    tab="smda",
                    table_type=selections["Table type"],
                    groups=selections["Group by"],
                    height="80vh",
                    selectors=smdamodel.selectors,
                ),
            ]
        )


def create_outcrop_barfig(dframe, y, x, colors):
    return create_figure(
        plot_type="bar",
        data_frame=dframe,
        x=x,
        y=y,
        color=x,
        color_discrete_map=colors,
        barmode="overlay",
        xaxis=dict(showticklabels=False),
    ).update_layout(margin={"l": 20, "r": 20, "t": 20, "b": 20}, showlegend=False)
