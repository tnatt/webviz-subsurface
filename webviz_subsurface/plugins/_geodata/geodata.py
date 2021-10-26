from typing import List, Tuple, Callable, Optional
from pathlib import Path

import numpy as np
import pandas as pd
import json
from dash import html, Dash, dcc
import plotly.express as px
from webviz_config import WebvizPluginABC
from webviz_config.webviz_assets import WEBVIZ_ASSETS
from webviz_config.webviz_store import webvizstore
from webviz_config.common_cache import CACHE
import webviz_subsurface
from webviz_subsurface._utils.webvizstore_functions import find_files, get_path
from .main_view import main_view
from .controllers import (
    varviz_callback,
    channel_callback,
    analogue_smda_callbacks,
    export_data_controllers,
    table_callbacks,
)


class GeoData(WebvizPluginABC):
    def __init__(
        self,
        app: Dash,
        csvfile_channel: Path,
        picture_folder: Path,
        csvfile_variogram: Path,
        csvfile_analogue: Optional[Path] = None,
        csvfile_smda_ae: Optional[Path] = None,
        csvfile_smda_strat: Optional[Path] = None,
    ):

        WEBVIZ_ASSETS.add(
            Path(webviz_subsurface.__file__).parent / "_assets" / "css" / "geodata.css"
        )

        super().__init__()
        self.csvfile_variogram = csvfile_variogram
        self.csvfile_channel = csvfile_channel
        self.csvfile_analogue = csvfile_analogue
        self.csvfile_smda_ae = csvfile_smda_ae
        self.csvfile_smda_strat = csvfile_smda_strat

        self.vmodel = VariogramModel(read_csv(self.csvfile_variogram))
        self.picture_folder = picture_folder
        self.picture_files = json.load(
            find_files(folder=Path(self.picture_folder), suffix=".PNG")
        )
        self.cmodel = ChannelModel(read_csv(self.csvfile_channel))
        self.amodel = (
            AnalogueModel(read_csv(self.csvfile_analogue))
            if csvfile_analogue is not None
            else None
        )
        self.smdamodel = (
            SMDAModel(read_csv(self.csvfile_smda_ae), read_csv(self.csvfile_smda_strat))
            if csvfile_smda_ae is not None
            else None
        )
        self.set_callbacks()

    @property
    def layout(self) -> html.Div:
        return html.Div(
            children=[
                html.Div(
                    style={"display": "none"},
                    children=dcc.Download(id=self.uuid("download-dataframe")),
                ),
                main_view(
                    get_uuid=self.uuid,
                    cmodel=self.cmodel,
                    vmodel=self.vmodel,
                    amodel=self.amodel,
                    smdamodel=self.smdamodel,
                ),
            ],
        )

    def set_callbacks(self) -> None:
        varviz_callback(
            get_uuid=self.uuid, vmodel=self.vmodel, picture_files=self.picture_files
        )
        channel_callback(
            get_uuid=self.uuid,
            channels_df=self.cmodel.dframe,
            responses=self.cmodel.responses,
            selectors=self.cmodel.selectors,
            amodel=self.amodel,
        )
        analogue_smda_callbacks(
            get_uuid=self.uuid, amodel=self.amodel, smdamodel=self.smdamodel
        )
        table_callbacks(
            get_uuid=self.uuid,
            cmodel=self.cmodel,
            vmodel=self.vmodel,
            amodel=self.amodel,
            smdamodel=self.smdamodel,
        )

        export_data_controllers(get_uuid=self.uuid)

    def add_webvizstore(self) -> List[Tuple[Callable, list]]:
        funcs = [
            (read_csv, [{"csv_file": fn}])
            for fn in [
                self.csvfile_variogram,
                self.csvfile_channel,
                self.csvfile_analogue,
                self.csvfile_smda_ae,
                self.csvfile_smda_strat,
            ]
        ]
        funcs.append(
            (find_files, [{"folder": Path(self.picture_folder), "suffix": ".PNG"}])
        )
        print(self.picture_files)
        funcs.extend([(get_path, [{"path": model}]) for model in self.picture_files])
        return funcs


