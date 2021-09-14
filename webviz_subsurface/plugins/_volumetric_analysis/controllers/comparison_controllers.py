from typing import Callable, Union, Optional

import numpy as np
import pandas as pd
import dash
import dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from webviz_subsurface._models import InplaceVolumesModel

from webviz_subsurface._figures import create_figure
from ..views.comparison_layout import (
    comparison_qc_plots_layout,
    comparison_table_layout,
)
from ..utils.table_and_figure_utils import (
    add_correlation_line,
    create_table_columns,
    create_data_table,
)
from ..utils.utils import move_to_end_of_list


def comparison_controllers(
    app: dash.Dash,
    get_uuid: Callable,
    volumemodel: InplaceVolumesModel,
) -> None:
    @app.callback(
        Output({"id": get_uuid("main-src-comp"), "wrapper": "table"}, "children"),
        Input(get_uuid("selections"), "data"),
        Input({"id": get_uuid("main-src-comp"), "element": "display-option"}, "value"),
        State(
            {"id": get_uuid("selections"), "tab": "src-comp", "selector": "Response"},
            "options",
        ),
        State(get_uuid("page-selected"), "data"),
    )
    def _update_page_src_comp(
        selections: dict,
        display_option: str,
        response_options: list,
        page_selected: str,
    ) -> html.Div:
        ctx = dash.callback_context.triggered[0]

        if page_selected != "src-comp":
            raise PreventUpdate

        selections = selections[page_selected]
        if not "display-option" in ctx["prop_id"]:
            if not selections["update"]:
                raise PreventUpdate

        return comparison_callback(
            compare_on="SOURCE",
            volumemodel=volumemodel,
            selections=selections,
            display_option=display_option,
            response_options=response_options,
        )

    @app.callback(
        Output({"id": get_uuid("main-ens-comp"), "wrapper": "table"}, "children"),
        Input(get_uuid("selections"), "data"),
        Input({"id": get_uuid("main-ens-comp"), "element": "display-option"}, "value"),
        State(
            {"id": get_uuid("selections"), "tab": "ens-comp", "selector": "Response"},
            "options",
        ),
        State(get_uuid("page-selected"), "data"),
    )
    def _update_page_ens_comp(
        selections: dict,
        display_option: str,
        response_options: list,
        page_selected: str,
    ) -> html.Div:
        ctx = dash.callback_context.triggered[0]

        if page_selected != "ens-comp":
            raise PreventUpdate

        selections = selections[page_selected]
        if not "display-option" in ctx["prop_id"]:
            if not selections["update"]:
                raise PreventUpdate

        return comparison_callback(
            compare_on="ENSEMBLE",
            volumemodel=volumemodel,
            selections=selections,
            display_option=display_option,
            response_options=response_options,
        )


