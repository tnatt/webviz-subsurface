from typing import List
from pathlib import Path
import warnings
import pandas as pd
import fmu.tools.fipmapper.fipmapper as fipmapper


class VolumeValidatorAndCombinator:
    """
    Class to validate volumetric dataframes based on their type (static/dynamic),
    and to ensure correct format of combined volumetric dataframe before initialization
    of an InplaceVolumesModel instance.

    A best guess of what volume type each source is are made based on available columns.

    The class works also as a combinator of dynamic and static sources by utilizing the
    FipMapper from fmu.tools for creating sets that are comparable in volumes. If a fipfile
    with FIPNUM to REGION∕ZONE mapping information is provided the volumes will be combined
    per set. Only region selectors FIPNUM/REGION∕ZONE which are unique whithin each set are
    kept in the resulting dataframe, if none meets the criteria SET is used.

    Validation steps:
    1. Static dataframes must follow a strict format to fit the data processing steps of the
       InplaceVolumesModel instance, all custom columns will be dropped.
    2. Dynamic dataframes must contain a FIPNUM column but custom columns are allowed.
    3. The combinator will only keep common columns between the different volumetric sources.
    4. Set volume_type based on what sources are available (static/dynamic/mixed).

    """

    ENSEMBLE_COLUMNS = ["ENSEMBLE", "REAL", "SOURCE"]
    VALID_STATIC_SELECTORS = ["ZONE", "REGION", "FACIES", "LICENSE"]
    VALID_STATIC_RESPONSES = [
        "BULK",
        "NET",
        "PORV",
        "HCPV",
        "GIIP",
        "STOIIP",
        "ASSOCIATEDOIL",
        "ASSOCIATEDGAS",
    ]
    FLUID_TYPES = ["TOTAL", "GAS", "OIL"]

    def __init__(self, volumes_table: pd.DataFrame, fipfile: Path = None):

        self.volume_sources = {"static": [], "dynamic": []}
        self.disjoint_set_df = (
            fipmapper.FipMapper(yamlfile=fipfile).disjoint_sets() if fipfile else None
        )
        self.dframe = self.validate_and_combine_sources(volumes_table)
        self.volume_type = self.set_volumetric_type()

    @property
    def possible_static_columns(self) -> list:
        possible_static_columns = self.VALID_STATIC_SELECTORS + self.ENSEMBLE_COLUMNS
        for fluid in self.FLUID_TYPES:
            possible_static_columns.extend(
                [f"{col}_{fluid}" for col in self.VALID_STATIC_RESPONSES]
            )
        return possible_static_columns

    def pore_to_porv_mapping(self, dframe: pd.DataFrame) -> pd.DataFrame:
        """Rename PORE columns to PORV (PORE will be deprecated..)"""
        return dframe.rename(
            columns={f"PORE_{fluid}": f"PORV_{fluid}" for fluid in self.FLUID_TYPES},
            errors="ignore",
        )

    def validate_and_combine_sources(self, volumes_table: pd.DataFrame) -> pd.DataFrame:
        """
        Validate columns for each volumetric source and combine them. Only common columns
        are kept. If a fipfile is provided volumes are summed per disjoint_set.
        """
        dfs = []
        all_columns = set()
        for src, voldf in volumes_table.groupby("SOURCE"):
            voldf = voldf.dropna(axis=1, how="all")
            voldf = self.pore_to_porv_mapping(voldf)
            self.set_volume_source_and_validate(voldf.columns, src)
            all_columns.update(voldf.columns)
            dfs.append(voldf)

        if self.disjoint_set_df is not None:
            dframe = self.create_set_dframe(
                disjoint_sets_df=self.disjoint_set_df, volume_dfs=dfs
            )
        else:
            dframe = pd.concat(dfs, join="inner", ignore_index=True)

        missing_columns = [col for col in all_columns if col not in dframe]
        if missing_columns:
            warnings.warn(
                f"Skipping volumetric columns: {missing_columns} as they are not present in all "
                "volumetric sources"
            )
        return dframe

    def set_volumetric_type(self) -> str:
        """Return volumetric type based on available volume sources"""
        if self.volume_sources["static"] and self.volume_sources["dynamic"]:
            return "mixed"
        return "static" if self.volume_sources["static"] else "dynamic"

    def set_volume_source_and_validate(self, columns: list, source: str) -> None:
        """
        Set volume type (stativ/dynamic) based on columns and validate columns
        based on type.
        """
        static_selectors_present = any(
            col in self.VALID_STATIC_SELECTORS for col in columns
        )
        non_static_columns = [
            col for col in columns if col not in self.possible_static_columns
        ]
        # Guess volume type based on columns
        if "FIPNUM" in columns:
            self.volume_sources["dynamic"].append(source)
        else:
            if not non_static_columns:
                if not static_selectors_present:
                    raise ValueError(
                        f"Static volume {source} provided with no valid selectors. "
                        f"One of {self.VALID_STATIC_SELECTORS} must be provided."
                    )
                self.volume_sources["static"].append(source)
            else:
                if static_selectors_present:
                    warnings.warn(
                        f"The volumetric source {source} is considered a dynamic source due "
                        f"to the presence of columns: {non_static_columns}. "
                        "If this is a static source remove these columns from the input to "
                        "trigger correct plugin mode."
                    )
                    self.volume_sources["dynamic"].append(source)

    def create_set_dframe(
        self, disjoint_sets_df: pd.DataFrame, volume_dfs: List[pd.DataFrame]
    ) -> pd.DataFrame:
        """Sum Eclipse and RMS volumetrics over the common disjoints sets."""

        region_selectors = find_region_selectors(disjoint_sets_df)
        set_data_list = []
        for set_idx, df in disjoint_sets_df.groupby(["SET"]):
            for voldf in volume_dfs:
                source = voldf["SOURCE"].unique()[0]
                if "FIPNUM" in voldf.columns:
                    filtered_df = voldf[voldf["FIPNUM"].isin(df["FIPNUM"].unique())]
                elif "ZONE" in voldf.columns and "REGION" in voldf.columns:
                    filtered_df = voldf[
                        (voldf["REGION"].isin(df["REGION"].unique()))
                        & (voldf["ZONE"].isin(df["ZONE"].unique()))
                    ]
                else:
                    raise ValueError(
                        f"Fipfile is provided but volumetric source {source} is missing "
                        "ZONE/REGION or FIPNUM definition."
                    )

                set_df = (
                    filtered_df.groupby(["ENSEMBLE", "REAL"])
                    .sum()
                    .reset_index()
                    .drop(labels=["FIPNUM", "REGION", "ZONE"], errors="ignore")
                )
                for col in region_selectors:
                    set_df[col] = df[col].iloc[0] if col != "SET" else set_idx
                set_df["SOURCE"] = source
                set_data_list.append(set_df)

        return pd.concat(set_data_list, join="inner", ignore_index=True)


def find_region_selectors(disjoint_sets_df):
    """Return region selectors that has a unique value
    per set. If none is found SET is used"""
    df = disjoint_sets_df.groupby(["SET"]).nunique()
    regcols = ["FIPNUM", "REGION", "ZONE"]
    if any((df[x] == 1).all() for x in regcols):
        return [x for x in regcols if (df[x] == 1).all()]
    return ["SET"]
