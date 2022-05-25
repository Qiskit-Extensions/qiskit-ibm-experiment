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

"""Dataclasses for returned results"""
import uuid
import copy
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union, Any
from datetime import datetime
from .constants import ResultQuality
from .device_component import DeviceComponent


@dataclass
class ExperimentData:
    """Dataclass for experiments"""

    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    experiment_type: str = None
    backend: Optional[str] = None
    tags: Optional[List[str]] = field(default_factory=list)
    job_ids: Optional[List[str]] = field(default_factory=list)
    share_level: Optional[str] = None
    metadata: Optional[Dict[str, str]] = field(default_factory=dict)
    figure_names: Optional[List[str]] = field(default_factory=list)
    notes: Optional[str] = None
    hub: Optional[str] = None
    group: Optional[str] = None
    project: Optional[str] = None
    owner: Optional[str] = None
    creation_datetime: Optional[datetime] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    updated_datetime: Optional[datetime] = None

    def __str__(self):
        ret = ""
        ret += f"Experiment: {self.experiment_type}"
        ret += f"\nExperiment ID: {self.experiment_id}"
        if self.backend:
            ret += f"\nBackend: {self.backend}"
        if self.tags:
            ret += f"\nTags: {self.tags}"
        ret += f"\nHub\\Group\\Project: {self.hub}\\{self.group}\\{self.project}"
        if self.creation_datetime:
            ret += f"\nCreated at: {self.creation_datetime}"
        if self.start_datetime:
            ret += f"\nStarted at: {self.start_datetime}"
        if self.end_datetime:
            ret += f"\nEnded at: {self.end_datetime}"
        if self.updated_datetime:
            ret += f"\nUpdated at: {self.updated_datetime}"
        if self.metadata:
            ret += f"\nMetadata: {self.metadata}"
        if self.figure_names:
            ret += f"\nFigures: {self.figure_names}"
        return ret

    def copy(self):
        """Creates a deep copy of the data"""
        return ExperimentData(
            experiment_id=self.experiment_id,
            parent_id=self.parent_id,
            experiment_type=self.experiment_type,
            backend=self.backend,
            tags=copy.copy(self.tags),
            job_ids=copy.copy(self.job_ids),
            share_level=self.share_level,
            metadata=copy.deepcopy(self.metadata),
            figure_names=copy.copy(self.figure_names),
            notes=self.notes,
            hub=self.hub,
            group=self.group,
            project=self.project,
            owner=self.owner,
            creation_datetime=self.creation_datetime,
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
            updated_datetime=self.updated_datetime,
        )


@dataclass
class AnalysisResultData:
    """Dataclass for experiment analysis results"""

    result_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: Optional[str] = None
    result_type: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    device_components: Optional[
        Union[List[Union[str, DeviceComponent]], str, DeviceComponent]
    ] = field(default_factory=list)
    quality: Optional[ResultQuality] = ResultQuality.UNKNOWN
    verified: Optional[bool] = False
    tags: Optional[List[str]] = field(default_factory=list)
    backend_name: Optional[str] = None
    creation_datetime: Optional[datetime] = None
    updated_datetime: Optional[datetime] = None
    chisq: Optional[float] = None

    def __str__(self):
        ret = f"Result {self.result_type}"
        ret += f"\nResult ID: {self.result_id}"
        ret += f"\nExperiment ID: {self.experiment_id}"
        ret += f"\nBackend: {self.backend_name}"
        ret += f"\nQuality: {self.quality}"
        ret += f"\nVerified: {self.verified}"
        ret += f"\nDevice components: {self.device_components}"
        ret += f"\nData: {self.result_data}"
        if self.chisq:
            ret += f"\nChi Square: {self.chisq}"
        if self.tags:
            ret += f"\nTags: {self.tags}"
        if self.creation_datetime:
            ret += f"\nCreated at: {self.creation_datetime}"
        if self.updated_datetime:
            ret += f"\nUpdated at: {self.updated_datetime}"
        return ret

    def copy(self):
        """Creates a deep copy of the data"""
        return AnalysisResultData(
            result_id=self.result_id,
            experiment_id=self.experiment_id,
            result_type=self.result_type,
            result_data=copy.deepcopy(self.result_data),
            device_components=copy.copy(self.device_components),
            quality=self.quality,
            verified=self.verified,
            tags=copy.copy(self.tags),
            backend_name=self.backend_name,
            creation_datetime=self.creation_datetime,
            updated_datetime=self.updated_datetime,
            chisq=self.chisq,
        )
