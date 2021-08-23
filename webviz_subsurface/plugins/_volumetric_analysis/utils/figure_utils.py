def fluid_annotation(selections: dict) -> dict:
    fluid_text = (" + ").join(selections["filters"]["FLUID_ZONE"])
    return dict(
        visible=bool(selections["Fluid annotation"])
        and selections["Subplots"] != "FLUID_ZONE",
        x=1,
        y=1,
        xref="paper",
        yref="paper",
        showarrow=False,
        text="Fluid zone<br>" + fluid_text,
        font=dict(size=15, color="black"),
        bgcolor="#E8E8E8",
    )


def add_correlation_line(figure, xy_min, xy_max):
    return figure.add_shape(
        type="line",
        layer="below",
        xref="x",
        yref="y",
        x0=xy_min,
        y0=xy_min,
        x1=xy_max,
        y1=xy_max,
        line=dict(color="black", width=2, dash="dash"),
    )
