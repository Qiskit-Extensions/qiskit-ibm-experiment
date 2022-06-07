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

import logging
import os
import uuid
from typing import List, Dict, Optional, Union
import pandas as pd
import numpy as np
import json
from qiskit_ibm_experiment.exceptions import IBMExperimentEntryNotFound, IBMExperimentEntryExists

logger = logging.getLogger(__name__)

class LocalExperimentClient():
    experiment_db_columns = [
        "type",
        "device_name",
        "extra",
        "experiment_id",
        "group_id",
        "hub_id",
        "jobs",
        "notes",
        "parent_experiment_uuid",
        "project_id",
        "start_time",
        "tags",
        "uuid",
        "visibility",
    ]
    results_db_columns =[
        "experiment_id",
        "result_data",
        "result_type",
        "device_components",
        "tags",
        "quality",
        "verified",
        "result_id",
        "chisq",
        "creation_datetime",
        "service",
        "backend_name",
    ]
    def __init__(self, main_dir) -> None:
        """ExperimentClient constructor.

        Args:
            access_token: The session's access token
            url: The session's base url
            additional_params: additional session parameters
        """
        self.set_paths(main_dir)
        self.create_directories()
        self.init_db()

    def set_paths(self, main_dir):
        self.main_dir = main_dir
        self.figures_dir = os.path.join(self.main_dir, 'figures')
        self.experiments_file = os.path.join(self.main_dir, 'experiments.json')
        self.results_file = os.path.join(self.main_dir, 'results.json')

    def create_directories(self):
        """Creates the directories needed for the DB if they do not exist"""
        dirs_to_create = [self.main_dir, self.figures_dir]
        for dir in dirs_to_create:
            if not os.path.exists(dir):
                os.makedirs(dir)

    def save(self):
        self.experiments.to_json(self.experiments_file)
        self.results.to_json(self.results_file)

    def serialize(self, df):
        result = df.replace({np.nan: None}).to_dict("records")[0]
        return json.dumps(result)

    def init_db(self):
        if os.path.exists(self.experiments_file):
            self.experiments = pd.read_json(self.experiments_file)
        else:
            self.experiments = pd.DataFrame(columns=self.experiment_db_columns)

        if os.path.exists(self.results_file):
            self.results = pd.read_json(self.results_file)
        else:
            self.results = pd.DataFrame(columns=self.results_db_columns)

        self.save()

    def devices(self) -> Dict:
        """Return the device list from the experiment DB."""
        pass

    def experiments(
        self,
        limit: Optional[int],
        marker: Optional[str],
        backend_name: Optional[str],
        experiment_type: Optional[str] = None,
        start_time: Optional[List] = None,
        device_components: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        hub: Optional[str] = None,
        group: Optional[str] = None,
        project: Optional[str] = None,
        exclude_public: Optional[bool] = False,
        public_only: Optional[bool] = False,
        exclude_mine: Optional[bool] = False,
        mine_only: Optional[bool] = False,
        parent_id: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> str:
        """Retrieve experiments, with optional filtering.

        Args:
            limit: Number of experiments to retrieve.
            marker: Marker used to indicate where to start the next query.
            backend_name: Name of the backend.
            experiment_type: Experiment type.
            start_time: A list of timestamps used to filter by experiment start time.
            device_components: A list of device components used for filtering.
            tags: Tags used for filtering.
            hub: Filter by hub.
            group: Filter by hub and group.
            project: Filter by hub, group, and project.
            exclude_public: Whether or not to exclude experiments with a public share level.
            public_only: Whether or not to only return experiments with a public share level.
            exclude_mine: Whether or not to exclude experiments where I am the owner.
            mine_only: Whether or not to only return experiments where I am the owner.
            parent_id: Filter by parent experiment ID.
            sort_by: Sorting order.

        Returns:
            A list of experiments and the marker, if applicable.
        """
        pass

    def experiment_get(self, experiment_id: str) -> str:
        """Get a specific experiment.

        Args:
            experiment_id: Experiment uuid.

        Returns:
            Experiment data.
        """
        exp = self.experiments.loc[self.experiments.uuid == experiment_id]
        if exp.empty:
            raise IBMExperimentEntryNotFound
        return self.serialize(exp)

    def experiment_upload(self, data: str) -> Dict:
        """Upload an experiment.

        Args:
            data: Experiment data.

        Returns:
            Experiment data.
        """
        data_dict = json.loads(data)
        if "uuid" not in data_dict:
            data_dict["uuid"] = str(uuid.uuid4())

        exp = self.experiments.loc[self.experiments.uuid == data_dict["uuid"]]
        if not exp.empty:
            raise IBMExperimentEntryExists

        new_df = pd.DataFrame([data_dict], columns=self.experiments.columns)
        self.experiments = pd.concat([self.experiments, new_df], ignore_index=True)
        self.save()
        return data_dict


    def experiment_update(self, experiment_id: str, new_data: str) -> Dict:
        """Update an experiment.

        Args:
            experiment_id: Experiment UUID.
            new_data: New experiment data.

        Returns:
            Experiment data.
        """
        pass


    def experiment_delete(self, experiment_id: str) -> Dict:
        """Delete an experiment.

        Args:
            experiment_id: Experiment UUID.

        Returns:
            JSON response.
        """
        self.experiments.drop(self.experiments.loc[self.experiments.uuid == experiment_id].index, inplace=True)


    def experiment_plot_upload(
        self,
        experiment_id: str,
        plot: Union[bytes, str],
        plot_name: str,
    ) -> Dict:
        """Upload an experiment plot.

        Args:
            experiment_id: Experiment UUID.
            plot: Plot file name or data to upload.
            plot_name: Name of the plot.

        Returns:
            JSON response.
        """
        pass


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
        """
        pass


    def experiment_plot_get(self, experiment_id: str, plot_name: str) -> bytes:
        """Retrieve an experiment plot.

        Args:
            experiment_id: Experiment UUID.
            plot_name: Name of the plot.

        Returns:
            Retrieved experiment plot.
        """
        pass


    def experiment_plot_delete(self, experiment_id: str, plot_file_name: str) -> None:
        """Delete an experiment plot.

        Args:
            experiment_id: Experiment UUID.
            plot_file_name: Plot file name.
        """
        pass


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
        """
        pass


    def analysis_result_create(self, result: str) -> Dict:
        """Upload an analysis result.

        Args:
            result: The analysis result to upload.

        Returns:
            Analysis result data.
        """
        pass


    def analysis_result_update(self, result_id: str, new_data: str) -> Dict:
        """Update an analysis result.

        Args:
            result_id: Analysis result ID.
            new_data: New analysis result data.

        Returns:
            Analysis result data.
        """
        pass


    def analysis_result_delete(self, result_id: str) -> Dict:
        """Delete an analysis result.

        Args:
            result_id: Analysis result ID.

        Returns:
            Analysis result data.
        """
        pass


    def analysis_result_get(self, result_id: str) -> str:
        """Retrieve an analysis result.

        Args:
            result_id: Analysis result ID.

        Returns:
            Analysis result data.
        """
        pass


    def device_components(self, backend_name: Optional[str]) -> List[Dict]:
        """Return device components for the backend.

        Args:
            backend_name: Name of the backend.

        Returns:
            A list of device components.
        """
        pass