def comparison_callback(
    compare_on: str,
    volumemodel: InplaceVolumesModel,
    selections: dict,
    display_option: str,
    response_options: list,
) -> html.Div:
    if selections["value1"] == selections["value2"]:
        return html.Div("Comparison between equal sources")

    groupby = selections["Group by"] if selections["Group by"] is not None else []
    if "FLUID_ZONE" not in groupby:
        groupby.append("FLUID_ZONE")

    do_not_compare_on = "SOURCE" if compare_on != "SOURCE" else "ENSEMBLE"
    groups = ["REAL", compare_on]
    for selector in groupby:
        if selector not in groups:
            groups.append(selector)

    if display_option == "info table":
        drop_responses = ["STOIIP", "GIIP", "ASSOCIATEDGAS", "ASSOCIATEDOIL"]
        responses = [selections["Response"]] + [
            x["value"]
            for x in response_options
            if x["value"] not in drop_responses and x["value"] != selections["Response"]
        ]

        df = create_comparison_df(
            volumemodel,
            on_col=compare_on,
            selections=selections,
            responses=responses,
            abssort_on=f"{selections['Response']} diff (%)",
            groups=groupby + [compare_on],
        )

        return comparison_table_layout(
            table=create_comaprison_table(
                display_option,
                df,
                groupby,
                selections,
                compare_on,
                volumemodel=volumemodel,
            ),
            table_type=display_option,
            selections=selections,
            filter_info=do_not_compare_on,
        )

    diffdf_real = create_comparison_df(
        volumemodel,
        on_col=compare_on,
        selections=selections,
        responses=[selections["Response"]],
        groups=groups,
        rename_diff_col=True,
    )

    if "REAL" not in groupby:
        diffdf_group = create_comparison_df(
            volumemodel,
            on_col=compare_on,
            selections=selections,
            responses=[selections["Response"]],
            groups=[x for x in groups if x != "REAL"],
            rename_diff_col=True,
        )
        # Add column with number of accepted realizations
        diffdf_group["# reals 💡"] = diffdf_group.apply(
            lambda row: find_higlighted_real_count(row, diffdf_real, groupby), axis=1
        )

    df = diffdf_group if "REAL" not in groupby else diffdf_real
    if df.empty:
        return html.Div("Only data with no volume present!")

    if display_option == "table":
        return comparison_table_layout(
            table=create_comaprison_table(
                tabletype=display_option,
                df=df,
                groupby=groupby,
                selections=selections,
                use_si_format=selections["Response"] in volumemodel.volume_columns,
                compare_on=compare_on,
            ),
            table_type=display_option,
            selections=selections,
            filter_info=do_not_compare_on,
        )

    if display_option == "plots":
        resp1 = f"{selections['Response']} {selections['value1']}"
        resp2 = f"{selections['Response']} {selections['value2']}"

        scatter_corr = create_scatterfig(
            df=df, x=resp1, y=resp2, selections=selections, groupby=groupby
        )
        scatter_corr = add_correlation_line(
            figure=scatter_corr, xy_min=df[resp1].min(), xy_max=df[resp1].max()
        )
        scatter_diff_vs_response = create_scatterfig(
            df=df,
            x=resp1,
            y=selections["Diff mode"],
            selections=selections,
            groupby=groupby,
            diff_mode=selections["Diff mode"],
        )
        scatter_diff_vs_real = create_scatterfig(
            df=diffdf_real,
            x="REAL",
            y=selections["Diff mode"],
            selections=selections,
            groupby=groupby,
            diff_mode=selections["Diff mode"],
        )
        barfig_non_accepted = create_barfig(
            df=df[df["highlighted"] == "yes"],
            groupby=groupby,
            diff_mode=selections["Diff mode"],
            colorcol=resp1,
        )

    return comparison_qc_plots_layout(
        scatter_diff_vs_real,
        scatter_corr,
        scatter_diff_vs_response,
        barfig_non_accepted,
    )


def create_comparison_df(
    volumemodel: InplaceVolumesModel,
    on_col: str,
    responses: list,
    selections: dict,
    groups: list,
    abssort_on: str = "diff (%)",
    rename_diff_col: bool = False,
) -> pd.DataFrame:

    value1, value2 = selections["value1"], selections["value2"]
    resp = selections["Response"]

    selections["filters"][on_col] = [value1, value2]
    dframe = volumemodel.get_df(selections["filters"], groups)

    groupby = [x for x in groups if x != on_col]
    df = dframe.loc[:, [on_col] + groupby + responses].pivot_table(
        columns=on_col, index=groupby
    )
    responses = [col for col in responses if col in df]
    for col in responses:
        df[col, "diff"] = df[col][value2] - df[col][value1]
        df[col, "diff (%)"] = ((df[col][value2] / df[col][value1]) - 1) * 100
        df.loc[df[col]["diff"] == 0, (col, "diff (%)")] = 0
    df = df.replace([np.inf, -np.inf], np.nan)
    dframe = df[responses].reset_index()

    if selections["Remove zeros"]:
        dframe = dframe.loc[
            ~((dframe[resp]["diff"] == 0) & (dframe[resp][value1] == 0))
        ]

    dframe["highlighted"] = _compute_accepted_col(dframe, resp, value1, selections)
    dframe.columns = dframe.columns.map(" ".join).str.strip(" ")
    if rename_diff_col:
        dframe = dframe.rename(
            columns={f"{resp} diff": "diff", f"{resp} diff (%)": "diff (%)"}
        )
    return dframe.sort_values(by=[abssort_on], key=abs, ascending=False)


def _compute_accepted_col(
    df: pd.DataFrame, response: str, value1: str, selections: dict
) -> list:
    accept_mask = (df[response][value1] > selections["Ignore value"]) & (
        df[response]["diff (%)"].abs() < selections["Accept value"]
    ) | (df[response][value1] <= selections["Ignore value"])
    return np.where(accept_mask, "no", "yes")


def find_higlighted_real_count(
    row: pd.Series, df_per_real: pd.DataFrame, groups: list
) -> str:
    query = " & ".join([f"{col}=='{row[col]}'" for col in groups])
    result = df_per_real.query(query)
    return str(len(result[result["highlighted"] == "yes"]))


