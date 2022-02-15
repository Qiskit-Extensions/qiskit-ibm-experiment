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
        'experiment': '/experiments/{uuid}'
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
        raw_data = self.session.get(url).text
        return raw_data

