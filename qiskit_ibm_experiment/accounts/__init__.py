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

"""
================================================
Accounts (:mod:`qiskit_ibm_experiment.accounts`)
================================================

.. currentmodule:: qiskit_ibm_experiment.accounts

Account management functionality related to the IBM experiment service.

Classes
=======

.. autosummary::
    :toctree: ../stubs/

    Account
    AccountManager
    ProxyConfiguration

Exceptions
==========

.. autosummary::
    :toctree: ../stubs/

    AccountNotFoundError
    AccountAlreadyExistsError
    InvalidAccountError
"""

from .account import Account
from .management import AccountManager
from .configuration import ProxyConfiguration
from .exceptions import (
    AccountNotFoundError,
    AccountAlreadyExistsError,
    InvalidAccountError,
)
