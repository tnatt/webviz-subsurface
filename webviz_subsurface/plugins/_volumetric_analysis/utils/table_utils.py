from typing import Tuple, List, Optional
import pandas as pd
from pandas.api.types import is_numeric_dtype
import numpy as np

from dash_table.Format import Format
import dash_html_components as html
import dash_table

import webviz_core_components as wcc

from webviz_subsurface._models import InplaceVolumesModel


# pylint: disable=too-many-locals
def make_table_wrapper_children(
    dframe: pd.DataFrame,
    responses: list,
    volumemodel: InplaceVolumesModel,
    selections: dict,
    table_type: str,
    view_height: float,
    page_selected: str,
    groups: Optional[list] = None,
) -> html.Div:

    groups = groups if groups is not None else []

    if table_type == "Statistics table":
        statcols = ["Mean", "Stddev", "P90", "P10", "Minimum", "Maximum"]
        groups = [x for x in groups if x != "REAL"]
        df_groups = dframe.groupby(groups) if groups else [(None, dframe)]

        data_properties = []
        data_volcols = []
        for response in responses:
            if not is_numeric_dtype(dframe[response]):
                continue
            for name, df in df_groups:
                values = df[response]
                data = {
                    "Response"
                    if response in volumemodel.volume_columns
                    else "Property": response,
                    "Mean": values.mean(),
                    "Stddev": values.std(),
                    "P10": np.nanpercentile(values, 90),
                    "P90": np.nanpercentile(values, 10),
                    "Minimum": values.min(),
                    "Maximum": values.max(),
                }
                if "FLUID_ZONE" not in groups:
                    data.update(
                        FLUID_ZONE=(" + ").join(selections["filters"]["FLUID_ZONE"])
                    )

                for idx, group in enumerate(groups):
                    data[group] = (
                        name if isinstance(name, str) == 1 else list(name)[idx]
                    )
                if response in volumemodel.volume_columns:
                    data_volcols.append(data)
                else:
                    data_properties.append(data)

        if data_volcols and data_properties:
            view_height = view_height / 2

        return html.Div(
            children=[
                html.Div(
                    style={"margin-top": "20px"},
                    children=create_data_table(
                        volumemodel=volumemodel,
                        columns=create_table_columns(
                            columns=[col]
                            + [x for x in groups if x != "FLUID_ZONE"]
                            + statcols
                            + ["FLUID_ZONE"],
                            format_columns=statcols,
                            use_si_format=col == "Response",
                        ),
                        data=data,
                        height=f"{view_height}vh",
                        table_id={"table_id": f"{page_selected}-{col}"},
                    ),
                )
                for col, data in zip(
                    ["Response", "Property"], [data_volcols, data_properties]
                )
            ]
        )

    # if table type Mean table
    groupby_real = (
        selections["Group by"] is not None and "REAL" in selections["Group by"]
    )
    if "REAL" in groups and not groupby_real:
        groups.remove("REAL")

    columns = responses + [x for x in groups if x not in responses]
    dframe = (
        dframe[columns].groupby(groups).mean().reset_index()
        if groups
        else dframe[responses].mean().to_frame().T
    )

    if "FLUID_ZONE" not in dframe:
        dframe["FLUID_ZONE"] = (" + ").join(selections["filters"]["FLUID_ZONE"])

    dframe = dframe[[x for x in dframe.columns if x != "FLUID_ZONE"] + ["FLUID_ZONE"]]
    return html.Div(
        children=[
            create_data_table(
                volumemodel=volumemodel,
                columns=create_table_columns(
                    columns=dframe.columns,
                    format_columns=dframe.columns,
                    volumemodel=volumemodel,
                ),
                data=dframe.iloc[::-1].to_dict("records"),
                height=f"{view_height}vh",
                table_id={"table_id": f"{page_selected}-meantable"},
            )
        ]
    )


def create_table_columns(
    columns: list,
    volumemodel: Optional[InplaceVolumesModel] = None,
    format_columns: Optional[list] = None,
    use_si_format: Optional[bool] = None,
) -> List[dict]:

    format_columns = format_columns if format_columns is not None else []

    table_columns = []
    for col in columns:
        data = {"id": col, "name": col}
        if col in format_columns:
            data.update(
                {
                    "type": "numeric",
                    "format": {"locale": {"symbol": ["", ""]}, "specifier": "$.4s"}
                    if use_si_format
                    or volumemodel is not None
                    and col in volumemodel.volume_columns
                    else Format(precision=3),
                }
            )
        table_columns.append(data)
    return table_columns


# pylint: disable=inconsistent-return-statements
def create_data_table(
    volumemodel: InplaceVolumesModel,
    columns: list,
    height: str,
    data: List[dict],
    table_id: dict,
    style_cell: Optional[list] = None,
    style_header_conditional: Optional[list] = None,
    style_cell_conditional: Optional[list] = None,
    style_data_conditional: Optional[list] = None,
    disjoint_set_df: Optional[list] = None,
) -> dash_table.DataTable:

    if not data:
        return []

    if style_cell_conditional is None:
        style_cell_conditional = [
            {
                "if": {
                    "column_id": volumemodel.selectors
                    + ["Response", "Property", "Sensitivity"]
                },
                "width": "10%",
                "textAlign": "left",
            }
        ]
        style_cell_conditional.extend(
            [{"if": {"column_id": "FLUID_ZONE"}, "textAlign": "right"}]
        )
    style_data_conditional = (
        style_data_conditional if style_data_conditional is not None else []
    )
    style_data_conditional.extend(fluid_table_style())

    return wcc.WebvizPluginPlaceholder(
        id={"request": "table_data", "table_id": table_id["table_id"]},
        buttons=["expand", "download"],
        children=dash_table.DataTable(
            id=table_id,
            sort_action="native",
            sort_mode="multi",
            filter_action="native",
            columns=columns,
            data=data,
            style_as_list_view=True,
            style_cell=style_cell,
            style_cell_conditional=style_cell_conditional,
            style_data_conditional=style_data_conditional,
            style_table={
                "height": height,
                "overflowY": "auto",
            },
            style_header_conditional=style_header_conditional,
            merge_duplicate_headers=True,
            tooltip_data=tooltip_for_sets(disjoint_set_df, data),
            tooltip_duration=None,
        ),
    )


def tooltip_for_sets(disjoint_set_df, data):
    if disjoint_set_df is None or "SET" not in data[0]:
        return None

    set_fipnums = {}
    set_regzones = {}
    for set_idx, df in disjoint_set_df.groupby("SET"):
        set_fipnums[str(set_idx)] = df["FIPNUM"].astype(str).unique()
        set_regzones[str(set_idx)] = df["REGZONE"].astype(str).unique()

    return [
        {
            "SET": {
                "value": "**Set {}** \n\n**Fipnums:** {} \n\n**Regzones:** {}".format(
                    row["SET"],
                    ", ".join(set_fipnums[row["SET"]]),
                    ", ".join(set_regzones[row["SET"]]),
                ),
                "type": "markdown",
            }
        }
        for row in data
    ]


def fluid_table_style() -> list:
    fluid_colors = {
        "oil": "#007079",
        "gas": "#FF1243",
        "water": "#ADD8E6",
    }
    return [
        {
            "if": {
                "filter_query": "{FLUID_ZONE} = " + f"'{fluid}'",
                "column_id": "FLUID_ZONE",
            },
            "color": color,
            "fontWeight": "bold",
        }
        for fluid, color in fluid_colors.items()
    ]
