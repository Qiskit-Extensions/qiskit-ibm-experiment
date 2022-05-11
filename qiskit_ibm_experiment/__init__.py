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

"""
========================================================
Qiskit Experiment Service (:mod:`qiskit_ibm_experiment`)
========================================================

.. currentmodule:: qiskit_ibm_experiment

Logging
-------

Qiskit IBM Experiment Service uses the ``qiskit_ibm_experiment`` logger.

Two environment variables can be used to control the logging:

    * ``QISKIT_IBM_EXPERIMENT_LOG_LEVEL``: Specifies the log level to use.
      If an invalid level is set, the log level defaults to ``WARNING``.
      The valid log levels are ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, and ``CRITICAL``
      (case-insensitive). If the environment variable is not set, then the parent logger's level
      is used, which also defaults to ``WARNING``.
    * ``QISKIT_IBM_EXPERIMENT_LOG_FILE``: Specifies the name of the log file to use. If specified,
      messages will be logged to the file only. Otherwise messages will be logged to the standard
      error (usually the screen).

For more advanced use, you can modify the logger itself. For example, to manually set the level
to ``WARNING``::

    import logging
    logging.getLogger('qiskit_ibm_experiment').setLevel(logging.WARNING)

Classes
==========================
.. autosummary::
   :toctree: ../stubs/

Exceptions
==========

.. autosummary::
    :toctree: ../stubs/

    IBMExperimentError
    IBMExperimentEntryExists
    IBMExperimentEntryNotFound
"""

import logging

from .service import IBMExperimentService

from .exceptions import *
from .service.constants import ResultQuality
from .service.utils import setup_logger
from .service.experiment_dataclasses import ExperimentData, AnalysisResultData
from .version import __version__


# Setup the logger for the IBM Quantum Provider package.
logger = logging.getLogger(__name__)
setup_logger(logger)

# Constants used by the IBM Quantum logger.
QISKIT_IBM_EXPERIMENT_LOGGER_NAME = "qiskit_ibm_experiment"
"""The name of the IBM Quantum logger."""
QISKIT_IBM_EXPERIMENT_LOG_LEVEL = "QISKIT_IBM_EXPERIMENT_LOG_LEVEL"
"""The environment variable name that is used to set the level for the IBM Quantum logger."""
QISKIT_IBM_EXPERIMENT_LOG_FILE = "QISKIT_IBM_EXPERIMENT_LOG_FILE"
"""The environment variable name that is used to set the file for the IBM Quantum logger."""
