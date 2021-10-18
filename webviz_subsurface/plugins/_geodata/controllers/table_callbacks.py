from typing import Callable

from dash import Input, Output, State, ALL, callback, html, no_update
from dash.exceptions import PreventUpdate
import webviz_core_components as wcc
from ..utils import make_table, update_relevant_components
from ..selections_view import filter_dropdowns


def table_callbacks(get_uuid: Callable, cmodel, vmodel, amodel, smdamodel):
    @callback(
        Output({"id": get_uuid("ui"), "tab": "tables", "selector": ALL}, "options"),
        Output({"id": get_uuid("ui"), "tab": "tables", "selector": ALL}, "value"),
        Output({"id": get_uuid("ui"), "tab": "tables", "selector": ALL}, "size"),
        Input({"id": get_uuid("ui"), "element": "table-data"}, "value"),
        State({"id": get_uuid("ui"), "tab": "tables", "selector": ALL}, "id"),
    )
    def update_table_selections(table_data: str, selector_ids) -> tuple:

        model = get_data_model(table_data)

        settings = {
            "Group by": {
                "options": [{"label": i, "value": i} for i in model.selectors],
                "value": None,
                "size": len(model.selectors),
            },
            "table_responses": {
                "options": [{"label": i, "value": i} for i in model.responses],
                "value": model.responses,
                "size": len(model.responses),
            },
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
            for prop in ["options", "value", "size"]
        )

    @callback(
        Output(
            {"id": get_uuid("ui"), "tab": "tables", "element": "filter_wrapper"},
            "children",
        ),
        Input({"id": get_uuid("ui"), "element": "table-data"}, "value"),
    )
    def update_table_filters(table_data: str) -> tuple:
        model = get_data_model(table_data)
        return filter_dropdowns(
            uuid=get_uuid("ui"),
            tab="tables",
            filters=model.selectors,
            dframe=model.dframe,
        )

    @callback(
        Output(get_uuid("main-table"), "children"),
        Input({"id": get_uuid("ui"), "tab": "tables", "selector": ALL}, "value"),
        Input({"id": get_uuid("ui"), "tab": "tables", "filter": ALL}, "value"),
        Input({"id": get_uuid("ui"), "element": "table-data"}, "value"),
        Input(get_uuid("tabs"), "value"),
        State({"id": get_uuid("ui"), "tab": "tables", "selector": ALL}, "id"),
        State({"id": get_uuid("ui"), "tab": "tables", "filter": ALL}, "id"),
    )
    def update_table(
        table_selections: list,
        table_filters: list,
        table_data,
        selected_tab,
        selector_ids,
        filter_ids,
    ) -> list:

        if selected_tab != "tables":
            raise PreventUpdate

        cfg = {
            id_value["selector"]: value
            for id_value, value in zip(selector_ids, table_selections)
        }
        filters = {
            id_value["filter"]: value
            for id_value, value in zip(filter_ids, table_filters)
        }

        model = get_data_model(table_data)
        dframe = model.dframe
        for filt, values in filters.items():
            dframe = dframe.loc[dframe[filt].isin(values)]

        return html.Div(
            children=[
                wcc.Header(f"Table showing statistics from source {table_data}"),
                make_table(
                    dframe,
                    cfg["table_responses"],
                    table_type=cfg["Table type"],
                    groups=cfg["Group by"],
                    height="80vh",
                    selectors=model.selectors,
                    tab="tables",
                ),
            ]
        )

    def get_data_model(table_data_selected):
        if table_data_selected == "DM - Channels":
            return cmodel
        elif table_data_selected == "DM - Variogram":
            return vmodel
        elif table_data_selected == "Safari":
            return amodel
        return smdamodel
