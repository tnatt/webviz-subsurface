from typing import Optional, List
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from dash import html, dash_table, no_update
import webviz_core_components as wcc


def make_table(
    dframe: pd.DataFrame,
    responses: list,
    table_type: str,
    selectors: list,
    height: str,
    tab: str,
    groups: Optional[list] = None,
    style_data_conditional=None,
) -> html.Div:

    groups = groups if groups is not None else []

    if table_type == "Statistics table":
        statcols = ["Mean", "Stddev", "P90", "P10", "Min", "Max", "Count"]
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
                    "Min": values.min(),
                    "Max": values.max(),
                    "Count": len(values),
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
                    "format": {"specifier": ".1f"} if col != "Count" else None,
                }
                for col in ["Response"] + groups + statcols
            ],
            data=data_list,
            selectors=selectors,
            height=height,
            table_id=f"{tab}-stattable",
            style_data_conditional=style_data_conditional,
        )

    # if table type Mean table
    if table_type == "Mean table":
        dframe = (
            dframe[responses + groups].groupby(groups).mean().reset_index()
            if groups
            else dframe[responses].mean().to_frame().T
        )
    else:
        dframe = dframe[groups + responses]

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
        table_id=f"{tab}-meantable",
        style_data_conditional=style_data_conditional,
    )


def create_dash_table(
    columns, data, selectors, height, table_id, style_data_conditional=None
):
    style_cell_conditional = [
        {
            "if": {"column_id": selectors + ["Response"]},
            "textAlign": "left",
            "width": "10%",
        },
    ]

    return html.Div(
        style={"margin-top": "20px"},
        children=wcc.WebvizPluginPlaceholder(
            id={"request": "table_data", "table_id": table_id},
            buttons=["expand", "download"],
            children=dash_table.DataTable(
                id={"table_id": table_id},
                sort_action="native",
                sort_mode="multi",
                filter_action="native",
                columns=columns,
                data=data,
                style_cell_conditional=style_cell_conditional,
                style_data_conditional=style_data_conditional,
                style_table={
                    "height": height,
                    "overflowY": "auto",
                },
            ),
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
