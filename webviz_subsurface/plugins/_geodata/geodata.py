from typing import List, Tuple, Callable, Optional
from pathlib import Path

import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype
from dash import html, Dash, Input, Output, State, ALL, dash_table, no_update
import plotly.express as px
import webviz_core_components as wcc
from webviz_config import WebvizPluginABC
from webviz_config import WebvizSettings
from webviz_config.webviz_store import webvizstore
from webviz_config.common_cache import CACHE
from webviz_subsurface._figures import create_figure
from .main_view import main_view
from .varviz_callback import varviz_callback


class GeoData(WebvizPluginABC):
    def __init__(
        self,
        app: Dash,
        webviz_settings: WebvizSettings,
        csvfile_channel: Path = None,
        csvfile_variogram: Path = None,
    ):

        super().__init__()

        self.csvfile_channel = read_csv(csvfile_channel) if csvfile_channel else None
        self.csvfile_variogram = (
            read_csv(csvfile_variogram) if csvfile_variogram else None
        )
        self.csvfile_variogram = self.csvfile_variogram.dropna(how="any")

        self.theme_colors = webviz_settings.theme.plotly_theme.get("layout", {}).get(
            "colorway", []
        )

        self.selectors = ["Delft3D model", "Formation", "Attribute"]

        self.variogram_filters = [
            "Delft3D model",
            "Variogram parameterzation",
            "Quality factor",
            "Attribute",
            "Identifier",
            "Indicator",
            "Crop box number",
        ]
        self.variogram_responses = [
            col
            for col in self.csvfile_variogram
            if col
            not in self.variogram_filters
            + ["cropbox_x0", "cropbox_x1", "cropbox_y0", "cropbox_y1"]
        ]
        self.responses = [
            col
            for col in self.csvfile_channel
            if col not in self.selectors and not col.startswith("cropbox")
        ]
        self.set_callbacks(app)

    @property
    def layout(self) -> html.Div:
        return html.Div(
            children=[
                main_view(
                    get_uuid=self.uuid,
                    responses=self.responses,
                    selectors=self.selectors,
                    channel_dframe=self.csvfile_channel,
                    variogram_dframe=self.csvfile_variogram,
                    variogram_filters=self.variogram_filters,
                    variogram_responses=self.variogram_responses,
                ),
            ],
        )

    def set_callbacks(self, app: Dash) -> None:
        varviz_callback(
            app=app, get_uuid=self.uuid, variogram_df=self.csvfile_variogram
        )

        @app.callback(
            Output(self.uuid("main-table"), "children"),
            Input({"id": self.uuid("selections-table"), "selector": ALL}, "value"),
            Input({"id": self.uuid("selections-table"), "filter": ALL}, "value"),
            State({"id": self.uuid("selections-table"), "selector": ALL}, "id"),
            State({"id": self.uuid("selections-table"), "filter": ALL}, "id"),
        )
        def update_table(
            table_selections: list, table_filters: list, selector_ids, filter_ids
        ) -> list:

            selections = {
                id_value["selector"]: value
                for id_value, value in zip(selector_ids, table_selections)
            }
            filters = {
                id_value["filter"]: value
                for id_value, value in zip(filter_ids, table_filters)
            }

            dframe = self.csvfile_channel
            for filt, values in filters.items():
                dframe = dframe.loc[dframe[filt].isin(values)]

            return make_table(
                dframe,
                selections["table_responses"],
                table_type=selections["Table type"],
                groups=selections["Group by"],
                height="80vh",
                selectors=self.selectors,
            )

        @app.callback(
            Output(self.uuid("main-plots"), "children"),
            Input({"id": self.uuid("selections-plots"), "selector": ALL}, "value"),
            Input({"id": self.uuid("selections-plots"), "filter": ALL}, "value"),
            Input(self.uuid("main-plots-display-option"), "value"),
            State({"id": self.uuid("selections-plots"), "selector": ALL}, "id"),
            State({"id": self.uuid("selections-plots"), "filter": ALL}, "id"),
        )
        def update_plots(
            plot_selections: list,
            plot_filters: list,
            display_option,
            selector_ids,
            filter_ids,
        ) -> list:

            selections = {
                id_value["selector"]: value
                for id_value, value in zip(selector_ids, plot_selections)
            }
            filters = {
                id_value["filter"]: value
                for id_value, value in zip(filter_ids, plot_filters)
            }

            dframe = self.csvfile_channel
            for filt, values in filters.items():
                dframe = dframe.loc[dframe[filt].isin(values)]

            groups = []
            responses = []
            for item in ["Subplots", "Color by", "X Response", "Y Response"]:
                value = selections[item]
                if selections[item] is not None:
                    if value in self.selectors and value not in groups:
                        groups.append(value)

                    if item in ["X Response", "Y Response"] and value not in responses:
                        responses.append(value)

            df_for_figure = dframe

            if display_option != "table":
                if selections["Plot type"] == "bar":
                    groups = list(
                        set(
                            selections[item]
                            for item in [
                                "Subplots",
                                "Color by",
                                "X Response",
                                "Y Response",
                            ]
                            if selections[item] is not None
                            and selections[item] in self.selectors
                        )
                    )
                    if groups:
                        df_for_figure = (
                            df_for_figure.groupby(groups).mean().reset_index()
                        )

                figure = create_figure(
                    plot_type=selections["Plot type"],
                    data_frame=df_for_figure,
                    x=selections["X Response"],
                    y=selections["Y Response"],
                    facet_col=selections["Subplots"],
                    color=selections["Color by"],
                    color_discrete_sequence=px.colors.qualitative.Dark2,
                    color_continuous_scale=px.colors.sequential.Viridis,
                    opacity=0.9,
                    layout=dict(
                        title=dict(
                            text=selections["X Response"],
                            x=0.5,
                            xref="paper",
                            font=dict(size=18),
                        ),
                        bargap=0.1,
                    ),
                    yaxis=dict(
                        showticklabels=True, tickfont_size=18, title_font_size=15
                    ),
                    xaxis=dict(tickfont_size=18, title_font_size=15),
                )

                if selections["X Response"] in self.selectors:
                    figure.update_xaxes(
                        dict(type="category", tickangle=45, tickfont_size=14)
                    )

                # if selections["Subplots"] is not None:
                #     if not selections["X axis matches"]:
                #         figure.update_xaxes({"matches": None})
                #     if not selections["Y axis matches"]:
                #         figure.update_yaxes({"matches": None})

                children = [
                    wcc.Graph(
                        config={"displayModeBar": False},
                        style={
                            "height": "80vh" if display_option == "plot" else "50vh"
                        },
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
                            height="30vh",
                            selectors=self.selectors,
                        )
                    )
                return html.Div(children)

            return make_table(
                dframe,
                responses,
                table_type="Statistics table",
                groups=groups,
                height="80vh",
                selectors=self.selectors,
            )

        @app.callback(
            Output({"id": self.uuid("selections-plots"), "selector": ALL}, "disabled"),
            Output({"id": self.uuid("selections-plots"), "selector": ALL}, "value"),
            Output({"id": self.uuid("selections-plots"), "selector": ALL}, "options"),
            Input(
                {"id": self.uuid("selections-plots"), "selector": "Plot type"}, "value"
            ),
            Input(
                {"id": self.uuid("selections-plots"), "selector": "Color by"}, "value"
            ),
            State({"id": self.uuid("selections-plots"), "selector": ALL}, "value"),
            State({"id": self.uuid("selections-plots"), "selector": ALL}, "id"),
        )
        def _plot_options(
            plot_type: str,
            selected_color_by,
            selector_values: list,
            selector_ids: list,
        ) -> tuple:

            selections = {
                id_value["selector"]: values
                for id_value, values in zip(selector_ids, selector_values)
            }

            settings = {
                selector: {"disable": False, "value": selections[selector]}
                for selector in ["Y Response", "Color by", "X Response"]
            }

            if plot_type in ["distribution", "histogram"]:
                settings["Y Response"] = {"disable": True, "value": None}

            # update dropdown options based on plot type
            if plot_type == "scatter":
                y_elm = x_elm = self.responses + self.selectors
            elif plot_type in ["box", "bar"]:
                y_elm = x_elm = self.selectors + self.responses
                if selections.get("Y Response") is None:
                    settings["Y Response"]["value"] = selected_color_by
            else:
                y_elm = self.selectors
                x_elm = self.responses

            colorby_elm = y_elm if plot_type == "scatter" else self.selectors
            settings["Y Response"]["options"] = [
                {"label": elm, "value": elm} for elm in y_elm
            ]
            settings["X Response"]["options"] = [
                {"label": elm, "value": elm} for elm in x_elm
            ]
            settings["Color by"]["options"] = [
                {"label": elm, "value": elm} for elm in colorby_elm
            ]

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


