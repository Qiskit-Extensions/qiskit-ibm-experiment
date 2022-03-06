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

"""Experiment tests."""

import os
import unittest
from unittest import skipIf, SkipTest
from test.service.ibm_test_case import IBMTestCase
from qiskit_ibm_experiment.exceptions import IBMNotAuthorizedError
from qiskit_ibm_experiment import IBMExperimentService


@skipIf(
    not os.environ.get("QISKIT_IBM_USE_STAGING_CREDENTIALS", ""), "Only runs on staging"
)
class TestExperimentPreferences(IBMTestCase):
    """Test experiment preferences."""

    @classmethod
    def setUpClass(cls):
        """Initial class level setup."""
        # pylint: disable=arguments-differ
        super().setUpClass()
        try:
            cls._setup_service()
        except IBMNotAuthorizedError:
            raise SkipTest("Not authorized to use experiment service.")

    @classmethod
    def _setup_service(cls):
        """Get the service for the class."""
        cls.service = IBMExperimentService(
            token=os.getenv("QISKIT_IBM_STAGING_API_TOKEN"),
            url=os.getenv("QISKIT_IBM_STAGING_API_URL"),
        )

    def test_default_preferences(self):
        """Test getting default preferences."""
        self.assertFalse(self.service.preferences["auto_save"])

    def test_set_preferences(self):
        """Test setting preferences."""
        self.service.preferences["auto_save"] = True
        self.assertTrue(self.service.preferences["auto_save"])


if __name__ == "__main__":
    unittest.main()
