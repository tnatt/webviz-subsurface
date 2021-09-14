from typing import List
import pandas as pd

import dash_html_components as html
import webviz_core_components as wcc


def set_main_layout(uuid):
    return wcc.Frame(
        color="white",
        highlight=False,
        style={"height": "91vh"},
        children=[
            html.Div(
                style={"margin-bottom": "20px"},
                children=wcc.RadioItems(
                    vertical=False,
                    id={"id": uuid, "element": "display-option"},
                    options=[
                        {
                            "label": "QC plots",
                            "value": "plots",
                        },
                        {"label": "Table", "value": "table"},
                    ],
                    value="plots",
                ),
            ),
            html.Div(id={"id": uuid, "page": "setinfo"}),
        ],
    )


def set_selections_layout(
    uuid: str,
    tab: str,
) -> wcc.Selectors:
    return wcc.Selectors(
        label="TABLE COTROLS",
        open_details=True,
        children=wcc.Checklist(
            id={"id": uuid, "tab": tab, "selector": "Group table"},
            options=[
                {"label": "Group table on set", "value": "grouped"},
            ],
            value=[],
        ),
    )


def set_filter_layout(
    uuid: str,
    tab: str,
    disjoint_set_df: pd.DataFrame,
) -> wcc.Selectors:
    return wcc.Selectors(
        label="FILTERS",
        open_details=True,
        children=filter_dropdowns(
            uuid=uuid,
            tab=tab,
            disjoint_set_df=disjoint_set_df,
        ),
    )


def filter_dropdowns(
    uuid: str,
    disjoint_set_df: pd.DataFrame,
    tab: str,
) -> html.Div:
    dropdowns: List[html.Div] = []
    selectors = ["REGION", "ZONE", "FIPNUM", "SET"]
    for selector in selectors:
        if selector not in disjoint_set_df:
            continue
        elements = list(disjoint_set_df[selector].unique())

        dropdowns.append(
            html.Div(
                children=wcc.SelectWithLabel(
                    label=selector.lower().capitalize(),
                    id={"id": uuid, "tab": tab, "selector": selector},
                    options=[{"label": i, "value": i} for i in elements],
                    value=elements,
                    multi=True,
                    size=min(15, len(elements)),
                ),
            )
        )
    return html.Div(dropdowns)
