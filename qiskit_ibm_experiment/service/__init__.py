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
==============================================
Service (:mod:`qiskit_ibm_experiment.service`)
==============================================

.. currentmodule:: qiskit_ibm_experiment.service

Modules related to IBM Quantum experiment service.

.. note::

  This service is not available to all accounts.

You can use the experiment service to query, upload, and retrieve
experiments, experiment figures, and analysis results. For example::

    from qiskit_ibm_experiment import IBMExperimentService
    service = IBMExperimentService()
    print(service.backends())

This service is intended to be used in conjunction with the ``qiskit-experiments``
package, which allows you to create different types of experiments (for example,
:class:`qiskit_experiments.library.characterization.T1`).

Classes
=======

.. autosummary::
    :toctree: ../stubs/

    IBMExperimentService
    ResultQuality
    DeviceComponent
"""

from .ibm_experiment_service import IBMExperimentService
from .constants import ResultQuality, ExperimentShareLevel
from .device_component import DeviceComponent
