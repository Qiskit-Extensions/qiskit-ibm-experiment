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
from qiskit_ibm_experiment.client.session import RetrySession

logger = logging.getLogger(__name__)


class ExperimentRestAdapter:
    """REST adapter for experiment result DB"""

    URL_MAP = {
        "devices": "/devices",
        "device_components": "/device_components",
        "experiment": "/experiments/{uuid}",
        "experiments": "/experiments",
        "analysis_results": "/analysis_results",
        "analysis_result": "/analysis_results/{uuid}",
        "bulk_update_analysis_results": "/analysis_results/bulkupdate",
        "plot": "/experiments/{uuid}/plots/{name}",
        "plot_upload": "/experiments/{uuid}/plots/upload/{name}",
        "files": "/experiments/{uuid}/files",
        "files_upload": "/experiments/{uuid}/files/upload/{path}",
        "files_download": "/experiments/{uuid}/files/{path}",
    }

    _HEADER_JSON_CONTENT = {"Content-Type": "application/json"}

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
        """Return the device list from the experiment DB."""
        url = self.get_url("devices")
        raw_data = self.session.get(url).json()
        return raw_data

    def experiment(self, experiment_id):
        """Return the experiment list from the experiment DB."""
        url = self.get_url("experiment")
        url = url.format(uuid=experiment_id)
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
        sort_by: Optional[str] = None,
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
        url = self.get_url("experiments")
        params = {}  # type: Dict[str, Any]
        if backend_name:
            params["device_name"] = backend_name
        if experiment_type:
            params["type"] = experiment_type
        if start_time:
            params["start_time"] = start_time
        if device_components:
            params["device_components"] = device_components
        if tags:
            params["tags"] = tags
        if limit:
            params["limit"] = limit
        if marker:
            params["marker"] = marker
        if hub:
            params["hub_id"] = hub
        if group:
            params["group_id"] = group
        if project:
            params["project_id"] = project
        if parent_id:
            params["parent_experiment_uuid"] = parent_id
        if exclude_public:
            params["visibility"] = "!public"
        elif public_only:
            params["visibility"] = "public"
        if exclude_mine:
            params["owner"] = "!me"
        elif mine_only:
            params["owner"] = "me"
        if sort_by:
            params["sort"] = sort_by

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
        sort_by: Optional[str] = None,
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
        url = self.get_url("analysis_results")
        params = {}  # type: Dict[str, Any]
        if backend_name:
            params["device_name"] = backend_name
        if device_components:
            params["device_components"] = device_components
        if experiment_uuid:
            params["experiment_uuid"] = experiment_uuid
        if quality:
            params["quality"] = quality
        if result_type:
            params["type"] = result_type
        if limit:
            params["limit"] = limit
        if marker:
            params["marker"] = marker
        if verified is not None:
            params["verified"] = "true" if verified else "false"
        if tags:
            params["tags"] = tags
        if created_at:
            params["created_at"] = created_at
        if sort_by:
            params["sort"] = sort_by
        return self.session.get(url, params=params).text

    def analysis_result(self, result_id: str) -> str:
        """Return an analysis result.

        Args:
            result_id: UUID of the analysis result.

        Returns:
            The analysis result.
        """
        url = self.get_url("analysis_result")
        url = url.format(uuid=result_id)
        return self.session.get(url).text

    def experiment_upload(self, experiment: str) -> Dict:
        """Upload an experiment.

        Args:
            experiment: The experiment data to upload.

        Returns:
            JSON response.
        """
        url = self.get_url("experiments")
        raw_data = self.session.post(
            url, data=experiment, headers=self._HEADER_JSON_CONTENT
        ).json()
        return raw_data

    def experiment_delete(self, experiment_id: str) -> Dict:
        """Delete an experiment.

        Args:
            experiment_id: Experiment UUID.

        Returns:
            JSON response.
        """
        url = self.get_url("experiment")
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
        url = self.get_url("experiment")
        url = url.format(uuid=experiment_id)
        return self.session.put(
            url, data=new_data, headers=self._HEADER_JSON_CONTENT
        ).json()

    def analysis_result_create(self, result: str) -> Dict:
        """Create an analysis result.

        Args:
            result: The analysis result to upload.

        Returns:
            JSON response.
        """
        url = self.get_url("analysis_results")
        return self.session.post(
            url, data=result, headers=self._HEADER_JSON_CONTENT
        ).json()

    def analysis_result_update(self, result_id: str, new_data: str) -> Dict:
        """Update the analysis result.

        Args:
            result_id: The id of the analysis result to update
            new_data: The new data to update in the analysis result

        Returns:
            JSON response.
        """
        url = self.get_url("analysis_result")
        url = url.format(uuid=result_id)
        return self.session.put(
            url, data=new_data, headers=self._HEADER_JSON_CONTENT
        ).json()

    def bulk_analysis_result_update(self, new_data: str) -> Dict:
        """Bulk updates the analysis results.

        Args:
            new_data: The new data to update in the analysis result

        Returns:
            JSON response.
        """
        url = self.get_url("bulk_update_analysis_results")
        return self.session.put(
            url, data=new_data, headers=self._HEADER_JSON_CONTENT
        ).json()

    def analysis_result_delete(self, result_id: str) -> Dict:
        """Delete the analysis result.
        Args:
            result_id: The id of the analysis result to update

        Returns:
            JSON response.
        """
        url = self.get_url("analysis_result")
        url = url.format(uuid=result_id)
        return self.session.delete(url).json()

    def upload_plot(
        self,
        experiment_id: str,
        plot: bytes,
        plot_name: str,
    ) -> Dict:
        """Upload a plot for the experiment.

        Args:
            experiment_id: The experiment the plot belongs to.
            plot: Plot file name or data to upload.
            plot_name: Name of the plot.

        Returns:
            JSON response.
        """
        upload_request_url = self.get_url("plot_upload")
        upload_request_url = upload_request_url.format(
            uuid=experiment_id, name=plot_name
        )
        upload_url = self.session.get(upload_request_url).json()["url"]
        response = self.session.put(
            upload_url, data=plot, headers=self._HEADER_JSON_CONTENT, bare=True
        )
        return response

    def update_plot(
        self,
        experiment_id: str,
        plot: bytes,
        plot_name: str,
    ) -> Dict:
        """Update an experiment plot.

        Args:
            experiment_id: The experiment the plot belongs to.
            plot: Plot file name or data to upload.
            plot_name: Name of the plot to be updated.

        Returns:
            JSON response.
        """

        # with the current server endpoint, upload and update are the same
        return self.upload_plot(experiment_id, plot, plot_name)

    def get_plot(self, experiment_id: str, plot_name: str) -> bytes:
        """Retrieve the specific experiment plot.

        Args:
            experiment_id: The experiment the plot belongs to.
            plot_name: Name of the plot to be retrieved.
        Returns:
            Plot content.
        """
        url = self.get_url("plot")
        url = url.format(uuid=experiment_id, name=plot_name)
        response = self.session.get(url)
        return response.content

    def delete_plot(self, experiment_id: str, plot_name: str) -> None:
        """Delete this experiment plot.
        Args:
            experiment_id: The experiment the plot belongs to.
            plot_name: Name of the plot to be retrieved.
        """
        url = self.get_url("plot")
        url = url.format(uuid=experiment_id, name=plot_name)
        self.session.delete(url)

    def device_components(self, backend_name: Optional[str] = None) -> Dict:
        """Return a list of device components for the backend.

        Args:
            backend_name: Name of the backend.

        Returns:
            JSON response.
        """
        params = {}
        if backend_name:
            params["device_name"] = backend_name
        url = self.get_url("device_components")
        return self.session.get(url, params=params).json()

    def files(self, experiment_id: str) -> Dict:
        """Return the experiment file list from the experiment DB.
        Args:
            experiment_id: The experiment ID
        Returns:
            A dictionary containing the file list
        """
        url = self.get_url("files")
        url = url.format(uuid=experiment_id)
        return self.session.get(url).json()

    def file_upload(self, experiment_id: str, file_pathname: str, file_data: str):
        """Uploads a file to the DB
        Args:
            experiment_id: Experiment ID.
            file_pathname: The intended name of the data file
            file_data: The contents of the data file
        """
        upload_request_url = self.get_url("files_upload")
        upload_request_url = upload_request_url.format(
            uuid=experiment_id, path=file_pathname
        )
        upload_url = self.session.get(upload_request_url).json()["url"]
        self.session.put(
            upload_url, data=file_data, headers=self._HEADER_JSON_CONTENT, bare=True
        )

    def file_download(self, experiment_id: str, file_name: str) -> Dict:
        """Downloads a data file from the DB

        Args:
            experiment_id: Experiment ID.
            file_name: The name of the data file

        Returns:
            The Dictionary of contents of the file
        """
        download_request_url = self.get_url("files_download")
        download_request_url = download_request_url.format(
            uuid=experiment_id, path=file_name
        )
        result = self.session.get(download_request_url)
        if result.status_code == 200:
            return result.json()
        return result
