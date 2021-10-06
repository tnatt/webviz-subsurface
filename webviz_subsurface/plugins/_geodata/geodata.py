from typing import List, Tuple, Callable, Optional
from pathlib import Path

import pandas as pd

from dash import html, Dash

from webviz_config import WebvizPluginABC
from webviz_config import WebvizSettings
from webviz_config.webviz_store import webvizstore
from webviz_config.common_cache import CACHE
from .main_view import main_view
from .varviz_callback import varviz_callback
from .channel_callbacks import channel_callback
from .analouge_callbacks import analouge_callback


class GeoData(WebvizPluginABC):
    def __init__(
        self,
        app: Dash,
        webviz_settings: WebvizSettings,
        csvfile_channel: Path,
        csvfile_variogram: Path,
        csvfile_analouge: Optional[Path] = None,
    ):

        super().__init__()
        self.csvfile_variogram = csvfile_variogram
        self.csvfile_channel = csvfile_channel
        self.csvfile_analouge = csvfile_analouge
        self.channels_df = read_csv(self.csvfile_channel)
        self.analouge_df = (
            read_csv(self.csvfile_analouge)
            if self.csvfile_analouge is not None
            else None
        )
        self.analouge_selectors = ["Study Name", "Attribute"]
        self.analouge_responses = ["Width", "Thickness"]
        self.variogram_df = read_csv(self.csvfile_variogram)
        self.variogram_df = self.variogram_df.dropna(how="any")
        self.variogram_df["Crop box number"] = self.variogram_df[
            "Crop box number"
        ].astype(str)
        # what to do here?
        self.variogram_df.loc[
            self.variogram_df["Quality factor"] < 0, "Quality factor"
        ] = 0

        self.theme_colors = webviz_settings.theme.plotly_theme.get("layout", {}).get(
            "colorway", []
        )

        self.selectors = ["Delft3D model", "Formation", "Attribute"]

        self.variogram_filters = [
            "Delft3D model",
            "Indicator",
            "Attribute",
            "Crop box number",
            "Variogram parameterzation",
            #   "Quality factor",
            #   "Identifier",
        ]
        self.variogram_responses = [
            col
            for col in self.variogram_df
            if col not in self.variogram_filters
            and "cropbox" not in col
            and col != "Standard deviation"
        ]
        self.responses = [
            "channel width mean",
            "channel width sd",
            "channel height mean",
            "channel height sd",
        ]
        self.set_callbacks()

    def add_webvizstore(self) -> List[Tuple[Callable, list]]:
        return [
            (read_csv, [{"csv_file": fn}])
            for fn in [
                self.csvfile_variogram,
                self.csvfile_channel,
                self.csvfile_analouge,
            ]
        ]

    @property
    def layout(self) -> html.Div:
        return html.Div(
            children=[
                main_view(
                    get_uuid=self.uuid,
                    responses=self.responses,
                    selectors=self.selectors,
                    channel_dframe=self.channels_df,
                    variogram_dframe=self.variogram_df,
                    variogram_filters=self.variogram_filters,
                    variogram_responses=self.variogram_responses,
                    analouge_dframe=self.analouge_df,
                    analouge_selectors=self.analouge_selectors,
                    analouge_responses=self.analouge_responses,
                ),
            ],
        )

    def set_callbacks(self) -> None:
        varviz_callback(get_uuid=self.uuid, variogram_df=self.variogram_df)
        channel_callback(
            get_uuid=self.uuid,
            channels_df=self.channels_df,
            responses=self.responses,
            selectors=self.selectors,
        )
        analouge_callback(
            get_uuid=self.uuid,
            analouge_df=self.analouge_df,
            selectors=self.analouge_selectors,
        )


@CACHE.memoize(timeout=CACHE.TIMEOUT)
@webvizstore
def read_csv(csv_file: Path) -> pd.DataFrame:
    return pd.read_csv(csv_file)
