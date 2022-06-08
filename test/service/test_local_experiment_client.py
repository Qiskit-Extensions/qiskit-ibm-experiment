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
import numpy as np
from test.service.ibm_test_case import IBMTestCase
from qiskit_ibm_experiment import IBMExperimentService
from qiskit_ibm_experiment import ExperimentData, AnalysisResultData
from qiskit_ibm_experiment.exceptions import IBMExperimentEntryNotFound, IBMExperimentEntryExists
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

        # attempt to create an experiment with the same id; should fail
        with self.assertRaises(IBMExperimentEntryExists):
            self.service.create_experiment(exp)

    def test_update_experiment(self):
        data = ExperimentData(
            experiment_type="test_experiment",
            backend="ibmq_qasm_simulator",
            metadata={"float_data": 3.14, "string_data": "foo"}
        )
        exp_id = self.service.create_experiment(data)
        data = self.service.experiment(exp_id)
        data.metadata['float_data'] = 2.71
        data.experiment_type = "foo_type" # this should NOT change
        data.notes = ["foo_note"]
        self.service.update_experiment(data)
        result = self.service.experiment(exp_id)
        self.assertEqual(result.metadata['float_data'], 2.71)
        self.assertEqual(result.experiment_type, "test_experiment")
        self.assertEqual(result.notes[0], "foo_note")

        data.experiment_id = "foo_id" # should not be able to update
        with self.assertRaises(IBMExperimentEntryNotFound):
            self.service.update_experiment(data)

    def test_delete_experiment(self):
        data = ExperimentData(
            experiment_type="test_experiment",
            backend="ibmq_qasm_simulator",
        )
        exp_id = self.service.create_experiment(data)
        # Check the experiment exists
        self.service.experiment(experiment_id=exp_id)
        self.service.delete_experiment(exp_id)
        with self.assertRaises(IBMExperimentEntryNotFound):
            self.service.experiment(experiment_id=exp_id)

    def test_get_experiments(self):
        exp_ids = ['00', '01', '10', '11']
        for exp_id in exp_ids:
            self.service.create_experiment(
                ExperimentData(
                    experiment_id=exp_id,
                    experiment_type=f"test_get_experiments_{exp_id[0]}",
                    backend=f"backend_{exp_id[1]}",
                )
            )
        exps = self.service.experiments(experiment_type="test_get_experiments", experiment_type_operator='like')
        self.assertEqual(len(exps), len(exp_ids))
        exps = self.service.experiments(experiment_type="test_get_experiments",
                                        experiment_type_operator='like',
                                        backend_name="backend_0")
        self.assertEqual(len(exps), 2)
        self.assertEqual(exps[0].backend, "backend_0")
        self.assertEqual(exps[1].backend, "backend_0")
        self.assertEqual(exps[0].experiment_id[1], "0")
        self.assertEqual(exps[1].experiment_id[1], "0")

    def test_create_analysis_result(self):
        exp_id = self.service.create_experiment(ExperimentData(experiment_type="test_experiment", backend="ibmq_qasm_simulator"))
        analysis_result_value = {"str": "foo", "float": 3.14}
        analysis_data = AnalysisResultData(experiment_id=exp_id,
                                           result_data=analysis_result_value,
                                           result_type="qiskit_test")
        analysis_id = self.service.create_analysis_result(analysis_data)
        result = self.service.analysis_result(result_id=analysis_id)
        self.assertEqual(result.result_type, "qiskit_test")
        self.assertEqual(result.result_data["str"], analysis_result_value["str"])
        self.assertEqual(result.result_data["float"], analysis_result_value["float"])

    def test_get_analysis_results(self):
        exp_id = self.service.create_experiment(
            ExperimentData(experiment_type="test_experiment",
                           backend="ibmq_qasm_simulator"))
        result_ids = ['00', '01', '10', '11']
        for result_id in result_ids:
            analysis_result_value = {"str": f"foo_{result_id}", "float": 3.14 + int(result_id)}
            analysis_data = AnalysisResultData(experiment_id=exp_id,
                                               result_id=result_id,
                                               result_data=analysis_result_value,
                                               result_type=f"test_get_analysis_results_{result_id[0]}")
            self.service.create_analysis_result(analysis_data)
        results = self.service.analysis_results(result_type="test_get_analysis_results", result_type_operator='like')
        self.assertEqual(len(results), len(result_ids))
        results = self.service.analysis_results(
            result_type="test_get_analysis_results_1")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].result_data['float'], 3.14 + 10)
        self.assertEqual(results[1].result_data['float'], 3.14 + 11)



if __name__ == "__main__":
    unittest.main()