def make_table(
    dframe: pd.DataFrame,
    responses: list,
    table_type: str,
    selectors: list,
    height,
    groups: Optional[list] = None,
) -> html.Div:

    groups = groups if groups is not None else []

    if table_type == "Statistics table":
        statcols = ["Mean", "Stddev", "P90", "P10", "Minimum", "Maximum"]
        df_groups = dframe.groupby(groups) if groups else [(None, dframe)]

        data_list = []
        for response in responses:
            if not is_numeric_dtype(dframe[response]):
                continue
            for name, df in df_groups:
                values = df[response]
                data = {
                    "Response": response,
                    "Mean": values.mean(),
                    "Stddev": values.std(),
                    "P10": np.nanpercentile(values, 90),
                    "P90": np.nanpercentile(values, 10),
                    "Minimum": values.min(),
                    "Maximum": values.max(),
                }

                for idx, group in enumerate(groups):
                    data[group] = (
                        name if not isinstance(name, tuple) else list(name)[idx]
                    )
                data_list.append(data)

        return create_dash_table(
            columns=[
                {
                    "id": col,
                    "name": col,
                    "type": "numeric",
                    "format": {"specifier": ".1f"},
                }
                for col in ["Response"] + groups + statcols
            ],
            data=data_list,
            selectors=selectors,
            height=height,
        )

    # if table type Mean table
    dframe = (
        dframe[responses + groups].groupby(groups).mean().reset_index()
        if groups
        else dframe[responses].mean().to_frame().T
    )

    return create_dash_table(
        columns=[
            {
                "id": col,
                "name": col,
                "type": "numeric",
                "format": {"specifier": ".1f"},
            }
            for col in dframe
        ],
        data=dframe.iloc[::-1].to_dict("records"),
        selectors=selectors,
        height=height,
    )


def create_dash_table(columns, data, selectors, height):
    style_cell_conditional = [
        {
            "if": {"column_id": selectors + ["Response"]},
            "textAlign": "left",
            "width": "15%",
        }
    ]
    return html.Div(
        style={"margin-top": "20px"},
        children=dash_table.DataTable(
            sort_action="native",
            sort_mode="multi",
            filter_action="native",
            columns=columns,
            data=data,
            style_cell_conditional=style_cell_conditional,
            style_table={
                "height": height,
                "overflowY": "auto",
            },
        ),
    )


def update_relevant_components(id_list: list, update_info: List[dict]) -> list:
    output_id_list = [no_update] * len(id_list)
    for elm in update_info:
        for idx, x in enumerate(id_list):
            if all(x[key] == value for key, value in elm["conditions"].items()):
                output_id_list[idx] = elm["new_value"]
                break
    return output_id_list


@CACHE.memoize(timeout=CACHE.TIMEOUT)
@webvizstore
def read_csv(csv_file: Path) -> pd.DataFrame:
    return pd.read_csv(csv_file)
