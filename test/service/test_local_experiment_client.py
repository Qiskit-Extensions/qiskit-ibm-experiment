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
import uuid
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from test.service.ibm_test_case import IBMTestCase
from dateutil import tz
from qiskit_ibm_experiment import IBMExperimentService
from qiskit_ibm_experiment import ExperimentData, AnalysisResultData
from qiskit_ibm_experiment.service import ResultQuality
from qiskit_ibm_experiment.exceptions import (
    IBMExperimentEntryNotFound,
    IBMExperimentEntryExists,
)


class TestExperimentLocalClient(IBMTestCase):
    """Test experiment modules."""

    @classmethod
    def setUpClass(cls):
        """Initial class level setup."""
        super().setUpClass()
        cls.service = IBMExperimentService(local=True, local_save=False)
        cls.service.options["prompt_for_delete"] = False

    def test_create_experiment(self):
        """Tests creating an experiment"""
        data = ExperimentData(
            experiment_type="test_experiment",
            backend="ibmq_qasm_simulator",
            metadata={"float_data": 3.14, "string_data": "foo"},
        )
        exp_id = self.service.create_experiment(data)
        self.assertIsNotNone(exp_id)

        exp = self.service.experiment(experiment_id=exp_id)
        self.assertEqual(exp.experiment_type, "test_experiment")
        self.assertEqual(exp.backend, "ibmq_qasm_simulator")
        self.assertEqual(exp.metadata["float_data"], 3.14)
        self.assertEqual(exp.metadata["string_data"], "foo")

        # attempt to create an experiment with the same id; should fail
        with self.assertRaises(IBMExperimentEntryExists):
            self.service.create_experiment(exp)

    def test_update_experiment(self):
        """Tests updating an experiment"""
        data = ExperimentData(
            experiment_type="test_experiment",
            backend="ibmq_qasm_simulator",
            metadata={"float_data": 3.14, "string_data": "foo"},
        )
        exp_id = self.service.create_experiment(data)
        data = self.service.experiment(exp_id)
        data.metadata["float_data"] = 2.71
        data.experiment_type = "foo_type"  # this should NOT change
        data.notes = ["foo_note"]
        self.service.update_experiment(data)
        result = self.service.experiment(exp_id)
        self.assertEqual(result.metadata["float_data"], 2.71)
        self.assertEqual(result.experiment_type, "test_experiment")
        self.assertEqual(result.notes[0], "foo_note")

        data.experiment_id = "foo_id"  # should not be able to update
        with self.assertRaises(IBMExperimentEntryNotFound):
            self.service.update_experiment(data)

    def test_delete_experiment(self):
        """Tests deleting an experiment"""
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
        """Tests getting an experiment"""
        exp_ids = ["00", "01", "10", "11"]
        for exp_id in exp_ids:
            self.service.create_experiment(
                ExperimentData(
                    experiment_id=exp_id,
                    experiment_type=f"test_get_experiments_{exp_id[0]}",
                    backend=f"backend_{exp_id[1]}",
                )
            )
        exps = self.service.experiments(
            experiment_type="test_get_experiments", experiment_type_operator="like"
        )
        self.assertEqual(len(exps), len(exp_ids))
        exps = self.service.experiments(
            experiment_type="test_get_experiments",
            experiment_type_operator="like",
            backend_name="backend_0",
        )
        self.assertEqual(len(exps), 2)
        self.assertEqual(exps[0].backend, "backend_0")
        self.assertEqual(exps[1].backend, "backend_0")
        self.assertEqual(exps[0].experiment_id[1], "0")
        self.assertEqual(exps[1].experiment_id[1], "0")

    def test_create_analysis_result(self):
        """Tests creating an analysis result"""
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type="test_experiment", backend="ibmq_qasm_simulator"
            )
        )
        analysis_result_value = {"str": "foo", "float": 3.14}
        analysis_data = AnalysisResultData(
            experiment_id=exp_id,
            result_data=analysis_result_value,
            result_type="qiskit_test",
        )
        analysis_id = self.service.create_analysis_result(analysis_data)
        result = self.service.analysis_result(result_id=analysis_id)
        self.assertEqual(result.result_type, "qiskit_test")
        self.assertEqual(result.result_data["str"], analysis_result_value["str"])
        self.assertEqual(result.result_data["float"], analysis_result_value["float"])

    def test_get_analysis_results(self):
        """Tests getting an analysis result"""
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type="test_experiment", backend="ibmq_qasm_simulator"
            )
        )
        result_ids = ["00", "01", "10", "11"]
        for result_id in result_ids:
            analysis_result_value = {
                "str": f"foo_{result_id}",
                "float": 3.14 + int(result_id),
            }
            analysis_data = AnalysisResultData(
                experiment_id=exp_id,
                result_id=result_id,
                result_data=analysis_result_value,
                result_type=f"test_get_analysis_results_{result_id[0]}",
            )
            self.service.create_analysis_result(analysis_data)
        results = self.service.analysis_results(
            result_type="test_get_analysis_results", result_type_operator="like"
        )
        self.assertEqual(len(results), len(result_ids))
        results = self.service.analysis_results(
            result_type="test_get_analysis_results_1"
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].result_data["float"], 3.14 + 10)
        self.assertEqual(results[1].result_data["float"], 3.14 + 11)

    def test_delete_analysis_result(self):
        """Tests deleting an analysis result"""
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type="test_experiment", backend="ibmq_qasm_simulator"
            )
        )
        analysis_data = AnalysisResultData(
            experiment_id=exp_id,
            result_data={"foo": "delete_bar"},
            result_type="test_result",
        )
        result_id = self.service.create_analysis_result(analysis_data)
        result = self.service.analysis_result(result_id)
        self.assertEqual(result.result_data["foo"], "delete_bar")
        self.service.delete_analysis_result(result_id)
        with self.assertRaises(IBMExperimentEntryNotFound):
            result = self.service.analysis_result(result_id)

    def test_update_analysis_result(self):
        """Test updating an analysis result."""
        result_id = self._create_analysis_result()
        fit = dict(value=41.456, variance=4.051)
        chisq = 1.3253

        self.service.update_analysis_result(
            AnalysisResultData(
                result_id=result_id,
                result_data=fit,
                tags=["qiskit_test"],
                quality=ResultQuality.GOOD,
                verified=True,
                chisq=chisq,
            )
        )

        rresult = self.service.analysis_result(result_id)
        self.assertEqual(result_id, rresult.result_id)
        self.assertEqual(fit, rresult.result_data)
        self.assertEqual(["qiskit_test"], rresult.tags)
        self.assertEqual(ResultQuality.GOOD, rresult.quality)
        self.assertTrue(rresult.verified)
        self.assertEqual(chisq, rresult.chisq)

    def test_bulk_update_analysis_result(self):
        """Test bulk updating analysis results."""
        num_results = 4
        result_ids = [self._create_analysis_result() for _ in range(num_results)]
        fits = [
            dict(value=41.456 + i * 0.17, variance=4.051 + i * 0.53)
            for i in range(num_results)
        ]
        chisqs = [1.3253 + i * 0.13 for i in range(num_results)]

        new_results = [
            AnalysisResultData(
                result_id=result_ids[i],
                result_data=fits[i],
                tags=["qiskit_test"],
                quality=ResultQuality.GOOD,
                verified=True,
                chisq=chisqs[i],
            )
            for i in range(num_results)
        ]
        self.service.bulk_update_analysis_result(new_results)
        for i in range(num_results):
            rresult = self.service.analysis_result(result_ids[i])
            self.assertEqual(result_ids[i], rresult.result_id)
            self.assertEqual(fits[i], rresult.result_data)
            self.assertEqual(["qiskit_test"], rresult.tags)
            self.assertEqual(ResultQuality.GOOD, rresult.quality)
            self.assertTrue(rresult.verified)
            self.assertEqual(chisqs[i], rresult.chisq)

    def test_figure(self):
        """Test getting a figure."""
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type="test_experiment", backend="ibmq_qasm_simulator"
            )
        )
        hello_bytes = str.encode("hello world")
        figure_name = "hello.svg"
        self.service.create_figure(
            experiment_id=exp_id, figure=hello_bytes, figure_name=figure_name
        )
        fig = self.service.figure(exp_id, figure_name)
        self.assertEqual(fig, hello_bytes)

    def test_files(self):
        """Test upload and download of files"""
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type="test_experiment", backend="ibmq_qasm_simulator"
            )
        )
        hello_data = {"hello": "world", "foo": "bar"}
        filename = "test_file.json"
        self.service.file_upload(exp_id, filename, hello_data)
        rfile_data = self.service.file_download(exp_id, filename)
        self.assertEqual(hello_data, rfile_data)
        self.assertTrue(self.service.experiment_has_file(exp_id, filename))
        file_list = self.service.files(exp_id)["files"]
        self.assertEqual(len(file_list), 1)
        self.assertEqual(file_list[0]["Key"], filename)

        exp_id2 = self.service.create_experiment(
            ExperimentData(
                experiment_type="test_experiment", backend="ibmq_qasm_simulator"
            )
        )
        file_list = self.service.files(exp_id2)["files"]
        self.assertEqual(len(file_list), 0)

    def test_server_setting_start_time(self):
        """Tests that start time is initialized by the server unless already present"""
        ref_start_dt = datetime.now() - timedelta(days=1)
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type="qiskit_time_test",
                backend="ibmq_qasm_simulator",
            )
        )
        experiments = self.service.experiments(
            start_datetime_after=ref_start_dt,
            experiment_type="qiskit_time_test",
        )
        found = False
        for exp in experiments:
            if exp.experiment_id == exp_id:
                found = True
        self.assertTrue(found)

    def test_experiments_with_start_time(self):
        """Test retrieving an experiment by its start_time."""
        ref_start_dt = datetime.now() - timedelta(days=1)
        ref_start_dt = ref_start_dt.replace(tzinfo=tz.tzlocal())
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type="qiskit_test",
                backend="ibmq_qasm_simulator",
                start_datetime=ref_start_dt,
            )
        )

        before_start = ref_start_dt - timedelta(hours=1)
        after_start = ref_start_dt + timedelta(hours=1)

        sub_tests = [
            (before_start, None, True, "before start, None"),
            (None, after_start, True, "None, after start"),
            (before_start, after_start, True, "before, after start"),
            (after_start, None, False, "after start, None"),
            (None, before_start, False, "None, before start"),
            (before_start, before_start, False, "before, before start"),
        ]

        for start_dt, end_dt, expected, title in sub_tests:
            with self.subTest(title=title):
                backend_experiments = self.service.experiments(
                    start_datetime_after=start_dt,
                    start_datetime_before=end_dt,
                    experiment_type="qiskit_test",
                )
                found = False
                for exp in backend_experiments:
                    if start_dt:
                        self.assertGreaterEqual(exp.start_datetime, start_dt)
                    if end_dt:
                        self.assertLessEqual(exp.start_datetime, end_dt)
                    if exp.experiment_id == exp_id:
                        found = True
                self.assertEqual(
                    found,
                    expected,
                    f"Experiment {exp_id} (not)found unexpectedly when filter using "
                    "start_dt={start_dt}, end_dt={end_dt}. Found={found}",
                )

    def test_experiments_with_sort_by(self):
        """Test retrieving experiments with sort_by."""
        tags = [str(uuid.uuid4())]
        exp1 = self.service.create_experiment(
            ExperimentData(
                tags=tags,
                experiment_type="qiskit_test_1",
                start_datetime=datetime.now() - timedelta(hours=1),
            )
        )
        exp2 = self.service.create_experiment(
            ExperimentData(
                tags=tags,
                experiment_type="qiskit_test_2",
                start_datetime=datetime.now(),
            )
        )
        exp3 = self.service.create_experiment(
            ExperimentData(
                tags=tags,
                experiment_type="qiskit_test_1",
                start_datetime=datetime.now() - timedelta(hours=2),
            )
        )

        subtests = [
            (
                ["experiment_type:asc"],
                [exp1, exp3, exp2] if exp1 < exp3 else [exp3, exp1, exp2],
            ),
            (
                ["experiment_type:desc"],
                [exp2, exp1, exp3] if exp1 < exp3 else [exp2, exp3, exp1],
            ),
            (["start_datetime:asc"], [exp3, exp1, exp2]),
            (["start_datetime:desc"], [exp2, exp1, exp3]),
            (["experiment_type:asc", "start_datetime:asc"], [exp3, exp1, exp2]),
            (["experiment_type:asc", "start_datetime:desc"], [exp1, exp3, exp2]),
            (["experiment_type:desc", "start_datetime:asc"], [exp2, exp3, exp1]),
            (["experiment_type:desc", "start_datetime:desc"], [exp2, exp1, exp3]),
        ]

        for sort_by, expected in subtests:
            with self.subTest(sort_by=sort_by):
                experiments = self.service.experiments(
                    tags=tags,
                    sort_by=sort_by,
                    experiment_type_operator="like",
                    experiment_type="qiskit_test",
                )
                self.assertEqual(expected, [exp.experiment_id for exp in experiments])

    def _create_experiment(
        self,
        experiment_type: Optional[str] = None,
        json_encoder: Optional[json.JSONEncoder] = None,
        **kwargs,
    ) -> str:
        """Create a new experiment."""
        experiment_type = experiment_type or "qiskit_test"
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type=experiment_type,
                **kwargs,
            ),
            json_encoder=json_encoder,
        )
        return exp_id

    def _create_analysis_result(
        self,
        exp_id: Optional[str] = None,
        result_type: Optional[str] = None,
        result_data: Optional[Dict] = None,
        json_encoder: Optional[json.JSONEncoder] = None,
        **kwargs: Any,
    ):
        """Create a simple analysis result."""
        experiment_id = exp_id or self._create_experiment()
        result_type = result_type or "qiskit_test"
        result_data = result_data or {}
        aresult_id = self.service.create_analysis_result(
            AnalysisResultData(
                experiment_id=experiment_id,
                result_data=result_data,
                result_type=result_type,
                **kwargs,
            ),
            json_encoder=json_encoder,
        )
        return aresult_id


if __name__ == "__main__":
    unittest.main()
