# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Experiment constants."""

import enum
import os

DEFAULT_BASE_URL = "https://auth.quantum-computing.ibm.com/api"
DEFAULT_ACCOUNT_CONFIG_JSON_FILE = os.path.join(
    os.path.expanduser("~"), ".qiskit", "qiskit-ibm.json"
)
DEFAULT_ACCOUNT_NAME = "default-ibm-quantum"
ACCOUNT_CHANNEL = "ibm_quantum"


class ExperimentShareLevel(enum.Enum):
    """Possible values for experiment share level (visibility)."""

    PRIVATE = "private"  # The experiment is only visible to its owner
    PROJECT = "project"  # The experiment is shared within its project
    GROUP = "group"  # The experiment is shared within its group
    HUB = "hub"  # The experiment is shared within its hub
    PUBLIC = "public"  # The experiment is shared publicly regardless of provider


class ResultQuality(enum.Enum):
    """Possible values for analysis result quality."""

    BAD = "BAD"
    GOOD = "GOOD"
    UNKNOWN = "UNKNOWN"


RESULT_QUALITY_FROM_API = {
    "Good": ResultQuality.GOOD,
    "Bad": ResultQuality.BAD,
    "No Information": ResultQuality.UNKNOWN,
}


RESULT_QUALITY_TO_API = {
    ResultQuality.GOOD: "Good",
    ResultQuality.BAD: "Bad",
    ResultQuality.UNKNOWN: "No Information",
}

RESULT_QUALITY_FROM_DATAFRAME = {
    "good": ResultQuality.GOOD,
    "bad": ResultQuality.BAD,
    "unknown": ResultQuality.UNKNOWN,
}

RESULT_QUALITY_TO_DATAFRAME = {
    ResultQuality.GOOD: "good",
    ResultQuality.BAD: "bad",
    ResultQuality.UNKNOWN: "unknown",
}
