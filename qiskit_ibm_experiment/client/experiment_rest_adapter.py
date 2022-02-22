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

"""Experiment REST adapter."""

import logging
from typing import Dict, List, Any, Union, Optional
import json

logger = logging.getLogger(__name__)


from qiskit_ibm_experiment.client.session import RetrySession


class ExperimentRestAdapter:
    """REST adapter for experiment result DB"""

    URL_MAP = {
        'devices': '/devices',
        'experiment': '/experiments/{uuid}',
        'experiments': '/experiments',
        'analysis_results': '/analysis_results',
        'analysis_result': '/analysis_results/{result_id}',
    }

    _HEADER_JSON_CONTENT = {"Content-Type": "application/json"}
    _DEFAULT_URL_BASE = "https://api.quantum-computing.ibm.com/resultsdb"

    def __init__(self, session: RetrySession, prefix_url: str = "") -> None:
        """ExperimentRestAdapter constructor.

        Args:
            session: Session to be used in the adapter.
            prefix_url: String to be prepend to all URLs.
        """
        self.session = session
        self.prefix_url = prefix_url

    def get_url(self, identifier: str) -> str:
        """Return the resolved URL for the specified identifier.

        Args:
            identifier: Internal identifier of the endpoint.

        Returns:
            The resolved URL of the endpoint (relative to the session base URL).
        """
        return self.prefix_url + self.URL_MAP[identifier]

    def devices(self):
        url = self.get_url('devices')
        raw_data = self.session.get(url).json()
        return raw_data

    def experiment(self, experiment_id):
        url = self.get_url('experiment')
        url = url.format(uuid = experiment_id)
        # to enable custom JSON decoding request text, not json
        return self.session.get(url).text

    def experiments(
            self,
            limit: Optional[int],
            marker: Optional[str],
            backend_name: Optional[str] = None,
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
            sort_by: Optional[str] = None
    ) -> str:
        """Return experiment data.

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
            Response text.
        """
        url = self.get_url('experiments')
        params = {}  # type: Dict[str, Any]
        if backend_name:
            params['device_name'] = backend_name
        if experiment_type:
            params['type'] = experiment_type
        if start_time:
            params['start_time'] = start_time
        if device_components:
            params['device_components'] = device_components
        if tags:
            params['tags'] = tags
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        if hub:
            params['hub_id'] = hub
        if group:
            params['group_id'] = group
        if project:
            params['project_id'] = project
        if parent_id:
            params['parent_experiment_uuid'] = parent_id
        if exclude_public:
            params['visibility'] = '!public'
        elif public_only:
            params['visibility'] = 'public'
        if exclude_mine:
            params['owner'] = '!me'
        elif mine_only:
            params['owner'] = 'me'
        if sort_by:
            params['sort'] = sort_by

        return self.session.get(url, params=params).text

    def analysis_results(
            self,
            limit: Optional[int],
            marker: Optional[str],
            backend_name: Optional[str] = None,
            device_components: Optional[Union[str, List[str]]] = None,
            experiment_uuid: Optional[str] = None,
            result_type: Optional[str] = None,
            quality: Optional[List[str]] = None,
            verified: Optional[bool] = None,
            tags: Optional[List[str]] = None,
            created_at: Optional[List] = None,
            sort_by: Optional[str] = None
    ) -> str:
        """Return all analysis results.

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
            Server response.
        """
        url = self.get_url('analysis_results')
        params = {}  # type: Dict[str, Any]
        if backend_name:
            params['device_name'] = backend_name
        if device_components:
            params['device_components'] = device_components
        if experiment_uuid:
            params['experiment_uuid'] = experiment_uuid
        if quality:
            params['quality'] = quality
        if result_type:
            params['type'] = result_type
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        if verified is not None:
            params["verified"] = "true" if verified else "false"
        if tags:
            params['tags'] = tags
        if created_at:
            params['created_at'] = created_at
        if sort_by:
            params['sort'] = sort_by
        return self.session.get(url, params=params).text

    def analysis_result(self, result_id):
        """Return an analysis result.

        Args:
            analysis_result_id: UUID of the analysis result.

        Returns:
            The analysis result .
        """
        url = self.get_url('analysis_result')
        url = url.format(result_id=result_id)
        return self.session.get(url).text

    def experiment_upload(self, experiment: str) -> Dict:
        """Upload an experiment.

        Args:
            experiment: The experiment data to upload.

        Returns:
            JSON response.
        """
        url = self.get_url('experiments')
        raw_data = self.session.post(url, data=experiment,
                                     headers=self._HEADER_JSON_CONTENT).json()
        return raw_data

    def experiment_delete(self, experiment_id: str) -> Dict:
        """Delete an experiment.

        Args:
            experiment_id: Experiment UUID.

        Returns:
            JSON response.
        """
        url = self.get_url('experiment')
        url = url.format(uuid=experiment_id)
        return self.session.delete(url).json()

    def experiment_update(self, experiment_id: str, new_data: str) -> Dict:
        """Update the experiment.

        Args:
            experiment_id: Id of the experiment to update.
            new_data: The data to add to the experiment

        Returns:
            JSON response.
        """
        url = self.get_url('experiment')
        url = url.format(uuid=experiment_id)
        return self.session.put(url, data=new_data,
                                headers=self._HEADER_JSON_CONTENT).json()