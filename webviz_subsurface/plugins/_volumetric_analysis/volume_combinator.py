from typing import List
from pathlib import Path
import warnings
import pandas as pd
import fmu.tools.fipmapper.fipmapper as fipmapper


class VolumeCombinator:
    def __init__(self, volumes_table: pd.DataFrame, fipfile: Path = None):
        self.disjoint_set_df = (
            fipmapper.FipMapper(yamlfile=fipfile).disjoint_sets() if fipfile else None
        )
        self.dframe = self.combine_sources(volumes_table)

    def combine_sources(self, volumes_table) -> pd.DataFrame:
        dfs = []
        all_columns = set()
        for _, data in volumes_table.groupby("SOURCE"):
            data = data.dropna(axis=1, how="all")
            all_columns.update(data.columns)
            dfs.append(data)

        if self.disjoint_set_df is not None:
            df = self.create_set_dframe(
                disjoint_sets_df=self.disjoint_set_df, volume_dfs=dfs
            )
        else:
            df = pd.concat(dfs, join="inner", ignore_index=True)

        missing_columns = [col for col in all_columns if col not in df.columns]
        if missing_columns:
            warnings.warn(
                f"Skipping volumetric columns: {missing_columns} as they are not present in all "
                "volumetric sources"
            )
        return df

    def create_set_dframe(
        self, disjoint_sets_df: pd.DataFrame, volume_dfs: List[pd.DataFrame]
    ) -> pd.DataFrame:
        """Sum Eclipse and RMS volumetrics over the common disjoints sets."""
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
                set_df["SET"] = str(set_idx)
                set_df["SOURCE"] = source
                set_data_list.append(set_df)

        return pd.concat(set_data_list, join="inner", ignore_index=True)
