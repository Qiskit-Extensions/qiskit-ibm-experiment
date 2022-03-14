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

import unittest
from test.service.ibm_test_case import IBMTestCase
from qiskit_ibm_experiment import IBMExperimentService


class TestExperiment(IBMTestCase):
    """Test experiment."""

    @classmethod
    def setUpClass(cls):
        """Initial class level setup."""
        # pylint: disable=arguments-differ
        super().setUpClass()
        cls._setup_service()

    @classmethod
    def _setup_service(cls):
        """Get the service for the class."""
        cls.service = IBMExperimentService(local=True)

    def test_default_preferences(self):
        """Test getting default preferences."""
        self.assertFalse(self.service.preferences["auto_save"])

    def test_set_preferences(self):
        """Test setting preferences."""
        self.service.preferences["auto_save"] = True
        self.assertTrue(self.service.preferences["auto_save"])

    def test_default_options(self):
        """Test getting default options."""
        self.assertTrue(self.service.options["prompt_for_delete"])

    def test_set_options(self):
        """Test setting options."""
        original_options = self.service.options
        self.service.set_option(prompt_for_delete=False)
        self.assertFalse(self.service.options["prompt_for_delete"])
        self.service.options = original_options

    def test_prompt_for_delete_options(self):
        """Test delete prompt is not displayed given the corresponding option"""
        original_options = self.service.options
        self.service.set_option(prompt_for_delete=False)
        self.assertTrue(
            self.service._confirm_delete("")
        )  # should work without mock patch
        self.service.options = original_options


if __name__ == "__main__":
    unittest.main()
