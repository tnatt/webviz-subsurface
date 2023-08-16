from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from dash import Dash, dcc
from webviz_config import WebvizConfigTheme, WebvizPluginABC, WebvizSettings

from webviz_subsurface._providers import Frequency
from webviz_subsurface._utils.ensemble_summary_provider_set_factory import (
    create_presampled_ensemble_summary_provider_set_from_paths,
)
from webviz_subsurface._utils.ensemble_table_provider_set_factory import (
    create_csvfile_providerset_from_paths,
)

from .controllers.property_delta_controller import property_delta_controller
from .controllers.property_qc_controller import property_qc_controller
from .controllers.property_response_controller import property_response_controller
from .models import PropertyStatisticsModel, ProviderTimeSeriesDataModel
from .utils.surface import generate_surface_table, get_path
from .views.main_view import main_view


class PropertyStatistics(WebvizPluginABC):
    """This plugin visualizes ensemble statistics calculated from grid properties.

---
**The main input to this plugin is property statistics extracted from grid models.
See the documentation in [fmu-tools](http://fmu-docs.equinor.com/) on how to generate this data.
Additional data includes UNSMRY data and optionally irap binary surfaces stored in standardized \
FMU format.


**Using raw ensemble data stored in realization folders**
* **`ensembles`:** Which ensembles in `shared_settings` to visualize.
* **`rel_file_pattern`:** path to `.arrow` files with summary data.
* **`statistic_file`:** Csv file for each realization with property statistics. See the \
    documentation in [fmu-tools](http://fmu-docs.equinor.com/) on how to generate this data.
* **`column_keys`:** List of vectors to extract. If not given, all vectors \
    from the simulations will be extracted. Wild card asterisk `*` can be used.
* **`time_index`:** Time separation between extracted values. Can be e.g. `monthly` (default) or \
    `yearly`.
* **`surface_renaming`:** Optional dictionary to rename properties/zones to match filenames \
    stored on FMU standardized format (zone--property.gri)

---

?> `Arrow` format for simulation time series data can be generated using the `ECL2CSV` forward \
model in ERT. On existing ensembles the command line tool `smry2arrow_batch` can be used to \
generate arrow files.

?> Folders with statistical surfaces are assumed located at \
`<ensemble_path>/share/results/maps/<ensemble>/<statistic>` where `statistic` are subfolders \
with statistical calculation: `mean`, `stddev`, `p10`, `p90`, `min`, `max`.

!> For smry data it is **strongly recommended** to keep the data frequency to a regular frequency \
(like `monthly` or `yearly`). This applies to both csv input and when reading from `UNSMRY` \
(controlled by the `sampling` key). This is because the statistics and fancharts are calculated \
per DATE over all realizations in an ensemble, and the available dates should therefore not \
differ between individual realizations of an ensemble.


"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        app: Dash,
        webviz_settings: WebvizSettings,
        ensembles: list,
        rel_file_pattern: str = "share/results/unsmry/*.arrow",
        statistics_file: str = "share/results/tables/gridpropstatistics.csv",
        surface_renaming: Optional[dict] = None,
        time_index: str = "monthly",
        column_keys: Optional[list] = None,
    ):
        super().__init__()
        self.theme: WebvizConfigTheme = webviz_settings.theme
        self._surface_folders: Union[dict, None] = None
        self._vmodel: Optional[ProviderTimeSeriesDataModel] = None

        ensemble_paths = {
            ensemble_name: webviz_settings.shared_settings["scratch_ensembles"][
                ensemble_name
            ]
            for ensemble_name in ensembles
        }
        resampling_frequency = Frequency(time_index)

        table_provider_set = create_csvfile_providerset_from_paths(
            ensemble_paths, statistics_file
        )
        property_df = table_provider_set.get_aggregated_dataframe()

        self._surface_folders = {
            ens: Path(ens_path.split("realization")[0]) / "share/results/maps" / ens
            for ens, ens_path in ensemble_paths.items()
        }
        try:
            smry_provider_set = (
                create_presampled_ensemble_summary_provider_set_from_paths(
                    ensemble_paths, rel_file_pattern, resampling_frequency
                )
            )
            self._vmodel = ProviderTimeSeriesDataModel(
                provider_set=smry_provider_set, column_keys=column_keys
            )
        except ValueError as err:
            print(err)
            self._vmodel = None

        self._pmodel = PropertyStatisticsModel(dataframe=property_df, theme=self.theme)

        self._surface_renaming = surface_renaming if surface_renaming else {}
        self._surface_table = generate_surface_table(
            zones=self._pmodel.zones,
            properties=self._pmodel.properties,
            ensembles=self._pmodel.ensembles,
            surface_folders=self._surface_folders,
            surface_renaming=self._surface_renaming,
        )
        self.set_callbacks(app)

    @property
    def layout(self) -> dcc.Tabs:
        return main_view(
            get_uuid=self.uuid,
            property_model=self._pmodel,
            surface_folders=self._surface_folders,
            vector_model=self._vmodel,
        )

    def set_callbacks(self, app: Dash) -> None:
        property_qc_controller(app=app, get_uuid=self.uuid, property_model=self._pmodel)
        if len(self._pmodel.ensembles) > 1:
            property_delta_controller(
                app=app,
                get_uuid=self.uuid,
                property_model=self._pmodel,
                surface_table=self._surface_table,
            )
        if self._vmodel is not None:
            property_response_controller(
                app=app,
                get_uuid=self.uuid,
                surface_table=self._surface_table,
                property_model=self._pmodel,
                timeseries_model=self._vmodel,
            )

    def add_webvizstore(self) -> List[Tuple[Callable, list]]:
        store: List[Tuple[Callable, list]] = [
            (
                generate_surface_table,
                [
                    {
                        "zones": self._pmodel.zones,
                        "properties": self._pmodel.properties,
                        "ensembles": self._pmodel.ensembles,
                        "surface_folders": self._surface_folders,
                        "surface_renaming": self._surface_renaming,
                    }
                ],
            )
        ]
        if self._surface_folders is not None:
            for path in self._surface_table["path"].unique():
                store.append((get_path, [{"path": Path(path)}]))
        return store
