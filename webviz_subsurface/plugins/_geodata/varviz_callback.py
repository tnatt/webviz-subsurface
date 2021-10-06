import plotly.express as px
from dash import html, Input, Output, State, callback, ALL, callback_context
import webviz_core_components as wcc
from webviz_subsurface._figures import create_figure


def varviz_callback(get_uuid, variogram_df):
    @callback(
        Output(get_uuid("varviz-scatter"), "figure"),
        Input({"id": get_uuid("selections-varviz"), "selector": ALL}, "value"),
        Input({"id": get_uuid("selections-varviz"), "filter": ALL}, "value"),
        State({"id": get_uuid("selections-varviz"), "selector": ALL}, "id"),
        State({"id": get_uuid("selections-varviz"), "filter": ALL}, "id"),
    )
    def _update_varviz_scatter(
        varviz_selections, varviz_filters, selector_ids, filter_ids
    ):

        selection = {
            id_value["selector"]: value
            for id_value, value in zip(selector_ids, varviz_selections)
            if value is not None
        }
        filters = {
            id_value["filter"]: value
            for id_value, value in zip(filter_ids, varviz_filters)
        }
        dframe = variogram_df
        for filt, values in filters.items():
            dframe = dframe.loc[dframe[filt].isin(values)]

        return create_figure(
            **selection,
            data_frame=dframe,
            plot_type="scatter",
            hover_data=list(filters.keys()),
            color_continuous_scale="viridis",
        )

    @callback(
        Output(get_uuid("varviz-image-wrapper"), "children"),
        Input(get_uuid("varviz-scatter"), "selectedData"),
        Input(get_uuid("varviz-scatter"), "clickData"),
        State({"id": get_uuid("selections-varviz"), "filter": ALL}, "id"),
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
        gauss_img = gaussian_random_field()
        for idx, curve in enumerate(traces.get("points", [])):
            if idx > 4:
                break
            label = str(
                {
                    filter_id.get("filter"): filter_val
                    for filter_id, filter_val in zip(
                        filter_ids, curve.get("customdata")
                    )
                }
            )
            fig = px.imshow(
                gauss_img,
                color_continuous_scale="BrBG",
            )
            fig.update_layout(
                {
                    "plot_bgcolor": "rgba(0, 0, 0, 0)",
                    "paper_bgcolor": "rgba(0, 0, 0, 0)",
                }
            )
            image_divs.append(
                html.Div(
                    [
                        wcc.Label(label),
                        wcc.Graph(figure=fig),
                    ]
                )
            )

        return image_divs


import numpy
import scipy.fftpack


def fftind(size):
    """Returns a numpy array of shifted Fourier coordinates k_x k_y.

    Input args:
        size (integer): The size of the coordinate array to create
    Returns:
        k_ind, numpy array of shape (2, size, size) with:
            k_ind[0,:,:]:  k_x components
            k_ind[1,:,:]:  k_y components

    Example:

        print(fftind(5))

        [[[ 0  1 -3 -2 -1]
        [ 0  1 -3 -2 -1]
        [ 0  1 -3 -2 -1]
        [ 0  1 -3 -2 -1]
        [ 0  1 -3 -2 -1]]
        [[ 0  0  0  0  0]
        [ 1  1  1  1  1]
        [-3 -3 -3 -3 -3]
        [-2 -2 -2 -2 -2]
        [-1 -1 -1 -1 -1]]]

    """
    k_ind = numpy.mgrid[:size, :size] - int((size + 1) / 2)
    k_ind = scipy.fftpack.fftshift(k_ind)
    return k_ind


def gaussian_random_field(alpha=3.0, size=128, flag_normalize=True):
    """Returns a numpy array of shifted Fourier coordinates k_x k_y.

    Input args:
        alpha (double, default = 3.0):
            The power of the power-law momentum distribution
        size (integer, default = 128):
            The size of the square output Gaussian Random Fields
        flag_normalize (boolean, default = True):
            Normalizes the Gaussian Field:
                - to have an average of 0.0
                - to have a standard deviation of 1.0
    Returns:
        gfield (numpy array of shape (size, size)):
            The random gaussian random field

    Example:
    import matplotlib
    import matplotlib.pyplot as plt
    example = gaussian_random_field()
    plt.imshow(example)
    """

    # Defines momentum indices
    k_idx = fftind(size)

    # Defines the amplitude as a power law 1/|k|^(alpha/2)
    amplitude = numpy.power(k_idx[0] ** 2 + k_idx[1] ** 2 + 1e-10, -alpha / 4.0)
    amplitude[0, 0] = 0

    # Draws a complex gaussian random noise with normal
    # (circular) distribution
    noise = numpy.random.normal(size=(size, size)) + 1j * numpy.random.normal(
        size=(size, size)
    )

    # To real space
    gfield = numpy.fft.ifft2(noise * amplitude).real

    # Sets the standard deviation to one
    if flag_normalize:
        gfield = gfield - numpy.mean(gfield)
        gfield = gfield / numpy.std(gfield)

    return gfield