class AnalogueModel:
    COLUMN_RENAMING = {
        "Channel width": "channel width mean",
        "Channel height": "channel height mean",
    }

    def __init__(self, dframe: pd.DataFrame):
        self.dframe = dframe.rename(columns=self.COLUMN_RENAMING)
        self.dframe["Data source"] = "Analogue"
        self.selectors = [
            "Data source",
            "Outcrop",
            "Architectural element",
            "Channel type",
        ]
        self.responses = [x for x in self.dframe.columns if x not in self.selectors]
        self.colors = {
            outcrop: color
            for outcrop, color in zip(
                dframe["Outcrop"].unique(), px.colors.qualitative.T10
            )
        }
        self.colors.update({"Digital Models": "black"})


class SMDAModel:
    COLUMN_RENAMING = {
        "country_identifier": "Country",
        "field_identifier": "Field",
        "unique_wellbore_identifier": "Wellbore",
        "strat_unit_identifier": "Formation"
        #      "identifier": "Architectural element"
    }

    def __init__(self, dframe_ae: pd.DataFrame, dframe_strat: pd.DataFrame):
        self.dframe = dframe_ae.rename(columns=self.COLUMN_RENAMING, errors="ignore")
        self.dframe_strat = dframe_strat.rename(
            columns=self.COLUMN_RENAMING, errors="ignore"
        )

        self.dframe["thickness_md"] = (
            self.dframe["base_depth_md"] - self.dframe["top_depth_md"]
        )
        self.dframe["Data source"] = "SMDA"
        self.dframe["Formation"] = self.dframe.apply(
            lambda row: self.find_strat_information(row), axis=1
        )
        #       self.identifiers = list(self.dframe["Architectural element"].unique())
        self.selectors = [
            "Data source",
            "Country",
            "Field",
            "Wellbore",
            "Architectural element",
            "Formation",
        ]
        self.responses = ["thickness_md"]

        self.colors = {
            outcrop: color
            for outcrop, color in zip(
                self.dframe["Architectural element"].unique(),
                px.colors.qualitative.Safe,
            )
        }

    def find_strat_information(self, row: pd.Series):
        midpoint = row["top_depth_md"] + (row["thickness_md"] / 2)
        strat_df = self.dframe_strat.loc[
            self.dframe_strat["Wellbore"] == row["Wellbore"]
        ]
        result = strat_df.loc[
            (strat_df["entry_md"] < midpoint) & (midpoint < strat_df["exit_md"])
        ]
        # NB check if this result always is 1 item
        return result["Formation"].iloc[0] if not result.empty else "-"


class ChannelModel:
    def __init__(self, dframe: pd.DataFrame):
        self.dframe = dframe
        self.dframe["Data source"] = "Digital Models"
        self.selectors = ["Data source", "Delft3D model", "Formation", "Attribute"]
        self.responses = [
            "channel width mean",
            "channel width sd",
            "channel height mean",
            "channel height sd",
        ]


class VariogramModel:
    INDICATOR_RENAMING = {
        "0": "Inactive cells",
        "1": "Active channel",
        "2": "Channel fill",
        "3": "Delta top background",
        "4": "Mouthbar",
        "5": "Delta front background",
        "6": "Prodaelta",
    }

    def __init__(self, dframe: pd.DataFrame):

        self.dframe = dframe.dropna(how="any").copy()
        self.dframe["Crop box number"] = self.dframe["Crop box number"].astype(str)
        # what to do here?
        self.dframe.loc[self.dframe["Quality factor"] < 0, "Quality factor"] = 0
        self.dframe.replace({"Indicator": self.INDICATOR_RENAMING}, inplace=True)
        self.dframe.replace({"Attribute": {"Porosity": "porosity"}}, inplace=True)
        self.dframe["Formation"] = np.where(
            self.dframe["Delft3D model"].str.startswith("MS2"), "Ile 2", "Aare 4.2-4.3"
        )

        self.selectors = [
            "Delft3D model",
            "Formation",
            "Indicator",
            "Attribute",
            "Crop box number",
            "Variogram parameterzation",
            #   "Quality factor",
            #   "Identifier",
        ]
        self.responses = [
            col
            for col in self.dframe
            if col not in self.selectors
            and "cropbox" not in col
            and col != "Standard deviation"
        ]
        self.model_names = list(self.dframe["Delft3D model"].unique())


@CACHE.memoize(timeout=CACHE.TIMEOUT)
@webvizstore
def read_csv(csv_file: Path) -> pd.DataFrame:
    return pd.read_csv(csv_file)
