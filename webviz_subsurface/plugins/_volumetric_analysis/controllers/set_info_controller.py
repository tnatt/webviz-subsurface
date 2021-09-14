from typing import Callable
import dash
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
import webviz_core_components as wcc
from ..utils.table_and_figure_utils import create_table_columns, create_data_table


def set_info_controller(
    app: dash.Dash,
    get_uuid: Callable,
    disjoint_set_df=None,
) -> None:
    @app.callback(
        Output({"id": get_uuid("main-setinfo"), "page": "setinfo"}, "children"),
        Input(get_uuid("selections"), "data"),
        Input(get_uuid("page-selected"), "data"),
        Input({"id": get_uuid("main-setinfo"), "element": "display-option"}, "value"),
    )
    def _update_page_setinfo(
        selections: dict, page_selected: str, display_option: str
    ) -> html.Div:

        if page_selected != "setinfo":
            raise PreventUpdate

        df = disjoint_set_df.copy()
        df = df[["SET", "FIPNUM", "REGION", "ZONE", "REGZONE"]]

        if "setinfo" in selections:
            selections = selections[page_selected]
            if not selections["update"]:
                raise PreventUpdate
            for filt, values in selections["filters"].items():
                df = df.loc[df[filt].isin(values)]

            if selections["Group table"] and display_option == "table":
                df["FIPNUM"] = df["FIPNUM"].astype(str)
                df = df.groupby(["SET"]).agg(lambda x: ", ".join(set(x))).reset_index()

        df = df.sort_values(by=["SET"])

        if display_option == "table":
            return html.Div(
                children=create_data_table(
                    columns=create_table_columns(df.columns),
                    data=df.to_dict("records"),
                    height="85vh",
                    table_id={"table_id": "disjointset-info"},
                    style_cell_conditional=[
                        {"if": {"column_id": "SET"}, "width": "10%"},
                        {"if": {"column_id": ["ZONE", "REGZONE"]}, "width": "30%"},
                        {
                            "if": {"column_id": ["FIPNUM", "REGION"]},
                            "width": "15%",
                        },
                    ],
                    style_cell={
                        "whiteSpace": "normal",
                        "textAlign": "left",
                        "height": "auto",
                    },
                ),
            )

        colors = (
            px.colors.qualitative.Safe
            + px.colors.qualitative.T10
            + px.colors.qualitative.Set1
        )
        df["FIPNUM"] = df["FIPNUM"].astype(str)
        figures = []
        fig_columns = [("ZONE", "REGION"), ("ZONE", "FIPNUM"), ("REGION", "FIPNUM")]
        for y_col, x_col in fig_columns:
            y = df[y_col].unique()
            x = sorted(df[x_col].unique(), key=int if x_col == "FIPNUM" else None)
            data = []
            for zone in y:
                set_list = []
                for reg in x:
                    set_idx = df.loc[(df[y_col] == zone) & (df[x_col] == reg), "SET"]
                    if not set_idx.empty:
                        set_list.append(set_idx.iloc[0])
                    else:
                        set_list.append(None)
                data.append(set_list)

            fig = wcc.Graph(
                config={"displayModeBar": False},
                style={"height": "28vh"},
                figure=go.Figure(
                    data=go.Heatmap(
                        z=data,
                        x=x,
                        y=y,
                        colorscale=colors,
                        showscale=False,
                        hovertemplate="SET: %{z} <br>"
                        + f"{x_col}: %{{x}} <br>"
                        + f"{y_col}: %{{y}} <extra></extra>",
                    )
                )
                .update_layout(margin={"l": 20, "r": 20, "t": 20, "b": 20})
                .update_xaxes(title_text=x_col, tickangle=45, ticks="outside")
                .update_xaxes(
                    showline=True,
                    linewidth=2,
                    linecolor="black",
                    mirror=True,
                )
                .update_yaxes(title_text=y_col)
                .update_yaxes(
                    showline=True,
                    linewidth=2,
                    linecolor="black",
                    mirror=True,
                )
                .update_layout(plot_bgcolor="white"),
            )
            figures.append(fig)

        return html.Div(figures)
