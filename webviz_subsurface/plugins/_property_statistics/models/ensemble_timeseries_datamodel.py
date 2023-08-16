import datetime
import fnmatch
import re
from typing import List, Optional

import pandas as pd

from webviz_subsurface._abbreviations.reservoir_simulation import historical_vector
from webviz_subsurface._utils.ensemble_summary_provider_set import (
    EnsembleSummaryProviderSet,
)
from webviz_subsurface._utils.simulation_timeseries import (
    set_simulation_line_shape_fallback,
)
from webviz_subsurface._utils.vector_selector import add_vector_to_vector_selector_data


class ProviderTimeSeriesDataModel:
    """Class to process and and visualize ensemble timeseries"""

    def __init__(
        self,
        provider_set: EnsembleSummaryProviderSet,
        column_keys: Optional[list] = None,
    ) -> None:
        self._provider_set = provider_set
        self.line_shape_fallback = set_simulation_line_shape_fallback("linear")
        all_vector_names = provider_set._all_vector_names
        self._vector_names = (
            self.filter_vectorlist_on_column_keys(column_keys, all_vector_names)
            if column_keys is not None
            else all_vector_names
        )
        if not self._vector_names:
            raise ValueError("No vectors match the selected 'column_keys' criteria")

        self._dates = provider_set.all_dates(None)

        # add vectors to vector selector
        self.vector_selector_data: list = []
        for vector in self.get_non_historical_vector_names():
            add_vector_to_vector_selector_data(self.vector_selector_data, vector)

    @property
    def vectors(self) -> List[str]:
        return self._vector_names

    @property
    def dates(self) -> List[datetime.datetime]:
        return self._dates

    def get_non_historical_vector_names(self) -> list:
        return [
            vector
            for vector in self._vector_names
            if historical_vector(vector, None, False) not in self._vector_names
        ]

    @staticmethod
    def filter_vectorlist_on_column_keys(
        column_key_list: list, vectorlist: list
    ) -> list:
        """Filter vectors using list of unix shell wildcards"""
        try:
            regex = re.compile(
                "|".join([fnmatch.translate(col) for col in column_key_list]),
                flags=re.IGNORECASE,
            )
            return [v for v in vectorlist if regex.fullmatch(v)]
        except re.error:
            return []

    def get_historical_vector_df(
        self, vector: str, ensemble: str
    ) -> Optional[pd.DataFrame]:
        hist_vecname = historical_vector(vector, smry_meta=None)

        if hist_vecname and hist_vecname in self.vectors:
            provider = self._provider_set.provider(ensemble)
            return provider.get_vectors_df(
                [hist_vecname], None, realizations=provider.realizations()[:1]
            ).rename(columns={hist_vecname: vector})
        return None

    def get_vector_df(
        self,
        ensemble: str,
        realizations: List[int],
        vectors: List[str],
    ) -> pd.DataFrame:
        provider = self._provider_set.provider(ensemble)
        ens_vectors = [vec for vec in vectors if vec in provider.vector_names()]
        return provider.get_vectors_df(ens_vectors, None, realizations)

    def get_last_date(self, ensemble: str) -> datetime.datetime:
        return max(self._provider_set.provider(ensemble).dates(None))
