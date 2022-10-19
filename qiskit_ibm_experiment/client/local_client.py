# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Client for local Quantum experiment services."""

# pylint treats the dataframes as JsonReader for some reason
# pylint: disable=no-member

import logging
import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
import pandas as pd
import numpy as np

from qiskit_ibm_experiment.exceptions import (
    IBMExperimentEntryNotFound,
    IBMExperimentEntryExists,
    IBMApiError,
    RequestsApiError,
)

from qiskit_ibm_experiment.service.utils import str_to_utc

logger = logging.getLogger(__name__)


class LocalExperimentClient:
    """Client for locally performing database services."""

    experiment_db_columns = [
        "type",
        "device_name",
        "extra",
        "uuid",
        "parent_experiment_uuid",
        "hub_id",
        "group_id",
        "project_id",
        "experiment_id",
        "visibility",
        "tags",
        "jobs",
        "notes",
        "start_time",
        "end_time",
        "updated_at",
    ]
    results_db_columns = [
        "experiment_uuid",
        "device_components",
        "fit",
        "type",
        "tags",
        "quality",
        "verified",
        "uuid",
        "chisq",
        "device_name",
        "created_at",
        "updated_at",
    ]

    def __init__(self, main_dir: str = None, local_save: bool = None) -> None:
        """ExperimentClient constructor.

        Args:
            main_dir: The dir in which to place the db files and subdirs
            local_save: whether to store data to disk or not
        """
        self._experiments = pd.DataFrame()
        self._results = pd.DataFrame()
        self._figures = None
        self._files = None
        self._files_list = {}
        self._local_save = False
        if local_save and main_dir is not None:
            self._local_save = True
            self.set_paths(main_dir)
            self.create_directories()
        self.init_db()

    def set_paths(self, main_dir):
        """Creates the path to db files and directories"""
        self.main_dir = main_dir
        self.figures_dir = os.path.join(self.main_dir, "figures")
        self.files_dir = os.path.join(self.main_dir, "files")
        self.experiments_file = os.path.join(self.main_dir, "experiments.json")
        self.results_file = os.path.join(self.main_dir, "results.json")

    def create_directories(self):
        """Creates the directories needed for the DB if they do not exist"""
        dirs_to_create = [self.main_dir, self.figures_dir, self.files_dir]
        for dir_to_create in dirs_to_create:
            if not os.path.exists(dir_to_create):
                os.makedirs(dir_to_create, exist_ok=True)

    def save(self):
        """Saves the db to disk"""
        if self._local_save:
            self._experiments.to_json(self.experiments_file)
            self._results.to_json(self.results_file)
            self._save_figures()
            self._save_files()

    def _save_figures(self):
        """Saves the figures to disk"""
        for exp_id in self._figures:
            for figure_name, figure_data in self._figures[exp_id].items():
                filename = f"{exp_id}_{figure_name}"
                with open(os.path.join(self.figures_dir, filename), "wb") as file:
                    file.write(figure_data)

    def _save_files(self):
        """Saves the figures to disk"""
        for exp_id in self._files:
            for file_name, file_data in self._files[exp_id].items():
                filename = f"{exp_id}_{file_name}"
                with open(os.path.join(self.files_dir, filename), "w") as file:
                    file.write(file_data)

    def serialize(self, dataframe):
        """Serializes db values as JSON"""
        result = dataframe.replace({np.nan: None}).to_dict("records")[0]
        return json.dumps(result)

    def init_db(self):
        """Initializes the db"""
        if self._local_save:
            if os.path.exists(self.experiments_file):
                self._experiments = pd.read_json(self.experiments_file)
            else:
                self._experiments = pd.DataFrame(columns=self.experiment_db_columns)

            if os.path.exists(self.results_file):
                self._results = pd.read_json(self.results_file)
            else:
                self._results = pd.DataFrame(columns=self.results_db_columns)

            if os.path.exists(self.figures_dir):
                self._figures = self._get_figure_list()
            else:
                self._figures = {}
            if os.path.exists(self.files_dir):
                self._files, self._files_list = self._get_files()
            else:
                self._files = {}
        else:
            self._experiments = pd.DataFrame(columns=self.experiment_db_columns)
            self._results = pd.DataFrame(columns=self.results_db_columns)
            self._figures = {}
            self._files = {}

        self.save()

    def _get_figure_list(self):
        """Generates the figure dictionary based on stored data on disk"""
        figures = {}
        for exp_id in self._experiments.uuid:
            # exp_id should be str to begin with, so just in case
            exp_id_string = str(exp_id)
            figures_for_exp = {}
            for filename in os.listdir(self.figures_dir):
                if filename.startswith(exp_id_string):
                    with open(os.path.join(self.figures_dir, filename), "rb") as file:
                        figure_data = file.read()
                    figure_name = filename[len(exp_id_string) + 1 :]
                    figures_for_exp[figure_name] = figure_data
            figures[exp_id] = figures_for_exp
        return figures

    def _get_files(self):
        """Generates the figure dictionary based on stored data on disk"""
        files = {}
        files_list = {}
        for exp_id in self._experiments.uuid:
            # exp_id should be str to begin with, so just in case
            exp_id_string = str(exp_id)
            file_list_for_exp = []
            files_for_exp = {}
            for filename in os.listdir(self.files_dir):
                if filename.startswith(exp_id_string):
                    file_full_path = os.path.join(self.files_dir, filename)
                    with open(file_full_path, "r") as file:
                        file_data = file.read()
                    file_name = filename[len(exp_id_string) + 1 :]
                    files_for_exp[file_name] = file_data
                    new_file_element = {
                        "Key": file_name,
                        "Size": len(file_data),
                        "LastModified": os.path.getmtime(file_full_path),
                    }
                    file_list_for_exp.append(new_file_element)
            files_list[exp_id] = file_list_for_exp
            files[exp_id] = files_for_exp
        return files, files_list

    def devices(self) -> Dict:
        """Return the device list from the experiment DB."""
        pass

    def experiments(
        self,
        limit: Optional[int] = 10,
        device_components: Optional[Union[str, "DeviceComponent"]] = None,
        experiment_type: Optional[str] = None,
        backend_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        **filters: Any,
    ) -> str:
        """Retrieve experiments, with optional filtering.

        Args:
            limit: Number of experiments to retrieve.
            device_components: A list of device components used for filtering.
            experiment_type: Experiment type.
            backend_name: Name of the backend.
            tags: Tags used for filtering.
            parent_id: Filter by parent experiment ID.
            **filters: A set of additional filters/sorters for the results
            (currently only "start_time" and "sort_by")

        Returns:
            A list of experiments and the marker, if applicable.

        Raises:
            ValueError: If the parameters are unsuitable for filtering
        """
        df = self._experiments

        if experiment_type is not None:
            if experiment_type[:5] == "like:":
                experiment_type = experiment_type.split(":")[1]
                df = df.loc[df.type.str.contains(experiment_type)]
            else:
                df = df.loc[df.type == experiment_type]

        if backend_name is not None:
            df = df.loc[df.device_name == backend_name]

        # Note a bug in the interface for all services:
        # It is impossible to filter by experiments whose parent id is None
        # (i.e., root experiments)
        if parent_id is not None:
            df = df.loc[df.parent_experiment_uuid == parent_id]

        # Waiting for consistency between provider service and qiskit-experiments service,
        # currently they have different types for `device_components`
        if device_components is not None:
            raise ValueError(
                "The fake service currently does not support filtering on device components"
            )

        if tags is not None:
            if tags[:3] == "any":
                tags_list = tags[4:].split(",")
                df = df.loc[
                    df.tags.apply(lambda dftags: any(x in dftags for x in tags_list))
                ]
            elif tags[:8] == "contains":
                tags_list = tags[9:].split(",")
                df = df.loc[
                    df.tags.apply(lambda dftags: all(x in dftags for x in tags_list))
                ]
            else:
                raise ValueError("Unrecognized tags operator")

        start_datetime_before = None
        start_datetime_after = None
        if "start_time" in filters:
            for start_time_string in filters["start_time"]:
                string_type = start_time_string[:2]
                value = str_to_utc(start_time_string[3:])
                if string_type == "ge":
                    start_datetime_after = value
                if string_type == "le":
                    start_datetime_before = value

        if start_datetime_before is not None:
            df = df.loc[df.start_time.apply(str_to_utc) <= start_datetime_before]
        if start_datetime_after is not None:
            df = df.loc[df.start_time.apply(str_to_utc) >= start_datetime_after]

        sort_by = filters.get("sort_by")
        if sort_by is None:
            sort_by = "start_time:desc"
        sort_by += ",uuid:asc"
        sort_by = sort_by.split(",")

        sort_by_columns = []
        sort_by_ascending = []
        for sort_by_element in sort_by:
            sortby_split = sort_by_element.split(":")
            if len(sortby_split) != 2 or (
                sortby_split[1] != "asc" and sortby_split[1] != "desc"
            ):
                raise ValueError(f"Sortby filter {sort_by} is malformed")
            sort_by_columns.append(sortby_split[0])
            sort_by_ascending.append(sortby_split[1] == "asc")

        df = df.sort_values(sort_by_columns, ascending=sort_by_ascending)
        df = df.iloc[:limit]
        result = {"experiments": df.replace({np.nan: None}).to_dict("records")}
        return json.dumps(result)

    def experiment_get(self, experiment_id: str) -> str:
        """Get a specific experiment.

        Args:
            experiment_id: Experiment uuid.

        Returns:
            Experiment data.

        Raises:
            IBMExperimentEntryNotFound: If the experiment is not found
        """
        exp = self._experiments.loc[self._experiments.uuid == experiment_id]
        if exp.empty:
            raise IBMExperimentEntryNotFound
        return self.serialize(exp)

    def experiment_upload(self, data: str) -> Dict:
        """Upload an experiment.

        Args:
            data: Experiment data.

        Returns:
            Experiment data.

        Raises:
            IBMExperimentEntryExists: If the experiment already exists

        """
        data_dict = json.loads(data)
        if "uuid" not in data_dict:
            data_dict["uuid"] = str(uuid.uuid4())
        if "start_time" not in data_dict:
            data_dict["start_time"] = str(datetime.now())
        if "tags" not in data_dict:
            data_dict["tags"] = []
        exp = self._experiments.loc[self._experiments.uuid == data_dict["uuid"]]
        if not exp.empty:
            raise IBMExperimentEntryExists

        new_df = pd.DataFrame([data_dict], columns=self._experiments.columns)
        self._experiments = pd.concat([self._experiments, new_df], ignore_index=True)
        self.save()
        return data_dict

    def experiment_update(self, experiment_id: str, new_data: str) -> Dict:
        """Update an experiment.

        Args:
            experiment_id: Experiment UUID.
            new_data: New experiment data.

        Returns:
            Experiment data.

        Raises:
            IBMExperimentEntryNotFound: If the experiment is not found
        """
        exp = self._experiments.loc[self._experiments.uuid == experiment_id]
        if exp.empty:
            raise IBMExperimentEntryNotFound
        exp_index = exp.index[0]
        new_data_dict = json.loads(new_data)
        for key, value in new_data_dict.items():
            self._experiments.at[exp_index, key] = value
        self.save()
        exp = self._experiments.loc[self._experiments.uuid == experiment_id]
        return self.serialize(exp)

    def experiment_delete(self, experiment_id: str) -> Dict:
        """Delete an experiment.

        Args:
            experiment_id: Experiment UUID.

        Returns:
            JSON response.

        Raises:
            IBMExperimentEntryNotFound: If the experiment is not found
        """
        exp = self._experiments.loc[self._experiments.uuid == experiment_id]
        if exp.empty:
            raise IBMExperimentEntryNotFound
        self._experiments.drop(
            self._experiments.loc[self._experiments.uuid == experiment_id].index,
            inplace=True,
        )
        self.save()
        return self.serialize(exp)

    def experiment_plot_upload(
        self,
        experiment_id: str,
        plot: Union[bytes, str],
        plot_name: str,
    ) -> bool:
        """Upload an experiment plot.

        Args:
            experiment_id: Experiment UUID.
            plot: Plot file name or data to upload.
            plot_name: Name of the plot.

        Returns:
            Whether the upload succeeded

        Raises:
            RequestsApiError: If the figure already exists
        """
        if experiment_id not in self._figures:
            self._figures[experiment_id] = {}
        exp_figures = self._figures[experiment_id]
        if plot_name in exp_figures:
            raise RequestsApiError(
                f"Figure {plot_name} already exists", status_code=409
            )
        exp_figures[plot_name] = plot
        self.save()
        return True

    def experiment_plot_update(
        self,
        experiment_id: str,
        plot: Union[bytes, str],
        plot_name: str,
    ) -> Dict:
        """Update an experiment plot.

        Args:
            experiment_id: Experiment UUID.
            plot: Plot file name or data to upload.
            plot_name: Name of the plot.

        Returns:
            JSON response.

        Raises:
            RequestsApiError: If the figure is not found
        """
        exp_figures = self._figures[experiment_id]
        if plot_name not in exp_figures:
            raise RequestsApiError(f"Figure {plot_name} not found", status_code=404)
        exp_figures[plot_name] = plot
        self.save()
        return json.dumps({"name": plot_name, "size": len(plot)})

    def experiment_plot_get(self, experiment_id: str, plot_name: str) -> bytes:
        """Retrieve an experiment plot.

        Args:
            experiment_id: Experiment UUID.
            plot_name: Name of the plot.

        Returns:
            Retrieved experiment plot.

        Raises:
            RequestsApiError: If the figure is not found
        """

        exp_figures = self._figures[experiment_id]
        if plot_name not in exp_figures:
            raise RequestsApiError(f"Figure {plot_name} not found", status_code=404)
        return exp_figures[plot_name]

    def experiment_plot_delete(self, experiment_id: str, plot_name: str) -> None:
        """Delete an experiment plot.

        Args:
            experiment_id: Experiment UUID.
            plot_name: Plot file name.

        Raises:
            RequestsApiError: If the figure is not found
        """
        exp_figures = self._figures[experiment_id]
        if plot_name not in exp_figures:
            raise RequestsApiError(f"Figure {plot_name} not found", status_code=404)
        del exp_figures[plot_name]

    def experiment_devices(self) -> List:
        """Return list of experiment devices.

        Returns:
            A list of experiment devices.
        """
        pass

    def analysis_results(
        self,
        limit: Optional[int],
        marker: Optional[str],
        backend_name: Optional[str] = None,
        device_components: Optional[List[str]] = None,
        experiment_uuid: Optional[str] = None,
        result_type: Optional[str] = None,
        quality: Optional[Union[str, List[str]]] = None,
        verified: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        created_at: Optional[List] = None,
        sort_by: Optional[str] = None,
    ) -> str:
        """Return a list of analysis results.

        Args:
            limit: Number of analysis results to retrieve.
            marker: Marker used to indicate where to start the next query.
            backend_name: Name of the backend.
            device_components: A list of device components used for filtering.
            experiment_uuid: Experiment UUID used for filtering.
            result_type: Analysis result type used for filtering.
            quality: Quality value used for filtering.
            verified: Indicates whether this result has been verified.
            tags: Filter by tags assigned to analysis results.
            created_at: A list of timestamps used to filter by creation time.
            sort_by: Indicates how the output should be sorted.

        Returns:
            A list of analysis results and the marker, if applicable.
        Raises:
            ValueError: If the parameters are unsuitable for filtering
        """
        # pylint: disable=unused-argument
        df = self._results

        # TODO: skipping device components for now until we conslidate more with the provider service
        # (in the qiskit-experiments service there is no operator for device components,
        # so the specification for filtering is not clearly defined)

        if experiment_uuid is not None:
            df = df.loc[df.experiment_uuid == experiment_uuid]
        if result_type is not None:
            if result_type[:5] == "like:":
                result_type = result_type.split(":")[1]
                df = df.loc[df.type.str.contains(result_type)]
            else:
                df = df.loc[df.type == result_type]
        if backend_name is not None:
            df = df.loc[df.backend_name == backend_name]
        if quality is not None:
            df = df.loc[df.quality == quality]
        if verified is not None:
            df = df.loc[df.verified == verified]

        if tags is not None:
            operator, tags = tags.split(":")
            tags = tags.split(",")
            if operator == "any:":  # OR operator
                df = df.loc[
                    df.tags.apply(lambda dftags: any(x in dftags for x in tags))
                ]
            elif operator == "AND":
                df = df.loc[
                    df.tags.apply(lambda dftags: all(x in dftags for x in tags))
                ]
            else:
                raise ValueError(f"Unrecognized tags operator {operator}")

        if sort_by is None:
            sort_by = "creation_datetime:desc"

        if not isinstance(sort_by, list):
            sort_by = [sort_by]

        # TODO: support also device components and result type
        if len(sort_by) != 1:
            raise ValueError(
                "The fake service currently supports only sorting by creation_datetime"
            )

        sortby_split = sort_by[0].split(":")
        # TODO: support also device components and result type
        if (
            len(sortby_split) != 2
            or sortby_split[0] != "creation_datetime"
            or (sortby_split[1] != "asc" and sortby_split[1] != "desc")
        ):
            raise ValueError(
                "The fake service currently supports only sorting by creation_datetime, "
                "which can be either asc or desc"
            )

        df = df.sort_values(
            ["created_at", "uuid"], ascending=[(sortby_split[1] == "asc"), True]
        )

        df = df.iloc[:limit]
        result = {"analysis_results": df.replace({np.nan: None}).to_dict("records")}
        return json.dumps(result)

    def analysis_result_create(self, result: str) -> Dict:
        """Upload an analysis result.

        Args:
            result: The analysis result to upload.

        Returns:
            Analysis result data.

        Raises:
            RequestsApiError: If experiment id is missing
        """
        data_dict = json.loads(result)
        exp_id = data_dict.get("experiment_uuid")
        if exp_id is None:
            raise RequestsApiError(
                "Cannot create analysis result without experiment id"
            )
        exp = self._experiments.loc[self._experiments.uuid == exp_id]
        if exp.empty:
            raise RequestsApiError(f"Experiment {exp_id} not found", status_code=404)
        exp_index = exp.index[0]
        data_dict["device_name"] = self._experiments.at[exp_index, "device_name"]
        if "uuid" not in data_dict:
            data_dict["uuid"] = str(uuid.uuid4())

        new_df = pd.DataFrame([data_dict], columns=self._results.columns)
        self._results = pd.concat([self._results, new_df], ignore_index=True)
        self.save()
        return data_dict

    def analysis_result_update(self, result_id: str, new_data: str) -> Dict:
        """Update an analysis result.

        Args:
            result_id: Analysis result ID.
            new_data: New analysis result data.

        Returns:
            Analysis result data.

        Raises:
            IBMExperimentEntryNotFound: If the analysis result is not found
        """
        result = self._results.loc[self._results.uuid == result_id]
        if result.empty:
            raise IBMExperimentEntryNotFound
        result_index = result.index[0]
        new_data_dict = json.loads(new_data)
        for key, value in new_data_dict.items():
            self._results.at[result_index, key] = value
        self.save()
        result = self._results.loc[self._results.uuid == result_id]
        return self.serialize(result)

    def bulk_analysis_result_update(self, new_data: str) -> Dict:
        """Bulk update analysis results.

        Args:
            new_data: New analysis result data array.

        Returns:
            Analysis result data.

        Raises:
            IBMExperimentEntryNotFound: If at least one analysis result is not found
            IBMApiError: If the input is not given in the expected format
        """

        # naive implementation, can be optimized if needed
        new_data_dict = json.loads(new_data)
        # expected format is {"analysis_results": [...]}
        if "analysis_results" not in new_data_dict or not isinstance(
            new_data_dict["analysis_results"], list
        ):
            raise IBMApiError(
                'Data not given in the correct bulk update format, pass {"analysis_results": [...]}'
            )
        response = {"analysis_results": []}
        for new_analysis_result in new_data_dict["analysis_results"]:
            result = self.analysis_result_update(
                new_analysis_result["uuid"], json.dumps(new_analysis_result)
            )
            response["analysis_results"].append(result)
        return response

    def analysis_result_delete(self, result_id: str) -> Dict:
        """Delete an analysis result.

        Args:
            result_id: Analysis result ID.

        Returns:
            Analysis result data.

        Raises:
            IBMExperimentEntryNotFound: If the analysis result is not found
        """
        result = self._results.loc[self._results.uuid == result_id]
        if result.empty:
            raise IBMExperimentEntryNotFound
        self._results.drop(
            self._results.loc[self._results.uuid == result_id].index, inplace=True
        )
        self.save()
        return self.serialize(result)

    def analysis_result_get(self, result_id: str) -> str:
        """Retrieve an analysis result.

        Args:
            result_id: Analysis result ID.

        Returns:
            Analysis result data.
        Raises:
            IBMExperimentEntryNotFound: If the analysis result is not found
        """
        result = self._results.loc[self._results.uuid == result_id]
        if result.empty:
            raise IBMExperimentEntryNotFound
        return self.serialize(result)

    def device_components(self, backend_name: Optional[str]) -> List[Dict]:
        """Return device components for the backend.

        Args:
            backend_name: Name of the backend.

        Returns:
            A list of device components.
        """
        pass

    def experiment_files_get(self, experiment_id: str) -> str:
        """Retrieve experiment related files.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Experiment files.
        """
        return {"files": self._files_list.get(experiment_id, [])}

    def experiment_file_upload(
        self, experiment_id: str, file_name: str, file_data: str
    ):
        """Uploads a data file to the DB

        Args:
            experiment_id: Experiment ID.
            file_name: The intended name of the data file
            file_data: The contents of the data file
        """
        if experiment_id not in self._files_list:
            self._files_list[experiment_id] = []
        if experiment_id not in self._files:
            self._files[experiment_id] = {}
        new_file_element = {
            "Key": file_name,
            "Size": len(file_data),
            "LastModified": str(datetime.now()),
        }
        self._files_list[experiment_id].append(new_file_element)
        self._files[experiment_id][file_name] = file_data
        self.save()

    def experiment_file_download(self, experiment_id: str, file_name: str) -> Dict:
        """Downloads a data file from the DB

        Args:
            experiment_id: Experiment ID.
            file_name: The name of the data file

        Returns:
            The Dictionary of contents of the file

        Raises:
            IBMExperimentEntryNotFound: if experiment or file not found
        """
        if experiment_id not in self._files:
            raise IBMExperimentEntryNotFound
        if file_name not in self._files[experiment_id]:
            raise IBMExperimentEntryNotFound
        return json.loads(self._files[experiment_id][file_name])
