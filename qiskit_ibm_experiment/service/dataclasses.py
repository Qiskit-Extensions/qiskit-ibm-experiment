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
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class ExperimentData:
    experiment_id: str
    parent_id: Optional[str]
    experiment_type: str
    backend: str
    tags: List[str]
    job_ids: List[str]
    share_level: str
    metadata: Dict[str, str]
    figure_names: List[str]
    notes: Optional[str]
    hub: str
    group: str
    project: str
    owner: str
    creation_datetime: datetime
    start_datetime: datetime
    end_datetime: datetime
    updated_datetime: datetime

@dataclass
class AnalysisResultData:
    experiment_id: str
    result_id: str
    result_type: str
    result_data: Dict[str, Any]
    device_components: List[str]
    quality: "ResultQuality"
    verified: bool
    tags: List[str]
    backend_name: str
    creation_datetime: datetime

