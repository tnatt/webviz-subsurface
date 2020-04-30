from plotly.subplots import make_subplots
from ._processing import filter_frame


def update_crossplot(dframe, wells, sizeby, colorby):
    wells = wells if isinstance(wells, list) else [wells]

    df = dframe[dframe["WELL"].isin(wells)]

    df = filter_frame(df, {"ACTIVE": 1})

    fig = make_subplots(
        rows=len(list(df["ENSEMBLE"].unique())), cols=1, vertical_spacing=0.1, subplot_titles=(df["ENSEMBLE"].unique()),
    )

    layout = fig["layout"]

    sim_range = find_sim_range(df)
    sizeref, cmin, cmax = size_color_settings(df, sizeby, colorby)

    shapes = []

    for i, (ens, ensdf) in enumerate(df.groupby("ENSEMBLE")):

        df = ensdf.groupby(["WELL", "DATE", "ZONE"]).mean().reset_index()

        trace = {
            "x": df["OBS"],
            "y": df["SIMULATED"],
            "type": "scatter",
            "mode": "markers",
            "hovertext": [
                f"Well: {well}"
                f"<br>Zone: {zone}"
                f"<br>Pressure observation: {obs:.2f}"             
                f"<br>Mean simulated pressure: {pressure:.2f}"
                f"<br>Mean misfit: {misfit:.2f}"
                f"<br>Stddev pressure: {stddev:.2f}"
                for well, zone, obs, stddev, misfit, pressure in zip(
                    df["WELL"], df["ZONE"], df["OBS"], df["STDDEV"], df["DIFF"], df["SIMULATED"]
                )
            ],
            "hoverinfo": "text",
            "marker": {
                "size": df[sizeby],
                "sizeref": 2.0 * sizeref / (30.0 ** 2),
                "sizemode": "area",
                "sizemin": 6,
                "color": df[colorby],
                "cmin": cmin,
                "cmax": cmax,
                "colorscale": [[0, "rgb(0,0,255)"], [1, "rgb(255,0,0)"]],
                "colorbar": {"x": -0.15},
                "showscale": i==0,
            },
        }

        fig.add_trace(trace, i + 1, 1)
        add_diagonal_line(shapes, sim_range, i)
      
        # First figure ('yaxis')
        if i == 0:
            layout.update(
                {
                    "xaxis": {"range": sim_range, "title": "Pressure Observation"},
                    "yaxis": {"range": sim_range, "title": "Simulated mean pressure"},
                }
            )
        # Remaining figures ('yaxisX')
        else:
            layout.update(
                {
                    f"xaxis{i+1}": {
                        "range": sim_range,
                        "title": "Pressure Observation",
                    },
                    f"yaxis{i+1}": {
                        "range": sim_range,
                        "title": "Simulated mean pressure",
                    },
                }
            )

    layout.update(
        {
            "height": 1000,
            "shapes": shapes,
            "showlegend": False,
            "title": {
                "text": "<b>RFT crossplot - sim vs obs</b>",
                "font": {"size": 30, "color": "DarkOrange"},
                "x": 0.5,
                "xanchor": "center",
            },
        }
    )

    return {"data": fig["data"], "layout": layout}


def add_diagonal_line(shapes, sim_range, index):

    shape_layout = {
        "type": "line",
        "yref": f"y{index+1}",
        "xref": f"x{index+1}",
        "x0": sim_range[0],
        "y0": sim_range[0],
        "x1": sim_range[1],
        "y1": sim_range[1],
        "line": {"color": "DarkOrange", "width": 3,},
    }
    shapes.append(shape_layout)
    return shapes


def size_color_settings(df, sizeby, colorby):
    
    df = df.groupby(["WELL", "DATE", "ZONE", "ENSEMBLE"]).mean().reset_index()

    sizeref =  df[sizeby].quantile(0.9)
    cmin = df[colorby].min()
    cmax = df[colorby].quantile(0.9)

    return sizeref, cmin, cmax


def find_sim_range(df):
    
    df = df.groupby(["WELL", "DATE", "ZONE", "ENSEMBLE"]).mean().reset_index()

    max_sim = df["SIMULATED"].max() if df["SIMULATED"].max() > df["OBS"].max() else df["OBS"].max() 
    min_sim = df["SIMULATED"].min() if df["SIMULATED"].min() < df["OBS"].min() else df["OBS"].min() 

    axis_extend = (max_sim - min_sim) * 0.1

    return [min_sim - axis_extend, max_sim + axis_extend]

