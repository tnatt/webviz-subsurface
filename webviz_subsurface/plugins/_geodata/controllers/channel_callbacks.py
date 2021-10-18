from typing import Callable
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
import plotly.express as px
from dash import html, Input, Output, State, ALL, no_update, callback
from dash.exceptions import PreventUpdate
import webviz_core_components as wcc

from webviz_subsurface._figures import create_figure
from ..utils import make_table, update_relevant_components


def channel_callback(
    get_uuid: Callable,
    channels_df: pd.DataFrame,
    selectors: list,
    responses: list,
    amodel=None,
):
    @callback(
        Output(get_uuid("main-plots"), "children"),
        Input({"id": get_uuid("ui"), "tab": "plots", "selector": ALL}, "value"),
        Input({"id": get_uuid("ui"), "tab": "plots", "filter": ALL}, "value"),
        Input({"id": get_uuid("ui"), "tab": "plots", "afilter": ALL}, "value"),
        Input(get_uuid("main-plots-display-option"), "value"),
        Input(get_uuid("tabs"), "value"),
        State({"id": get_uuid("ui"), "tab": "plots", "selector": ALL}, "id"),
        State({"id": get_uuid("ui"), "tab": "plots", "filter": ALL}, "id"),
        State({"id": get_uuid("ui"), "tab": "plots", "afilter": ALL}, "id"),
    )
    def update_plots(
        plot_selectors: list,
        filters: list,
        afilters,
        display_option,
        selected_tab,
        selector_ids,
        filter_ids,
        afilter_ids,
    ) -> list:

        if selected_tab != "plots":
            raise PreventUpdate

        cfg = {
            id_value["selector"]: value
            for id_value, value in zip(selector_ids, plot_selectors)
        }
        filters = {
            id_value["filter"]: value for id_value, value in zip(filter_ids, filters)
        }
        afilters = {
            id_value["afilter"]: value for id_value, value in zip(afilter_ids, afilters)
        }

        dframe = channels_df
        for filt, values in filters.items():
            dframe = dframe.loc[dframe[filt].isin(values)]

        if cfg["Analogue data"]:
            a_dframe = amodel.dframe.copy()
            for filt, values in afilters.items():
                a_dframe = a_dframe.loc[a_dframe[filt].isin(values)]

            dframe = pd.concat([dframe, a_dframe])
            if cfg["Analogue color"] is not None:
                mask = dframe["Data source"] == "Analogue"
                dframe["Data source"].loc[mask] = dframe["Outcrop"].loc[mask]
            cfg["color"] = "Data source"

        groups = []
        responses = []
        for item in ["facet_col", "color", "x", "y"]:
            value = cfg[item]
            if cfg[item] is not None:
                if value in selectors and value not in groups:
                    groups.append(value)

                if item in ["x", "y"] and value not in responses:
                    responses.append(value)

        df_for_figure = (
            dframe.groupby(groups).mean().reset_index()
            if cfg["plot_type"] == "bar" and groups
            else dframe
        )

        numeric_x = is_numeric_dtype(dframe[cfg["x"]])
        numeric_y = cfg["y"] is not None and is_numeric_dtype(dframe[cfg["y"]])

        plot_options = ["plot_type", "x", "y", "facet_col", "color", "nbins", "barmode"]
        figure = create_figure(
            **{key: value for key, value in cfg.items() if key in plot_options},
            data_frame=df_for_figure,
            color_discrete_map=amodel.colors if cfg["Analogue data"] else None,
            color_discrete_sequence=px.colors.qualitative.Dark2,
            color_continuous_scale=px.colors.sequential.Viridis,
            opacity=0.7,
            layout={
                "title": {"text": cfg["x"], "x": 0.5, "xref": "paper", "font_size": 18},
                "bargap": 0.1,
            },
            trendline=cfg["trendline"] if all([numeric_x, numeric_y]) else None,
            yaxis=dict(showticklabels=True, tickfont_size=18, title_font_size=15),
            xaxis=dict(tickfont_size=18, title_font_size=15),
        )

        if cfg["x"] in selectors:
            figure.update_xaxes(dict(type="category", tickangle=45, tickfont_size=14))

        if cfg["facet_col"] is not None:
            if not cfg["X axis matches"]:
                figure.update_xaxes({"matches": None})
            if not cfg["Y axis matches"]:
                figure.update_yaxes({"matches": None})
        else:
            if cfg["statlines"] is not None:
                figure = add_histogram_lines(figure, cfg)

        children = [
            wcc.Graph(
                config={"displayModeBar": False},
                style={"height": "80vh" if display_option == "plot" else "50vh"},
                figure=figure,
            )
        ]
        if display_option == "plot_with_table":
            children.append(
                make_table(
                    dframe,
                    responses,
                    table_type="Statistics table",
                    groups=groups,
                    height="35vh",
                    selectors=selectors,
                    tab="plots",
                    style_data_conditional=[
                        {
                            "if": {"filter_query": "{Data source} = 'Digital Models'"},
                            "backgroundColor": "rgb(230, 230, 230)",
                            "fontWeight": "bold",
                        },
                    ],
                )
            )

        return html.Div(children)

    @callback(
        Output({"id": get_uuid("ui"), "tab": "plots", "selector": ALL}, "disabled"),
        Output({"id": get_uuid("ui"), "tab": "plots", "selector": ALL}, "value"),
        Output({"id": get_uuid("ui"), "tab": "plots", "selector": ALL}, "options"),
        Input({"id": get_uuid("ui"), "tab": "plots", "selector": "plot_type"}, "value"),
        Input({"id": get_uuid("ui"), "tab": "plots", "selector": "color"}, "value"),
        Input(
            {"id": get_uuid("ui"), "tab": "plots", "selector": "Analogue data"}, "value"
        ),
        State({"id": get_uuid("ui"), "tab": "plots", "selector": ALL}, "value"),
        State({"id": get_uuid("ui"), "tab": "plots", "selector": ALL}, "id"),
    )
    def _plot_options(
        plot_type: str,
        selected_color_by,
        analogue_data: list,
        selector_values: list,
        selector_ids: list,
    ) -> tuple:

        cfg = {
            id_value["selector"]: values
            for id_value, values in zip(selector_ids, selector_values)
        }
        settings = {
            selector: {"disable": False, "value": cfg[selector]}
            for selector in ["y", "x", "trendline", "color", "facet_col"]
        }

        if plot_type in ["distribution", "histogram"]:
            settings["y"] = {"disable": True, "value": None}

        # update dropdown options based on plot type
        if plot_type == "scatter":
            y_elm = x_elm = responses + selectors
        elif plot_type in ["box", "bar"]:
            y_elm = x_elm = selectors + responses
            if cfg.get("y") is None:
                settings["y"]["value"] = selected_color_by
        else:
            y_elm = selectors
            x_elm = responses

        settings["y"]["options"] = [{"label": elm, "value": elm} for elm in y_elm]
        settings["x"]["options"] = [{"label": elm, "value": elm} for elm in x_elm]
        settings["facet_col"]["options"] = [
            {"label": elm, "value": elm} for elm in selectors
        ]

        settings["trendline"]["disable"] = plot_type != "scatter"

        if analogue_data:
            settings["color"] = {"disable": True, "value": "Data source"}
            settings["facet_col"] = {
                "options": [{"label": "Data source", "value": "Data source"}],
            }

        return tuple(
            update_relevant_components(
                id_list=selector_ids,
                update_info=[
                    {
                        "new_value": values.get(prop, no_update),
                        "conditions": {"selector": selector},
                    }
                    for selector, values in settings.items()
                ],
            )
            for prop in ["disable", "value", "options"]
        )

    @callback(
        Output(
            {"id": get_uuid("ui"), "tab": "plots", "element": "afilter_wrapper"},
            "style",
        ),
        Input(
            {"id": get_uuid("ui"), "tab": "plots", "selector": "Analogue data"}, "value"
        ),
    )
    def _show_hide_analogue_filters(analogue_data: list) -> list:
        return {"display": "block" if analogue_data else "none"}


def add_histogram_lines(figure, cfg):

    for trace in figure.data:
        if trace.type != "histogram":
            continue
        mean = trace.x.mean()
        p10 = np.nanpercentile(trace.x, 90)
        p90 = np.nanpercentile(trace.x, 10)

        figure.add_vline(
            x=mean,
            annotation_text=f"<b>Mean:</b> {mean:.1f}",
            annotation={"font_size": 15, "bgcolor": "white"},
            line_width=4,
            line_color=trace.marker.color,
        )
        if cfg["statlines"] == "all":
            figure.add_vline(
                x=p10,
                annotation_text=f"<b>P10:</b> {p10:.1f}",
                annotation={"font_size": 15, "bgcolor": "white"},
                line_width=3,
                line_dash="dash",
                line_color=trace.marker.color,
            )
            figure.add_vline(
                x=p90,
                annotation_text=f"<b>P90:</b> {p90:.1f}",
                annotation={"font_size": 15, "bgcolor": "white"},
                line_width=3,
                line_dash="dash",
                line_color=trace.marker.color,
            )
    return figure
