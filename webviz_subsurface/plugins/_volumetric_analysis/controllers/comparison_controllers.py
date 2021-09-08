from typing import Callable

import numpy as np
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html
import plotly.express as px
from webviz_subsurface._models import InplaceVolumesModel

from webviz_subsurface._figures import create_figure
from ..views.src_comparison_layout import (
    src_comp_qc_plots_layout,
    src_comp_table_layout,
)
from ..utils.figure_utils import add_correlation_line
from ..utils.table_utils import create_table_columns, create_data_table
from ..utils.utils import move_to_end_of_list, move_to_start_of_list


def comparison_controllers(
    app: dash.Dash,
    get_uuid: Callable,
    volumemodel: InplaceVolumesModel,
    disjoint_set_df=None,
) -> None:
    @app.callback(
        Output(
            {"id": get_uuid("main-src-comp"), "wrapper": "table"},
            "children",
        ),
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

        return main_callback(
            compare_on="SOURCE",
            volumemodel=volumemodel,
            selections=selections,
            display_option=display_option,
            response_options=response_options,
        )

    @app.callback(
        Output(
            {"id": get_uuid("main-ens-comp"), "wrapper": "table"},
            "children",
        ),
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

        return main_callback(
            compare_on="ENSEMBLE",
            volumemodel=volumemodel,
            selections=selections,
            display_option=display_option,
            response_options=response_options,
        )


def main_callback(
    compare_on, volumemodel, selections, display_option, response_options
):
    if selections["value1"] == selections["value2"]:
        return html.Div("Comparison between equal sources")

    groupby = selections["Group by"] if selections["Group by"] is not None else []
    if "FLUID_ZONE" not in groupby:
        groupby.append("FLUID_ZONE")

    test = "SOURCE" if compare_on != "SOURCE" else "ENSEMBLE"
    groups = ["REAL", compare_on]
    for selector in groupby:
        if selector not in groups:
            groups.append(selector)

    if display_option == "info table":
        response_options = [x["value"] for x in response_options]
        responses = move_to_start_of_list(selections["Response"], response_options)

        df = create_comparison_df(
            volumemodel,
            on_col=compare_on,
            selections=selections,
            responses=responses,
            abssort_on=f"{selections['Response']} diff (%)",
            groups=groupby + [compare_on],
        )
        return src_comp_table_layout(
            table=create_comaprison_table(
                display_option, df, groupby, selections, compare_on
            ),
            table_type=display_option,
            selections=selections,
            filter_info=test,
        )

    diffdf_real = create_comparison_df(
        volumemodel,
        on_col=compare_on,
        selections=selections,
        responses=[selections["Response"]],
        groups=groups,
        abssort_on="diff (%)",
        rename_diff_col=True,
    )

    if "REAL" not in groupby:
        diffdf_group = create_comparison_df(
            volumemodel,
            on_col=compare_on,
            selections=selections,
            responses=[selections["Response"]],
            groups=[x for x in groups if x != "REAL"],
            abssort_on=selections["Diff mode"],
            rename_diff_col=True,
        )
        diffdf_group["# reals ❌"] = add_accepted_real_count(
            diffdf_group, diffdf_real, groupby
        )

    df = diffdf_group if "REAL" not in groupby else diffdf_real
    if df.empty:
        return html.Div("Only data with no volume present!")

    if display_option == "table":
        return src_comp_table_layout(
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
            filter_info=test,
        )

    if display_option == "plots":
        resp1 = f"{selections['Response']} {selections['value1']}"
        resp2 = f"{selections['Response']} {selections['value2']}"

        scatter_corr = create_scatterfig(
            df=df, x=resp1, y=resp2, selections=selections, groupby=groupby
        )
        scatter_corr = add_correlation_line(
            figure=scatter_corr,
            xy_min=min(df[resp1].min(), df[resp2].min()),
            xy_max=max(df[resp1].max(), df[resp2].max()),
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
            df=df[df["accepted"] == "no"],
            groupby=groupby,
            diff_mode=selections["Diff mode"],
        )

    return src_comp_qc_plots_layout(
        scatter_diff_vs_real,
        scatter_corr,
        scatter_diff_vs_response,
        barfig_non_accepted,
    )


def create_comparison_df(
    volumemodel,
    on_col: str,
    responses: list,
    selections: dict,
    groups: list,
    abssort_on: str,
    rename_diff_col: bool = False,
):

    dframe = create_response_diff_df(
        volumemodel,
        on_col=on_col,
        value1=selections["value1"],
        value2=selections["value2"],
        responses=responses,
        filters=selections["filters"],
        groups=groups,
    )

    resp = selections["Response"]
    if selections["Remove zeros"]:
        dframe = dframe.loc[
            ~((dframe[resp]["diff"] == 0) & (dframe[resp][selections["value1"]] == 0))
        ]

    dframe["accepted"] = _compute_accepted_col(
        dframe, resp, selections["value1"], selections
    )
    dframe.columns = dframe.columns.map(" ".join).str.strip(" ")
    if rename_diff_col:
        dframe = dframe.rename(
            columns={f"{resp} diff": "diff", f"{resp} diff (%)": "diff (%)"}
        )
    return dframe.sort_values(by=[abssort_on], key=abs, ascending=False)


def create_response_diff_df(
    volumemodel,
    on_col: str,
    value1: str,
    value2: str,
    responses: list,
    filters: dict,
    groups: list,
):

    filters[on_col] = [value1, value2]
    dframe = volumemodel.get_df(filters, groups)
    groupby = [x for x in groups if x != on_col]
    df = dframe.loc[:, [on_col] + groupby + responses].pivot_table(
        columns=on_col, index=groupby
    )
    responses = [col for col in responses if col in df]
    for resp in responses:
        df[resp, "diff"] = df[resp][value2] - df[resp][value1]
        df[resp, "diff (%)"] = ((df[resp][value2] / df[resp][value1]) - 1) * 100
        df.loc[df[resp]["diff"] == 0, (resp, "diff (%)")] = 0
    df = df.replace([np.inf, -np.inf], np.nan)
    return df[responses].reset_index()


def _compute_accepted_col(df, response, value1, selections):
    accept_mask = (df[response][value1] > selections["Ignore value"]) & (
        df[response]["diff (%)"].abs() < selections["Accept value"]
    ) | (df[response][value1] <= selections["Ignore value"])

    return np.where(accept_mask, "yes", "no")


def add_accepted_real_count(df, df_real, groups):
    return df.apply(lambda row: find_non_accepted_reals(row, df_real, groups), axis=1)


def find_non_accepted_reals(row, df_per_real, groups):
    query = " & ".join([f"{col}=='{row[col]}'" for col in groups])
    result = df_per_real.query(query)
    return str(len(result[result["accepted"] == "no"]))


def create_comaprison_table(
    tabletype, df, groupby, selections, compare_on, use_si_format=None
):
    df.loc[df["accepted"] == "no", "accepted"] = "❌"
    df.loc[df["accepted"] == "yes", "accepted"] = "✔️"

    if selections["Remove accepted"]:
        df = df.loc[df["accepted"] == "❌"]
        if df.empty:
            return html.Div(
                [
                    html.Div("All data accepted!"),
                    html.Div("To see the data turn off setting 'Remove accepted data'"),
                ]
            )

    if tabletype == "info table":
        diff_cols = [x for x in df.columns if "diff (%)" in x]
        rename_dict = {x: x.split(" diff (%)")[0] for x in diff_cols}
        df = df[groupby + diff_cols + ["accepted"]].rename(columns=rename_dict)
        df = df.drop(
            columns=[
                x
                for x in ["STOIIP", "GIIP", "ASSOCIATEDGAS", "ASSOCIATEDOIL"]
                if x != selections["Response"] and x in df
            ]
        )
        columns = [
            {
                "id": col,
                "name": col,
                "type": "numeric" if col not in groupby else "text",
                "format": {"specifier": ".1f"},
            }
            for col in move_to_end_of_list("FLUID_ZONE", df.columns)
        ]
    else:
        columns = create_table_columns(
            columns=move_to_end_of_list("FLUID_ZONE", df.columns),
            use_si_format=use_si_format,
            format_columns=[col for col in df.columns if col not in groupby],
        )
        for col in columns:
            if "%" in col["id"] and isinstance(col["format"], dict):
                col["format"].update(specifier=".1f")

    return create_data_table(
        selectors=groupby,
        columns=columns,
        height="80vh",
        data=df.to_dict("records"),
        table_id={"table_id": f"{compare_on}-comp-table"},
        style_cell={"textAlign": "center"},
        style_data_conditional=[
            {
                "if": {"filter_query": "{accepted} = '❌'"},
                "color": "#FF1243",
                "fontWeight": "bold",
            },
        ],
        style_cell_conditional=[{"if": {"column_id": "accepted"}, "display": "None"}]
        if tabletype == "info table"
        else None,
        #    disjoint_set_df=disjoint_set_df,
    )


def create_scatterfig(df, x, y, selections, groupby, diff_mode=None):
    colorby = selections["Color by"]
    if colorby != "accepted":
        colorby = groupby[0] if groupby else None
    color_map = {"no": "#FF1243", "yes": "#80B7BC"}
    fig = (
        create_figure(
            plot_type="scatter",
            data_frame=df,
            x=x,
            y=y,
            color_discrete_sequence=px.colors.qualitative.Dark2,
            color_discrete_map=color_map if colorby == "accepted" else None,
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


def find_diff_plot_range(df, diff_mode, selections):
    """
    Find plot range for diff axis. If axis focus is selected
    the range will center around the non-acepted data points.
    An 10% extension is added to the axis
    """
    if selections["Axis focus"] and "no" in df["accepted"].values:
        data = df[df["accepted"] == "no"][diff_mode]
    else:
        data = df[diff_mode]

    low = min(data.min(), -selections["Accept value"])
    high = max(data.max(), selections["Accept value"])
    extend = (high - low) * 0.1
    return [low - extend, high + extend]


def create_barfig(df, groupby, diff_mode):
    if df.empty:
        return None
    return (
        create_figure(
            plot_type="bar",
            data_frame=df,
            x=df[groupby].astype(str).agg(" ".join, axis=1),
            y=diff_mode,
            color_continuous_scale="reds",
            color="diff (%)" if diff_mode == "diff" else "diff",
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
