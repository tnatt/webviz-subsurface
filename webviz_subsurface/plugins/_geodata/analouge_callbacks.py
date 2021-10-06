from typing import Callable

import pandas as pd
from dash import Input, Output, State, ALL, callback
from dash.exceptions import PreventUpdate
from .channel_callbacks import make_table


def analouge_callback(get_uuid: Callable, analouge_df: pd.DataFrame, selectors: list):
    @callback(
        Output(get_uuid("main-table-analouge"), "children"),
        Input({"id": get_uuid("selections-table-analouge"), "selector": ALL}, "value"),
        Input({"id": get_uuid("selections-table-analouge"), "filter": ALL}, "value"),
        Input(get_uuid("tabs"), "value"),
        State({"id": get_uuid("selections-table-analouge"), "selector": ALL}, "id"),
        State({"id": get_uuid("selections-table-analouge"), "filter": ALL}, "id"),
    )
    def update_table(
        table_selections: list,
        table_filters: list,
        selected_tab,
        selector_ids,
        filter_ids,
    ) -> list:

        if selected_tab != "analouge":
            raise PreventUpdate

        selections = {
            id_value["selector"]: value
            for id_value, value in zip(selector_ids, table_selections)
        }
        filters = {
            id_value["filter"]: value
            for id_value, value in zip(filter_ids, table_filters)
        }

        dframe = analouge_df
        for filt, values in filters.items():
            dframe = dframe.loc[dframe[filt].isin(values)]

        return make_table(
            dframe,
            selections["table_responses"],
            table_type=selections["Table type"],
            groups=selections["Group by"],
            height="80vh",
            selectors=selectors,
        )
