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
from qiskit_ibm_experiment import ExperimentData
from qiskit_ibm_experiment.exceptions import IBMExperimentEntryNotFound
class TestExperimentServerIntegration(IBMTestCase):
    """Test experiment modules."""

    @classmethod
    def setUpClass(cls):
        """Initial class level setup."""
        super().setUpClass()
        cls.service = IBMExperimentService(local=True)
        cls.service.options["prompt_for_delete"] = False

    def test_create_experiment(self):
        data = ExperimentData(
            experiment_type="test_experiment",
            backend="ibmq_qasm_simulator",
            metadata={"float_data": 3.14, "string_data": "foo"}
        )
        exp_id = self.service.create_experiment(data)
        self.assertIsNotNone(exp_id)

        exp = self.service.experiment(experiment_id=exp_id)
        self.assertEqual(exp.experiment_type, "test_experiment")
        self.assertEqual(exp.backend, "ibmq_qasm_simulator")
        self.assertEqual(exp.metadata['float_data'], 3.14)
        self.assertEqual(exp.metadata['string_data'], "foo")

    def test_delete_experiment(self):
        data = ExperimentData(
            experiment_type="test_experiment",
            backend="ibmq_qasm_simulator",
        )
        exp_id = self.service.create_experiment(data)
        # Check the experiment exists
        exp = self.service.experiment(experiment_id=exp_id)
        self.service.delete_experiment(exp_id)
        with self.assertRaises(IBMExperimentEntryNotFound):
            exp = self.service.experiment(experiment_id=exp_id)


if __name__ == "__main__":
    unittest.main()
