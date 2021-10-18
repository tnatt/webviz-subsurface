import base64
import plotly.express as px
from dash import html, Input, Output, State, callback, ALL, callback_context
from dash.exceptions import PreventUpdate
import webviz_core_components as wcc
from webviz_subsurface._figures import create_figure
from webviz_subsurface._utils.webvizstore_functions import get_path
from ..utils import make_table


def varviz_callback(get_uuid, vmodel, picture_files):
    @callback(
        Output(get_uuid("varviz-main"), "children"),
        Input({"id": get_uuid("ui"), "tab": "varviz", "selector": ALL}, "value"),
        Input({"id": get_uuid("ui"), "tab": "varviz", "filter": ALL}, "value"),
        Input(get_uuid("main-varviz-display-option"), "value"),
        Input(get_uuid("tabs"), "value"),
        State({"id": get_uuid("ui"), "tab": "varviz", "selector": ALL}, "id"),
        State({"id": get_uuid("ui"), "tab": "varviz", "filter": ALL}, "id"),
    )
    def _update_varviz_scatter(
        varviz_selections,
        varviz_filters,
        display_option,
        selected_tab,
        selector_ids,
        filter_ids,
    ):

        if selected_tab != "varviz":
            raise PreventUpdate

        selection = {
            id_value["selector"]: value
            for id_value, value in zip(selector_ids, varviz_selections)
            if value is not None
        }
        filters = {
            id_value["filter"]: value
            for id_value, value in zip(filter_ids, varviz_filters)
        }
        dframe = vmodel.dframe.copy()
        for filt, values in filters.items():
            dframe = dframe.loc[dframe[filt].isin(values)]

        groups = []
        for item in ["facet_col", "color"]:
            value = selection.get(item)
            if value is not None and value not in groups:
                groups.append(value)

        children = [
            wcc.Graph(
                #   config={"displayModeBar": False},
                id=get_uuid("varviz-scatter"),
                style={"height": "80vh" if display_option == "plot" else "50vh"},
                figure=create_figure(
                    **selection,
                    data_frame=dframe,
                    plot_type="scatter",
                    hover_data=list(filters.keys()),
                    color_continuous_scale="viridis",
                ),
            )
        ]
        if display_option == "plot_with_table":
            children.append(
                make_table(
                    dframe,
                    responses=[selection["x"], selection["y"]],
                    table_type="Statistics table",
                    groups=groups,
                    height="30vh",
                    selectors=vmodel.selectors,
                    tab="plots",
                )
            )
        return html.Div(children)

    @callback(
        Output(get_uuid("varviz-image-wrapper"), "children"),
        Input(get_uuid("varviz-scatter"), "selectedData"),
        Input(get_uuid("varviz-scatter"), "clickData"),
        State({"id": get_uuid("ui"), "tab": "varviz", "filter": ALL}, "id"),
    )
    def _update_images(selected_traces, clicked_trace, filter_ids):
        ctx = callback_context.triggered[0]
        if not ctx.get("value"):
            return []

        if ctx["prop_id"] == f"{get_uuid('varviz-scatter')}.selectedData":
            traces = selected_traces
        else:
            traces = clicked_trace
        image_divs = []
        models = []
        for idx, curve in enumerate(traces.get("points", [])):
            if idx > 4:
                break
            filters = {
                filter_id.get("filter"): filter_val
                for filter_id, filter_val in zip(filter_ids, curve.get("customdata"))
            }
            label = str(filters)
            model = filters["Delft3D model"]
            if model not in models:
                models.append(model)
        for model in models:
            for picfile in picture_files:
                if f"{model}.PNG" in picfile:

                    img = base64.b64encode(open(get_path(picfile), "rb").read()).decode(
                        "ascii"
                    )
                    image_divs.append(
                        html.Div(
                            children=[
                                html.Label(label),
                                html.A(
                                    target="_blank",
                                    href=f"data:image/png;base64,{img}",
                                    children=html.Img(
                                        src=f"data:image/png;base64,{img}",
                                        style={"height": "30vh"},
                                    ),
                                ),
                            ]
                        )
                    )

        return image_divs