def create_comaprison_table(
    tabletype: str,
    df: pd.DataFrame,
    groupby: list,
    selections: dict,
    compare_on: str,
    use_si_format: Optional[bool] = None,
    volumemodel: Optional[InplaceVolumesModel] = None,
) -> dash_table.DataTable:

    diff_mode_percent = selections["Diff mode"] == "diff (%)"

    if selections["Remove accepted"]:
        df = df.loc[df["highlighted"] == "yes"]
        if df.empty:
            return html.Div(
                [
                    html.Div("All data outside highlight criteria!"),
                    html.Div(
                        "To see the data turn off setting 'Display only highlighted data'"
                    ),
                ]
            )

    if tabletype == "info table":
        diff_cols = [x for x in df.columns if selections["Diff mode"] in x]
        if not diff_mode_percent:
            diff_cols = [x for x in diff_cols if not "(%)" in x]
        rename_dict = {x: x.split(f" {selections['Diff mode']}")[0] for x in diff_cols}
        df = df[groupby + diff_cols + ["highlighted"]].rename(columns=rename_dict)

        columns = create_table_columns(
            columns=move_to_end_of_list("FLUID_ZONE", df.columns),
            no_format=groupby,
            use_si_format=volumemodel.volume_columns if not diff_mode_percent else None,
            use_percentage=list(df.columns) if diff_mode_percent else None,
        )
    else:
        columns = create_table_columns(
            columns=move_to_end_of_list("FLUID_ZONE", df.columns),
            no_format=groupby,
            use_si_format=list(df.columns) if use_si_format else None,
            use_percentage=["diff (%)"],
        )

    return create_data_table(
        selectors=groupby,
        columns=columns,
        height="80vh",
        data=df.to_dict("records"),
        table_id={"table_id": f"{compare_on}-comp-table"},
        style_cell={"textAlign": "center"},
        style_data_conditional=[
            {
                "if": {"filter_query": "{highlighted} = 'yes'"},
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
        ],
        style_cell_conditional=[
            {"if": {"column_id": "highlighted"}, "display": "None"}
        ],
    )


def create_scatterfig(
    df: pd.DataFrame,
    x: str,
    y: str,
    selections: dict,
    groupby: list,
    diff_mode: Optional[str] = None,
) -> go.Figure:
    colorby = selections["Color by"]
    if colorby != "highlighted":
        colorby = groupby[0] if groupby else None
    color_map = {"yes": "#FF1243", "no": "#80B7BC"}
    fig = (
        create_figure(
            plot_type="scatter",
            data_frame=df,
            x=x,
            y=y,
            # size=colorby,
            color_discrete_sequence=px.colors.qualitative.Dark2,
            color_discrete_map=color_map if colorby == "highlighted" else None,
            color=colorby,
            hover_data={col: True for col in groupby},
        )
        .update_traces(marker_size=10)
        .update_layout(margin={"l": 20, "r": 20, "t": 20, "b": 20})
    )
    if diff_mode is not None:
        fig.update_yaxes(range=find_diff_plot_range(df, diff_mode, selections))
        if diff_mode == "diff (%)" and x == "REAL":
            fig.add_hline(y=selections["Accept value"], line_dash="dot").add_hline(
                y=-selections["Accept value"], line_dash="dot"
            )
    return fig


def find_diff_plot_range(df: pd.DataFrame, diff_mode: str, selections: dict) -> list:
    """
    Find plot range for diff axis. If axis focus is selected
    the range will center around the non-acepted data points.
    An 10% extension is added to the axis
    """
    if selections["Axis focus"] and "yes" in df["highlighted"].values:
        df = df[df["highlighted"] == "yes"]

    low = min(df[diff_mode].min(), -selections["Accept value"])
    high = max(df[diff_mode].max(), selections["Accept value"])
    extend = (high - low) * 0.1
    return [low - extend, high + extend]


def create_barfig(
    df: pd.DataFrame, groupby: list, diff_mode: str, colorcol: str
) -> Union[None, go.Figure]:
    if df.empty:
        return None
    return (
        create_figure(
            plot_type="bar",
            data_frame=df,
            x=df[[x for x in groupby if x != "FLUID_ZONE"]]
            .astype(str)
            .agg(" ".join, axis=1),
            y=diff_mode,
            color_continuous_scale="teal_r",
            color=df[colorcol],
            hover_data={col: True for col in groupby},
            opacity=1,
        )
        .update_layout(
            margin={"l": 20, "r": 20, "t": 5, "b": 5},
            bargap=0.15,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        .update_xaxes(title_text=None, tickangle=45, ticks="outside")
        .update_yaxes(zeroline=True, zerolinecolor="black")
    )
