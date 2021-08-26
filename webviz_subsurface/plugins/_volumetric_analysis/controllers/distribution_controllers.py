from typing import Callable, List
import pandas as pd
import numpy as np
import dash
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from webviz_config import WebvizConfigTheme
from webviz_subsurface._components.tornado._tornado_data import TornadoData
from webviz_subsurface._components.tornado._tornado_bar_chart import TornadoBarChart
from webviz_subsurface._components.tornado._tornado_table import TornadoTable
from webviz_subsurface._models import InplaceVolumesModel
from webviz_subsurface._abbreviations.volume_terminology import (
    volume_description,
    volume_unit,
)
from webviz_subsurface._figures import create_figure
from ..views.src_comparison_layout import src_comp_qc_plots_layout
from ..utils.utils import update_relevant_components
from ..utils.figure_utils import fluid_annotation, add_correlation_line
from ..utils.table_utils import (
    make_table_wrapper_children,
    create_table_columns,
    create_data_table,
)

# pylint: disable=too-many-statements, too-many-locals, too-many-branches
def distribution_controllers(
    app: dash.Dash,
    get_uuid: Callable,
    volumemodel: InplaceVolumesModel,
    theme: WebvizConfigTheme,
    disjoint_set_df=None,
) -> None:
    @app.callback(
        Output(
            {"id": get_uuid("main-voldist"), "element": "graph", "page": ALL}, "figure"
        ),
        Output(
            {"id": get_uuid("main-voldist"), "wrapper": "table", "page": ALL},
            "children",
        ),
        Input(get_uuid("selections"), "data"),
        Input(
            {"id": get_uuid("main-voldist"), "element": "plot-table-select"}, "value"
        ),
        State(get_uuid("page-selected"), "data"),
        State({"id": get_uuid("main-voldist"), "element": "graph", "page": ALL}, "id"),
        State({"id": get_uuid("main-voldist"), "wrapper": "table", "page": ALL}, "id"),
    )
    def _update_page_1p1t_and_custom(
        selections: dict,
        plot_table_select: str,
        page_selected: str,
        figure_ids: list,
        table_wrapper_ids: list,
    ) -> tuple:

        if page_selected not in ["1p1t", "custom"]:
            raise PreventUpdate

        selections = selections[page_selected]
        if not selections["update"]:
            raise PreventUpdate

        groups = ["REAL"]
        parameters = []
        responses = []
        for item in ["Subplots", "Color by", "X Response", "Y Response"]:
            if selections[item] is not None:
                if (
                    selections[item] in volumemodel.selectors
                    and selections[item] not in groups
                ):
                    groups.append(selections[item])
                if (
                    selections[item] in volumemodel.parameters
                    and selections[item] not in parameters
                ):
                    parameters.append(selections[item])
                if (
                    item in ["X Response", "Y Response"]
                    and selections[item] not in responses
                ):
                    responses.append(selections[item])

        dframe = volumemodel.get_df(
            filters=selections["filters"], groups=groups, parameters=parameters
        )

        if not (plot_table_select == "table" and page_selected == "custom"):
            df_for_figure = (
                dframe
                if not (selections["Plot type"] == "bar" and groups != ["REAL"])
                else dframe.groupby([x for x in groups if x != "REAL"])
                .mean()
                .reset_index()
            )
            figure = create_figure(
                plot_type=selections["Plot type"],
                data_frame=df_for_figure,
                x=selections["X Response"],
                y=selections["Y Response"],
                nbins=selections["hist_bins"],
                facet_col=selections["Subplots"],
                color=selections["Color by"],
                color_discrete_sequence=selections["Colorscale"],
                color_continuous_scale=selections["Colorscale"],
                barmode=selections["barmode"],
                layout=dict(
                    title=dict(
                        text=(
                            f"{volume_description(selections['X Response'])}"
                            + (
                                f" [{volume_unit(selections['X Response'])}]"
                                if selections["X Response"]
                                in volumemodel.volume_columns
                                else ""
                            )
                        ),
                        x=0.5,
                        xref="paper",
                        font=dict(size=18),
                    ),
                ),
                yaxis=dict(showticklabels=True),
            ).add_annotation(fluid_annotation(selections))

            if selections["X Response"] in volumemodel.selectors:
                figure.update_xaxes(
                    dict(type="category", tickangle=45, tickfont_size=12)
                )

            if selections["Subplots"] is not None:
                if not selections["X axis matches"]:
                    figure.update_xaxes({"matches": None})
                if not selections["Y axis matches"]:
                    figure.update_yaxes({"matches": None})
        else:
            figure = dash.no_update

        # Make tables
        if not (plot_table_select == "graph" and page_selected == "custom"):
            table_wrapper_children = make_table_wrapper_children(
                dframe=dframe,
                responses=responses,
                groups=groups,
                volumemodel=volumemodel,
                page_selected=page_selected,
                selections=selections,
                table_type="Statistics table",
                view_height=42 if page_selected == "1p1t" else 86,
            )
        else:
            table_wrapper_children = dash.no_update

        return tuple(
            update_relevant_components(
                id_list=id_list,
                update_info=[
                    {
                        "new_value": val,
                        "conditions": {"page": page_selected},
                    }
                ],
            )
            for val, id_list in zip(
                [figure, table_wrapper_children], [figure_ids, table_wrapper_ids]
            )
        )

    @app.callback(
        Output(
            {"id": get_uuid("main-table"), "wrapper": "table", "page": "table"},
            "children",
        ),
        Input(get_uuid("selections"), "data"),
        State(get_uuid("page-selected"), "data"),
    )
    def _update_page_tables(
        selections: dict,
        page_selected: str,
    ) -> list:

        if page_selected != "table":
            raise PreventUpdate

        selections = selections[page_selected]
        if not selections["update"]:
            raise PreventUpdate

        table_groups = ["ENSEMBLE", "REAL"]
        if selections["Group by"] is not None:
            table_groups.extend(
                [x for x in selections["Group by"] if x not in table_groups]
            )
        dframe = volumemodel.get_df(
            filters=selections["filters"],
            groups=table_groups,
        )

        return make_table_wrapper_children(
            dframe=dframe,
            responses=selections["table_responses"],
            groups=selections["Group by"],
            view_height=88,
            table_type=selections["Table type"],
            volumemodel=volumemodel,
            page_selected=page_selected,
            selections=selections,
        )

    @app.callback(
        Output(
            {
                "id": get_uuid("main-voldist"),
                "chart": ALL,
                "selector": ALL,
                "page": "per_zr",
            },
            "figure",
        ),
        Input(get_uuid("selections"), "data"),
        State(get_uuid("page-selected"), "data"),
        State(
            {
                "id": get_uuid("main-voldist"),
                "chart": ALL,
                "selector": ALL,
                "page": "per_zr",
            },
            "id",
        ),
    )
    def _update_page_per_zr(
        selections: dict,
        page_selected: str,
        figure_ids: List[dict],
    ) -> list:
        if page_selected != "per_zr":
            raise PreventUpdate

        selections = selections[page_selected]
        if not selections["update"]:
            raise PreventUpdate

        figs = {}
        for selector in [x["selector"] for x in figure_ids]:
            dframe = volumemodel.get_df(
                filters=selections["filters"], groups=[selector]
            )
            texttemplate = (
                "%{text:.3s}"
                if selections["X Response"] in volumemodel.volume_columns
                else "%{text:.3g}"
            )
            # pylint: disable=no-member
            figs[selector] = {
                "pie": create_figure(
                    plot_type="pie",
                    data_frame=dframe,
                    values=selections["X Response"],
                    names=selector,
                    title=f"{selections['X Response']} per {selector}",
                    color_discrete_sequence=selections["Colorscale"],
                    color=selector,
                )
                .update_traces(marker_line=dict(color="#000000", width=1))
                .update_layout(margin=dict(l=10, b=10)),
                "bar": create_figure(
                    plot_type="bar",
                    data_frame=dframe,
                    x=selector,
                    y=selections["X Response"],
                    color_discrete_sequence=px.colors.diverging.BrBG_r,
                    color=selections["Color by"],
                    text=selections["X Response"],
                    xaxis=dict(
                        type="category", tickangle=45, tickfont_size=17, title=None
                    ),
                )
                .update_traces(texttemplate=texttemplate, textposition="auto")
                .add_annotation(fluid_annotation(selections)),
            }

        output_figs = []
        for fig_id in figure_ids:
            output_figs.append(figs[fig_id["selector"]][fig_id["chart"]])
        return output_figs

    @app.callback(
        Output(
            {"id": get_uuid("main-voldist"), "element": "plot", "page": "conv"},
            "figure",
        ),
        Input(get_uuid("selections"), "data"),
        State(get_uuid("page-selected"), "data"),
    )
    def _update_page_conv(selections: dict, page_selected: str) -> go.Figure:
        if page_selected != "conv":
            raise PreventUpdate

        selections = selections[page_selected]
        if not selections["update"]:
            raise PreventUpdate

        subplots = selections["Subplots"] if selections["Subplots"] is not None else []
        groups = ["REAL"]
        if subplots and subplots not in groups:
            groups.append(subplots)

        dframe = volumemodel.get_df(filters=selections["filters"], groups=groups)
        dframe = dframe.sort_values(by=["REAL"])

        dfs = []
        df_groups = dframe.groupby(subplots) if subplots else [(None, dframe)]
        for _, df in df_groups:
            for calculation in ["mean", "p10", "p90"]:
                df_stat = df.copy()
                df_stat[selections["X Response"]] = (
                    (df_stat[selections["X Response"]].expanding().mean())
                    if calculation == "mean"
                    else df_stat[selections["X Response"]]
                    .expanding()
                    .quantile(0.1 if calculation == "p90" else 0.9)
                )
                df_stat["calculation"] = calculation
                dfs.append(df_stat)
        if dfs:
            dframe = pd.concat(dfs)

        figure = (
            create_figure(
                plot_type="line",
                data_frame=dframe,
                x="REAL",
                y=selections["X Response"],
                facet_col=selections["Subplots"],
                color="calculation",
                title=f"Convergence plot of mean/p10/p90 for {selections['X Response']} ",
                yaxis=dict(showticklabels=True),
            )
            .update_traces(line_width=3.5)
            .update_traces(line=dict(color="black"), selector={"name": "mean"})
            .update_traces(
                line=dict(color="firebrick", dash="dash"),
                selector={"name": "p10"},
            )
            .update_traces(
                line=dict(color="royalblue", dash="dash"), selector={"name": "p90"}
            )
            .add_annotation(fluid_annotation(selections))
        )

        if selections["Subplots"] is not None:
            if not selections["X axis matches"]:
                figure.update_xaxes({"matches": None})
            if not selections["Y axis matches"]:
                figure.update_yaxes(dict(matches=None))
        return figure

    @app.callback(
        Output(
            {
                "id": get_uuid("main-tornado"),
                "element": "bulktornado",
                "page": "tornado",
            },
            "figure",
        ),
        Output(
            {
                "id": get_uuid("main-tornado"),
                "element": "inplacetornado",
                "page": "tornado",
            },
            "figure",
        ),
        Output(
            {
                "id": get_uuid("main-tornado"),
                "wrapper": "table",
                "page": "tornado",
            },
            "children",
        ),
        Input(get_uuid("selections"), "data"),
        State(get_uuid("page-selected"), "data"),
    )
    def _update_page_tornado(selections: dict, page_selected: str) -> go.Figure:

        if page_selected != "tornado":
            raise PreventUpdate

        selections = selections[page_selected]
        if not selections["update"]:
            raise PreventUpdate

        filters = selections["filters"].copy()

        figures = []
        tables = []
        for plot_id in ["left", "right"]:
            response = selections[f"Response {plot_id}"]
            sensfilter = selections[f"Sensitivities {plot_id}"]

            if selections["Reference"] not in sensfilter:
                sensfilter.append(selections["Reference"])

            filters.update(SENSNAME=sensfilter)

            groups = ["REAL", "ENSEMBLE", "SENSNAME", "SENSCASE", "SENSTYPE"]
            df_for_tornado = volumemodel.get_df(filters=filters, groups=groups)
            df_for_tornado.rename(columns={response: "VALUE"}, inplace=True)

            tornado_data = TornadoData(
                dframe=df_for_tornado,
                reference=selections["Reference"],
                response_name=response,
                scale=selections["Scale"],
                cutbyref=bool(selections["Remove no impact"]),
            )
            figure = TornadoBarChart(
                tornado_data=tornado_data,
                plotly_theme=theme.plotly_theme,
                label_options=selections["labeloptions"],
                number_format="#.3g",
                use_true_base=selections["Scale"] == "True",
                show_realization_points=bool(selections["real_scatter"]),
            ).figure

            figure.update_xaxes(
                gridwidth=1,
                gridcolor="whitesmoke",
                showgrid=True,
                side="bottom",
                title=None,
            ).update_layout(
                title=dict(
                    text=f"Tornadoplot for {response} <br>"
                    + f"Fluid zone: {(' + ').join(selections['filters']['FLUID_ZONE'])}",
                    font=dict(size=18),
                ),
                margin={"t": 70},
                hovermode="closest",
            ).update_traces(
                hovertemplate="REAL: %{text}<extra></extra>",
                selector={"type": "scatter"},
            )

            figures.append(figure)

            tornado_table = TornadoTable(tornado_data=tornado_data)
            table_data = tornado_table.as_plotly_table
            for data in table_data:
                data["Reference"] = tornado_data.reference_average
            tables.append(table_data)

        return (
            figures[0],
            figures[1],
            html.Div(
                children=[
                    html.Div(
                        style={"margin-top": "20px"},
                        children=create_data_table(
                            volumemodel=volumemodel,
                            columns=tornado_table.columns
                            + create_table_columns(
                                columns=["Reference"],
                                format_columns=["Reference"],
                                use_si_format=True,
                            ),
                            data=table,
                            height="20vh",
                            table_id={"table_id": f"{page_selected}-table{idx}"},
                        ),
                    )
                    for idx, table in enumerate(tables)
                ]
            ),
        )

    @app.callback(
        Output(
            {
                "id": get_uuid("main-src-comp"),
                "wrapper": "table",
                "page": "src-comp",
            },
            "children",
        ),
        Input(get_uuid("selections"), "data"),
        Input({"id": get_uuid("main-src-comp"), "element": "display-option"}, "value"),
        State(get_uuid("page-selected"), "data"),
    )
    def _update_page_src_comp(
        selections: dict, display_option: str, page_selected: str
    ) -> html.Div:
        ctx = dash.callback_context.triggered[0]

        if page_selected != "src-comp":
            raise PreventUpdate

        selections = selections[page_selected]

        if not "display-option" in ctx["prop_id"]:
            if not selections["update"]:
                raise PreventUpdate

        response = selections["Response"]
        resp1 = f"{response} {selections['Source A']}"
        resp2 = f"{response} {selections['Source B']}"
        src1, src2 = selections["Source A"], selections["Source B"]
        groupby = selections["Group by"] if selections["Group by"] is not None else []
        diff_mode = selections["Diff mode"]

        if src1 == src2:
            return html.Div("Comparison between equal sources")

        groups = ["REAL", "SOURCE", "ENSEMBLE"]
        for selector in groupby:
            if selector not in groups:
                groups.append(selector)

        selections["filters"]["SOURCE"] = [src1, src2]
        dframe = volumemodel.get_df(filters=selections["filters"], groups=groups)

        df = (
            dframe.loc[:, groups + [response]]
            .pivot_table(
                columns=["SOURCE"],
                index=[x for x in groups if x not in ["SOURCE"]],
            )
            .reset_index()
        )
        df.columns = df.columns.map(" ".join).str.strip(" ")

        # todo -  rearrange cols for resp1 og resp2

        df["diff"] = df[resp2] - df[resp1]
        df["diff (%)"] = ((df[resp2] / df[resp1]) - 1) * 100
        df = df.replace([np.inf, -np.inf], np.nan)

        def compute_accepted_col(df):
            accept_mask = (df[resp1] > selections["Ignore value"]) & (
                df["diff (%)"].abs() < selections["Accept value"]
            ) | (df[resp1] <= selections["Ignore value"])

            df["accepted"] = "no"
            df.loc[accept_mask, "accepted"] = "yes"
            return df

        def count_not_accepted(df):
            return len(df[df["accepted"] == "no"])

        def test(row, selectors, df_real):
            query = " & ".join([f"{col}=='{row[col]}'" for col in selectors])
            result = df_real.query(query)
            return f"{str(count_not_accepted(result))} / {str(len(result))}"  # * 100

        df_real = compute_accepted_col(df)
        non_accepted_count_real = count_not_accepted(df_real)

        selectors = [x for x in groupby if x != "REAL"]
        df = df.groupby(["ENSEMBLE"] + selectors).mean().reset_index()
        df = df.drop(columns="REAL")
        df = compute_accepted_col(df)
        non_accepted_count_group = count_not_accepted(df)
        df["# reals"] = df.apply(
            lambda row: test(row, ["ENSEMBLE"] + selectors, df_real), axis=1
        )

        df = df_real if "REAL" in groupby else df

        if display_option == "table":
            selections["Table type"] = "Mean table"

            if selections["Sort"]:
                df = df.sort_values(by=[diff_mode], key=abs, ascending=False)

            columns = create_table_columns(
                columns=df.columns,
                use_si_format=response in volumemodel.volume_columns,
                format_columns=[col for col in df.columns if col not in groups],
            )
            for col in columns:
                if "%" in col["id"]:
                    col["format"].update(specifier=".1f")

            return html.Div(
                create_data_table(
                    volumemodel=volumemodel,
                    columns=columns,
                    height="80vh",
                    data=df.to_dict("records"),
                    table_id={"table_id": "src-comp-table"},
                    style_cell={"textAlign": "center"},
                    style_data_conditional=[
                        {
                            "if": {"filter_query": "{accepted} = 'no'"},
                            "color": "#FF1243",
                            "fontWeight": "bold",
                        },
                    ],
                    disjoint_set_df=disjoint_set_df,
                )
            )

        colorby = selections["Color by"]
        if colorby != "accepted":
            colorby = groupby[0] if groupby else None
        color_map = {"no": "#FF1243", "yes": "#80B7BC"}

        fig_corr, fig_diff_vs_response, fig_dif_vs_real = (
            (
                create_figure(
                    plot_type="scatter",
                    data_frame=df_plot,
                    x=x,
                    y=y,
                    color_discrete_sequence=px.colors.qualitative.Dark2,
                    color_discrete_map=color_map if colorby == "accepted" else None,
                    color=colorby,
                    hover_data={col: True for col in selectors},
                )
                .update_traces(marker_size=10)
                .update_layout(margin={"l": 20, "r": 20, "t": 20, "b": 20})
            )
            for (df_plot, x, y) in [
                (df, resp1, resp2),
                (df, resp1, diff_mode),
                (df_real, "REAL", diff_mode),
            ]
        )

        fig_corr = add_correlation_line(
            figure=fig_corr,
            xy_min=min(df[resp1].min(), df[resp2].min()),
            xy_max=max(df[resp1].max(), df[resp2].max()),
        )

        fig_distribution = create_figure(
            plot_type="distribution",
            data_frame=dframe,
            x=response,
            color_discrete_sequence=selections["Colorscale"],
            color="SOURCE",
        ).update_layout(margin={"l": 75, "r": 20, "t": 20, "b": 20})

        if diff_mode == "diff (%)":
            fig_dif_vs_real.add_hline(
                y=selections["Accept value"], line_dash="dot"
            ).add_hline(y=-selections["Accept value"], line_dash="dot")

        def find_diff_plot_range(df, diff_mode, selections):
            if selections["Axis focus"] and "no" in df["accepted"].values:
                data = df[df["accepted"] == "no"][diff_mode]
            else:
                data = df[diff_mode]

            low = min(data.min(), -selections["Accept value"])
            high = max(data.max(), selections["Accept value"])
            extend = (high - low) * 0.1
            return [low - extend, high + extend]

        plotrange = find_diff_plot_range(df_real, diff_mode, selections)
        fig_dif_vs_real.update_yaxes(range=plotrange)
        fig_diff_vs_response.update_yaxes(range=plotrange)

        return src_comp_qc_plots_layout(
            fig_dif_vs_real,
            fig_corr,
            fig_diff_vs_response,
            fig_distribution,
            non_accepted_count_group,
            non_accepted_count_real,
            selectors,
            response,
            src1,
            src2,
        )
