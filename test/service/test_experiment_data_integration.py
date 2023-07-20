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

"""Experiment integration tests."""

import os
import unittest
from unittest import mock, skipIf
import contextlib
from test.service.ibm_test_case import IBMTestCase
import numpy as np
from qiskit import transpile, QuantumCircuit
from qiskit.providers import JobStatus
from qiskit.test.reference_circuits import ReferenceCircuits
from qiskit_experiments.framework import (
    ExperimentData,
    ExperimentDecoder,
    ExperimentEncoder,
)
from qiskit_experiments.framework.experiment_data import ExperimentStatus
from qiskit_experiments.framework import AnalysisResult
from qiskit_experiments.database_service.exceptions import ExperimentEntryNotFound
from qiskit_ibm_provider import IBMProvider

from qiskit_ibm_experiment import IBMExperimentService
from qiskit_ibm_experiment.exceptions import IBMExperimentEntryNotFound
from qiskit_ibm_experiment.exceptions import IBMApiError


@skipIf(
    not os.environ.get("QISKIT_IBM_USE_STAGING_CREDENTIALS", ""), "Only runs on staging"
)
class TestExperimentDataIntegration(IBMTestCase):
    """Test experiment service with experiment data."""

    @classmethod
    def setUpClass(cls):
        """Initial class level setup."""
        super().setUpClass()
        try:
            cls._setup_service()
            cls._setup_provider()
            cls.circuit = transpile(ReferenceCircuits.bell(), cls.backend)
        except Exception as err:
            cls.log.info("Error while setting the service/provider: %s", err)
            raise

    @classmethod
    def _setup_service(cls):
        """Get the service for the class."""
        cls.service = IBMExperimentService(
            token=os.getenv("QISKIT_IBM_STAGING_API_TOKEN"),
            url=os.getenv("QISKIT_IBM_STAGING_API_URL"),
        )

    @classmethod
    def _setup_provider(cls):
        """Get the provider for the class."""
        cls.provider = IBMProvider(
            token=os.getenv("QISKIT_IBM_STAGING_API_TOKEN"),
            url=os.getenv("QISKIT_IBM_STAGING_API_URL"),
            instance=os.getenv("QISKIT_IBM_STAGING_HGP"),
        )
        cls.backend = cls.provider.get_backend(os.getenv("QISKIT_IBM_STAGING_BACKEND"))
        try:
            cls.device_components = cls.service.device_components(cls.backend.name)
        except IBMApiError:
            cls.device_components = None

    def setUp(self) -> None:
        """Test level setup."""
        super().setUp()
        self.experiments_to_delete = []
        self.results_to_delete = []
        self.jobs_to_cancel = []

    def tearDown(self):
        """Test level tear down."""
        for result_uuid in self.results_to_delete:
            try:
                with mock.patch("builtins.input", lambda _: "y"):
                    self.service.delete_analysis_result(result_uuid)
            except Exception as err:  # pylint: disable=broad-except
                self.log.info(
                    "Unable to delete analysis result %s: %s", result_uuid, err
                )
        for expr_uuid in self.experiments_to_delete:
            try:
                with mock.patch("builtins.input", lambda _: "y"):
                    self.service.delete_experiment(expr_uuid)
            except Exception as err:  # pylint: disable=broad-except
                self.log.info("Unable to delete experiment %s: %s", expr_uuid, err)
        for job in self.jobs_to_cancel:
            with contextlib.suppress(Exception):
                job.cancel()
        super().tearDown()

    # TODO add after options PR
    # def test_service_options(self):
    #     """Test service options."""
    #     self.assertFalse(self.service.options()['auto_save'])
    #
    def test_add_data_job(self):
        """Test add job to experiment data."""
        exp_data = ExperimentData(
            backend=self.backend, experiment_type="qiskit_test", service=self.service
        )
        transpiled = transpile(ReferenceCircuits.bell(), self.backend)
        transpiled.metadata = {"foo": "bar"}
        job = self._run_circuit(transpiled)
        exp_data.add_jobs(job)
        self.assertEqual([job.job_id()], exp_data.job_ids)
        result = job.result()
        exp_data.block_for_results()
        circuit_data = exp_data.data(0)
        self.assertEqual(result.get_counts(0), circuit_data["counts"])
        self.assertEqual(job.job_id(), circuit_data["job_id"])
        self.assertEqual(transpiled.metadata, circuit_data["metadata"])

    def test_new_experiment_data(self):
        """Test creating a new experiment data."""
        metadata = {"complex": 2 + 3j, "numpy": np.zeros(2)}
        exp_data = ExperimentData(
            service=self.service,
            backend=self.backend,
            experiment_type="qiskit_test",
            tags=["foo", "bar"],
            share_level="hub",
            metadata=metadata,
            notes="some notes",
        )

        job_ids = []
        for _ in range(2):
            job = self._run_circuit()
            exp_data.add_jobs(job)
            job_ids.append(job.job_id())

        exp_data.block_for_results().save(suppress_errors=False)
        self.experiments_to_delete.append(exp_data.experiment_id)

        hub, group, project = list(self.backend.provider._hgps)[0].split("/")

        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        self._verify_experiment_data(exp_data, rexp)
        self.assertEqual(hub, rexp.hub)  # pylint: disable=no-member
        self.assertEqual(group, rexp.group)  # pylint: disable=no-member
        self.assertEqual(project, rexp.project)  # pylint: disable=no-member

    def test_update_experiment_data(self):
        """Test updating an experiment."""
        exp_data = self._create_experiment_data()

        for _ in range(2):
            job = self._run_circuit()
            exp_data.add_jobs(job)
        exp_data.tags = ["foo", "bar"]
        exp_data.share_level = "hub"
        exp_data.notes = "some notes"
        exp_data.block_for_results().save(suppress_errors=False)

        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        self._verify_experiment_data(exp_data, rexp)

    def _verify_experiment_data(self, expected, actual):
        """Verify the input experiment data."""
        self.assertEqual(expected.experiment_id, actual.experiment_id)
        self.assertEqual(expected.job_ids, actual.job_ids)
        self.assertEqual(expected.share_level, actual.share_level)
        self.assertEqual(expected.tags, actual.tags)
        self.assertEqual(expected.notes, actual.notes)
        self.assertEqual(
            expected.metadata.get("complex", {}), actual.metadata.get("complex", {})
        )
        self.assertTrue(actual.creation_datetime)
        self.assertTrue(getattr(actual, "creation_datetime").tzinfo)

    def test_add_analysis_results(self):
        """Test adding an analysis result."""
        exp_data = self._create_experiment_data()
        result_data = {"complex": 2 + 3j, "numpy": np.zeros(2)}
        aresult = AnalysisResult(
            name="qiskit_test",
            value=result_data,
            device_components=self.device_components,
            experiment_id=exp_data.experiment_id,
            quality="good",
            verified=True,
            tags=["foo", "bar"],
            service=self.service,
        )
        exp_data.add_analysis_results(aresult)
        exp_data.save(suppress_errors=False)

        rresult = AnalysisResult.load(aresult.result_id, self.service)
        self.assertEqual(exp_data.experiment_id, rresult.experiment_id)
        self._verify_analysis_result(aresult, rresult)

    def test_update_analysis_result(self):
        """Test updating an analysis result."""
        aresult, exp_data = self._create_analysis_result()

        rdata = {"complex": 2 + 3j, "numpy": np.zeros(2)}
        aresult.value = rdata
        aresult.quality = "good"
        aresult.verified = True
        aresult.tags = ["foo", "bar"]
        aresult.save(suppress_errors=False)

        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        rresult = rexp.analysis_results(0)
        self._verify_analysis_result(aresult, rresult)

    def _verify_analysis_result(self, expected, actual):
        """Verify the input analysis result."""
        self.assertEqual(expected.result_id, actual.result_id)
        self.assertEqual(expected.name, actual.name)
        ecomp = {str(comp) for comp in expected.device_components}
        acomp = {str(comp) for comp in actual.device_components}
        self.assertEqual(ecomp, acomp)
        self.assertEqual(expected.experiment_id, actual.experiment_id)
        self.assertEqual(expected.quality, actual.quality)
        self.assertEqual(expected.verified, actual.verified)
        self.assertEqual(expected.tags, actual.tags)
        self.assertEqual(expected.value["complex"], actual.value["complex"])
        self.assertEqual(expected.value["numpy"].all(), actual.value["numpy"].all())

    def test_delete_analysis_result(self):
        """Test deleting an analysis result."""
        aresult, exp_data = self._create_analysis_result()
        with mock.patch("builtins.input", lambda _: "y"):
            exp_data.delete_analysis_result(0)
            exp_data.save(suppress_errors=False)
        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        self.assertRaises(
            ExperimentEntryNotFound, rexp.analysis_results, aresult.result_id
        )
        self.assertRaises(
            IBMExperimentEntryNotFound, self.service.analysis_result, aresult.result_id
        )

    def test_add_figures(self):
        """Test adding a figure to the experiment data."""
        exp_data = self._create_experiment_data()
        hello_bytes = str.encode("hello world")

        sub_tests = ["hello.svg", None]

        for idx, figure_name in enumerate(sub_tests):
            with self.subTest(figure_name=figure_name):
                exp_data.add_figures(
                    figures=hello_bytes, figure_names=figure_name, save_figure=True
                )
                rexp = ExperimentData.load(exp_data.experiment_id, self.service)
                self.assertEqual(rexp.figure(idx).figure, hello_bytes)

    def test_add_figures_plot(self):
        """Test adding a matplotlib figure."""
        import matplotlib.pyplot as plt

        figure, axes = plt.subplots()
        axes.plot([1, 2, 3])

        exp_data = self._create_experiment_data()
        exp_data.add_figures(figure, save_figure=True)

        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        self.assertTrue(rexp.figure(0))

    def test_add_figures_file(self):
        """Test adding a figure file."""
        exp_data = self._create_experiment_data()
        hello_bytes = str.encode("hello world")
        file_name = "hello_world.svg"
        self.addCleanup(os.remove, file_name)
        with open(file_name, "wb") as file:
            file.write(hello_bytes)

        exp_data.add_figures(figures=file_name, save_figure=True)
        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        self.assertEqual(rexp.figure(0).figure, hello_bytes)

    def test_update_figure(self):
        """Test updating a figure."""
        exp_data = self._create_experiment_data()
        hello_bytes = str.encode("hello world")
        figure_name = "hello.svg"

        exp_data.add_figures(
            figures=hello_bytes, figure_names=figure_name, save_figure=True
        )
        self.assertEqual(exp_data.figure(0).figure, hello_bytes)

        friend_bytes = str.encode("hello friend")
        exp_data.add_figures(
            figures=friend_bytes,
            figure_names=figure_name,
            overwrite=True,
            save_figure=True,
        )
        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        self.assertEqual(rexp.figure(0).figure, friend_bytes)
        self.assertEqual(rexp.figure(figure_name).figure, friend_bytes)

    def test_delete_figure(self):
        """Test deleting a figure."""
        exp_data = self._create_experiment_data()
        hello_bytes = str.encode("hello world")
        figure_name = "hello.svg"

        exp_data.add_figures(
            figures=hello_bytes, figure_names=figure_name, save_figure=True
        )
        with mock.patch("builtins.input", lambda _: "y"):
            exp_data.delete_figure(0)
            exp_data.save(suppress_errors=False)

        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        self.assertRaises(IBMExperimentEntryNotFound, rexp.figure, figure_name)
        self.assertRaises(
            IBMExperimentEntryNotFound,
            self.service.figure,
            exp_data.experiment_id,
            figure_name,
        )

    def test_save_all(self):
        """Test saving all."""
        exp_data = self._create_experiment_data()
        exp_data.tags = ["foo", "bar"]
        aresult = AnalysisResult(
            value={},
            name="qiskit_test",
            device_components=self.device_components,
            experiment_id=exp_data.experiment_id,
        )
        exp_data.add_analysis_results(aresult)
        hello_bytes = str.encode("hello world")
        exp_data.add_figures(hello_bytes, figure_names="hello.svg")
        exp_data.save(suppress_errors=False)

        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        # Experiment tag order is not necessarily preserved
        # so compare tags with a predictable sort order.
        self.assertEqual(["bar", "foo"], sorted(rexp.tags))
        self.assertEqual(aresult.result_id, rexp.analysis_results(0).result_id)
        self.assertEqual(hello_bytes, rexp.figure(0).figure)

        exp_data.delete_analysis_result(0)
        exp_data.delete_figure(0)
        with mock.patch("builtins.input", lambda _: "y"):
            exp_data.save(suppress_errors=False)

        rexp = ExperimentData.load(exp_data.experiment_id, self.service)
        self.assertRaises(IBMExperimentEntryNotFound, rexp.figure, "hello.svg")
        self.assertRaises(
            ExperimentEntryNotFound, rexp.analysis_results, aresult.result_id
        )

    def test_set_service_job(self):
        """Test setting service with a job."""
        exp_data = ExperimentData(experiment_type="qiskit_test", service=self.service)
        job = self._run_circuit()
        exp_data.add_jobs(job)
        exp_data.save(suppress_errors=False)
        self.experiments_to_delete.append(exp_data.experiment_id)

        rexp = self.service.experiment(exp_data.experiment_id)
        self.assertEqual([job.job_id()], rexp.job_ids)

    def test_auto_save_experiment(self):
        """Test auto save."""
        exp_data = self._create_experiment_data()
        exp_data.auto_save = True

        subtests = [
            (
                setattr,
                (
                    exp_data,
                    "tags",
                    ["foo"],
                ),
            ),
            (setattr, (exp_data, "notes", "foo")),
            (setattr, (exp_data, "share_level", "hub")),
        ]

        for func, params in subtests:
            with self.subTest(func=func):
                with mock.patch.object(
                    IBMExperimentService,
                    "create_or_update_experiment",
                    wraps=exp_data.service.create_or_update_experiment,
                ) as mocked:
                    func(*params)
                    mocked.assert_called_once()
                    data = mocked.call_args[0][0]
                    self.assertEqual(exp_data.experiment_id, data.experiment_id)
                    mocked.reset_mock()

    def test_auto_save_figure(self):
        """Test auto saving figure."""
        exp_data = self._create_experiment_data()
        exp_data.auto_save = True
        figure_name = "hello.svg"

        with mock.patch.object(
            IBMExperimentService,
            "update_experiment",
            wraps=exp_data.service.update_experiment,
        ) as mocked_exp:
            with mock.patch.object(
                IBMExperimentService,
                "create_figure",
                wraps=exp_data.service.create_figure,
            ) as mocked_fig:
                exp_data.add_figures(
                    str.encode("hello world"), figure_names=figure_name
                )
                mocked_exp.assert_called_once()
                mocked_fig.assert_called_once()
                mocked_exp.reset_mock()

            with mock.patch.object(
                IBMExperimentService,
                "update_figure",
                wraps=exp_data.service.update_figure,
            ) as mocked_fig:
                exp_data.add_figures(
                    str.encode("hello friend"), figure_names=figure_name, overwrite=True
                )
                mocked_fig.assert_called_once()
                mocked_exp.assert_called_once()
                mocked_exp.reset_mock()

            with mock.patch.object(
                IBMExperimentService,
                "delete_figure",
                wraps=exp_data.service.delete_figure,
            ) as mocked_fig, mock.patch("builtins.input", lambda _: "y"):
                exp_data.delete_figure(figure_name)
                mocked_fig.assert_called_once()
                mocked_exp.assert_called_once()

    def test_auto_save_analysis_result(self):
        """Test auto saving analysis result."""
        exp_data = self._create_experiment_data()
        exp_data.auto_save = True
        aresult = AnalysisResult(
            value={},
            name="qiskit_test",
            device_components=self.device_components,
            experiment_id=exp_data.experiment_id,
        )

        with mock.patch.object(
            IBMExperimentService,
            "update_experiment",
            wraps=exp_data.service.update_experiment,
        ) as mocked_exp:
            with mock.patch.object(
                IBMExperimentService,
                "create_analysis_result",
                wraps=exp_data.service.create_analysis_result,
            ) as mocked_res:
                exp_data.add_analysis_results(aresult)
                mocked_exp.assert_called_once()
                mocked_res.assert_called_once()
                mocked_exp.reset_mock()

            with mock.patch.object(
                IBMExperimentService,
                "delete_analysis_result",
                wraps=exp_data.service.delete_analysis_result,
            ) as mocked_res, mock.patch("builtins.input", lambda _: "y"):
                exp_data.delete_analysis_result(aresult.result_id)
                mocked_res.assert_called_once()
                mocked_exp.assert_called_once()

    def test_auto_save_analysis_result_update(self):
        """Test auto saving analysis result updates."""
        aresult, exp_data = self._create_analysis_result()
        aresult.auto_save = True

        subtests = [
            ("tags", ["foo"]),
            ("value", {"foo": "bar"}),
            ("quality", "GOOD"),
            ("verified", True),
        ]
        for attr, value in subtests:
            with self.subTest(attr=attr):
                with mock.patch.object(
                    IBMExperimentService,
                    "create_or_update_analysis_result",
                    wraps=exp_data.service.create_or_update_analysis_result,
                ) as mocked:
                    setattr(aresult, attr, value)
                    mocked.assert_called_once()
                    data = mocked.call_args[0][0]
                    self.assertEqual(aresult.result_id, data.result_id)
                    mocked.reset_mock()

    def test_block_for_results(self):
        """Test blocking for jobs"""
        exp_data = ExperimentData(
            backend=self.backend, experiment_type="qiskit_test", service=self.service
        )
        jobs = []
        for _ in range(2):
            job = self._run_circuit()
            exp_data.add_jobs(job)
            jobs.append(job)
        exp_data.block_for_results()
        self.assertTrue(all(job.status() == JobStatus.DONE for job in jobs))
        self.assertEqual(ExperimentStatus.DONE, exp_data.status())

    def test_file_upload_download(self):
        """test upload and download of actual experiment data"""
        exp_id = self._create_experiment_data().experiment_id
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.measure_all()
        data = {"string": "b-string", "int": 10, "float": 0.333, "circuit": qc}
        json_filename = "data.json"

        self.service.file_upload(
            exp_id, json_filename, data, json_encoder=ExperimentEncoder
        )
        rjson_data = self.service.file_download(
            exp_id, json_filename, json_decoder=ExperimentDecoder
        )
        self.assertEqual(data, rjson_data)

    def _create_experiment_data(self):
        """Create an experiment data."""
        exp_data = ExperimentData(
            backend=self.backend,
            experiment_type="qiskit_test",
            verbose=False,
            service=self.service,
        )
        exp_data.save(suppress_errors=False)
        self.experiments_to_delete.append(exp_data.experiment_id)
        return exp_data

    def _create_analysis_result(self):
        """Create a simple analysis result."""
        exp_data = self._create_experiment_data()
        aresult = AnalysisResult(
            value={},
            name="qiskit_test",
            device_components=self.device_components,
            experiment_id=exp_data.experiment_id,
        )
        exp_data.add_analysis_results(aresult)
        exp_data.save(suppress_errors=False)
        self.results_to_delete.append(aresult.result_id)
        return aresult, exp_data

    def _run_circuit(self, circuit=None):
        """Run a circuit."""
        circuit = circuit or self.circuit
        job = self.backend.run(circuit, shots=1)
        self.jobs_to_cancel.append(job)
        return job


if __name__ == "__main__":
    unittest.main()
