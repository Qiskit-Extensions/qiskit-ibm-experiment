# This code is part of Qiskit.
#
# (C) Copyright IBM 2021-2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Local experiment client tests"""
import unittest
from test.service.ibm_test_case import IBMTestCase
from qiskit_ibm_experiment import IBMExperimentService


class TestExperimentServerIntegration(IBMTestCase):
    """Test experiment modules."""

    @classmethod
    def setUpClass(cls):
        """Initial class level setup."""
        super().setUpClass()
        cls.service = IBMExperimentService(local=True)

    def test_create_experiment(self):
        exp_id = self.service.create_experiment(
            experiment_type="test_experiment",
            backend_name="ibmq_qasm_simulator",
        )
        self.assertIsNotNone(exp_id)

if __name__ == "__main__":
    unittest.main()
