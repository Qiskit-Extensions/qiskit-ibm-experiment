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

"""Experiment integration test with server."""

import os
import uuid
import unittest
import json
import re
from unittest import mock, skipIf
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from test.service.ibm_test_case import IBMTestCase
from test.utils.utils import ExperimentEncoder, ExperimentDecoder
import numpy as np
from dateutil import tz
import yaml
from qiskit_ibm_provider import IBMProvider
from qiskit_ibm_experiment.service import ResultQuality, ExperimentShareLevel
from qiskit_ibm_experiment import IBMExperimentEntryNotFound, IBMApiError
from qiskit_ibm_experiment import IBMExperimentService
from qiskit_ibm_experiment import ExperimentData, AnalysisResultData


@skipIf(
    not os.environ.get("QISKIT_IBM_USE_STAGING_CREDENTIALS", ""), "Only runs on staging"
)
class TestExperimentServerIntegration(IBMTestCase):
    """Test experiment modules."""

    @classmethod
    def setUpClass(cls):
        """Initial class level setup."""
        super().setUpClass()
        cls.default_exp_type = "qiskit_test"
        try:
            cls._setup_service()
            cls._setup_provider()
        except Exception as err:
            cls.log.info("Error while setting the service/provider: %s", err)
            raise

    @classmethod
    def _setup_service(cls):
        """Get the service for the class."""
        cls.service = IBMExperimentService(
            token=os.getenv("QISKIT_IBM_STAGING_API_TOKEN"),
            url=os.getenv("QISKIT_IBM_STAGING_API_URL"),
            hgp=os.getenv("QISKIT_IBM_STAGING_HGP"),
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

    @classmethod
    def get_experiments(cls, **kwargs):
        """Gets the experiments, filtering for default experiment type
        if not explicitly doing otherwise"""
        if "experiment_type" not in kwargs:
            kwargs["experiment_type"] = cls.default_exp_type
        return cls.service.experiments(**kwargs)

    def setUp(self) -> None:
        """Test level setup."""
        super().setUp()
        self.experiments_to_delete = []

    def tearDown(self):
        """Test level tear down."""
        for expr_uuid in self.experiments_to_delete:
            try:
                with mock.patch("builtins.input", lambda _: "y"):
                    self.service.delete_experiment(expr_uuid)
            except Exception as err:  # pylint: disable=broad-except
                print("Unable to delete experiment %s: %s", expr_uuid, err)
                self.log.info("Unable to delete experiment %s: %s", expr_uuid, err)
        super().tearDown()

    def test_experiments(self):
        """Test retrieving experiments."""
        exp_id = self._create_experiment()
        experiments = self.get_experiments()
        self.assertTrue(experiments, "No experiments found.")

        found = False
        for exp in experiments:
            self.assertTrue(exp.experiment_id, f"{exp} does not have an ID!")
            for dt_attr in [
                "start_datetime",
                "creation_datetime",
                "end_datetime",
                "updated_datetime",
            ]:
                if getattr(exp, dt_attr, None):
                    self.assertTrue(getattr(exp, dt_attr).tzinfo)
            if exp.experiment_id == exp_id:
                found = True
        self.assertTrue(found, f"Experiment {exp_id} not found!")

    def test_experiments_with_backend(self):
        """Test retrieving all experiments for a specific backend."""
        exp_id = self._create_experiment()
        backend_experiments = self.get_experiments(backend_name=self.backend.name)

        found = False
        for exp in backend_experiments:
            self.assertEqual(self.backend.name, exp.backend)
            if exp.experiment_id == exp_id:
                found = True
        self.assertTrue(
            found,
            f"Experiment {exp_id} not found when filter by backend name {self.backend.name}.",
        )

    def test_experiments_with_type(self):
        """Test retrieving all experiments for a specific type."""
        exp_type = "qiskit_test"
        exp_id = self._create_experiment(experiment_type=exp_type)
        backend_experiments = self.get_experiments(experiment_type=exp_type)

        found = False
        for exp in backend_experiments:
            self.assertEqual(exp_type, exp.experiment_type)
            if exp.experiment_id == exp_id:
                found = True
        self.assertTrue(
            found, f"Experiment {exp_id} not found when filter by type {exp_type}."
        )

    def test_experiments_with_parent_id(self):
        """Test retrieving all experiments for a specific parent id."""
        parent_id = self._create_experiment()
        child_id = self._create_experiment(parent_id=parent_id)
        experiments = self.get_experiments(parent_id=parent_id)

        found = False
        for exp in experiments:
            self.assertEqual(parent_id, exp.parent_id)
            if exp.experiment_id == child_id:
                found = True
        self.assertTrue(
            found, f"Experiment {child_id} not found when filter by type {parent_id}."
        )

    def test_experiments_with_type_operator(self):
        """Test retrieving all experiments for a specific type with operator."""
        exp_type = "qiskit_test"
        exp_id = self._create_experiment(experiment_type=exp_type)

        experiments = self.get_experiments(
            experiment_type="foo", experiment_type_operator="like"
        )
        self.assertNotIn(exp_id, [exp.experiment_id for exp in experiments])

        subtests = ["qiskit", "test"]
        for filter_type in subtests:
            with self.subTest(filter_type=filter_type):
                experiments = self.get_experiments(
                    experiment_type=exp_type, experiment_type_operator="like"
                )
                found = False
                for exp in experiments:
                    self.assertTrue(re.match(f".*{filter_type}.*", exp.experiment_type))
                    if exp.experiment_id == exp_id:
                        found = True
                self.assertTrue(
                    found,
                    f"Experiment {exp_id} not found "
                    f"when filter by type {filter_type}",
                )

    def test_experiments_with_bad_type_operator(self):
        """Test retrieving all experiments with a bad type operator."""
        with self.assertRaises(ValueError):
            self.get_experiments(experiment_type="foo", experiment_type_operator="bad")

    def test_experiments_with_start_time(self):
        """Test retrieving an experiment by its start_time."""
        ref_start_dt = datetime.now() - timedelta(days=1)
        ref_start_dt = ref_start_dt.replace(tzinfo=tz.tzlocal())
        exp_id = self._create_experiment(start_datetime=ref_start_dt)

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
                backend_experiments = self.get_experiments(
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
                    f"start_dt={start_dt}, end_dt={end_dt}. Found={found}",
                )

    def test_experiments_with_tags(self):
        """Test filtering experiments using tags."""
        ref_tags = ["qiskit_test", "foo"]
        exp_id = self._create_experiment(tags=ref_tags)

        phantom_tag = uuid.uuid4().hex
        sub_tests = [
            (ref_tags, "AND", True),
            (ref_tags, "OR", True),
            (ref_tags[:1], "OR", True),
            (ref_tags + [phantom_tag], "AND", False),
            (ref_tags + [phantom_tag], "OR", True),
            ([phantom_tag], "OR", False),
        ]
        for tags, operator, found in sub_tests:
            with self.subTest(tags=tags, operator=operator):
                experiments = self.get_experiments(tags=tags, tags_operator=operator)
                ref_expr_found = False
                for expr in experiments:
                    msg = f"Tags {tags} not fond in experiment tags {expr.tags}"
                    if operator == "AND":
                        self.assertTrue(all(f_tag in expr.tags for f_tag in tags), msg)
                    else:
                        self.assertTrue(any(f_tag in expr.tags for f_tag in tags), msg)
                    if expr.experiment_id == exp_id:
                        ref_expr_found = True
                self.assertTrue(
                    ref_expr_found == found,
                    f"Experiment tags {ref_tags} unexpectedly (not)found. Found={found}",
                )

    def test_experiments_with_hgp(self):
        """Test retrieving all experiments for a specific h/g/p."""
        exp_id = self._create_experiment()
        hub, group, project = list(self.provider._hgps)[0].split("/")
        sub_tests = [
            {"hub": hub},
            {"hub": hub, "group": group},
            {"hub": hub, "group": group, "project": project},
        ]

        for hgp_kwargs in sub_tests:
            with self.subTest(kwargs=hgp_kwargs.keys()):
                hgp_experiments = self.get_experiments(**hgp_kwargs)
                ref_expr_found = False
                for expr in hgp_experiments:
                    for hgp_key, hgp_val in hgp_kwargs.items():
                        self.assertEqual(getattr(expr, hgp_key), hgp_val)
                    if expr.experiment_id == exp_id:
                        ref_expr_found = True
                self.assertTrue(ref_expr_found)

    def test_experiments_with_hgp_error(self):
        """Test retrieving experiments with bad h/g/p specification."""
        sub_tests = [
            ({"project": "test_project"}, ["hub", "group"]),
            ({"project": "test_project", "group": "test_group"}, ["hub"]),
            ({"project": "test_project", "hub": "test_hub"}, ["group"]),
            ({"group": "test_group"}, ["hub"]),
        ]

        for hgp_kwargs, missing_keys in sub_tests:
            with self.subTest(kwargs=hgp_kwargs.keys()):
                with self.assertRaises(ValueError) as ex_cm:
                    self.get_experiments(**hgp_kwargs)
                for key in missing_keys:
                    self.assertIn(key, str(ex_cm.exception))

    def test_experiments_with_exclude_public(self):
        """Tests retrieving experiments with exclude_public filter."""
        # Make sure that we have at least one public experiment and one non-public
        # experiment.
        public_exp_id = self._create_experiment(share_level=ExperimentShareLevel.PUBLIC)
        private_exp_id = self._create_experiment(
            share_level=ExperimentShareLevel.PRIVATE
        )

        experiments = self.get_experiments(exclude_public=True)
        # The public experiment we just created should not be in the set.
        non_public_experiment_uuids = []
        for experiment in experiments:
            self.assertNotEqual(
                experiment.share_level,
                ExperimentShareLevel.PUBLIC.value,
                f"Public experiment should not be returned with exclude_public filter: {experiment}",
            )
            non_public_experiment_uuids.append(experiment.experiment_id)
        self.assertIn(
            private_exp_id,
            non_public_experiment_uuids,
            f"Non-public experiment not returned with exclude_public filter:{private_exp_id}",
        )
        self.assertNotIn(
            public_exp_id,
            non_public_experiment_uuids,
            f"Public experiment returned with exclude_public filter: {public_exp_id}",
        )

    def test_experiments_with_public_only(self):
        """Tests retrieving experiments with public_only filter."""
        # Make sure that we have at least one public experiment and one non-public
        # experiment.
        public_exp_id = self._create_experiment(share_level=ExperimentShareLevel.PUBLIC)
        private_exp_id = self._create_experiment(
            share_level=ExperimentShareLevel.PRIVATE
        )

        experiments = self.get_experiments(public_only=True)
        public_experiment_uuids = []
        for experiment in experiments:
            self.assertEqual(
                experiment.share_level,
                ExperimentShareLevel.PUBLIC.value,
                f"Only public experiments should be returned with public_only filter: {experiment}",
            )
            public_experiment_uuids.append(experiment.experiment_id)
        self.assertIn(
            public_exp_id,
            public_experiment_uuids,
            f"Public experiment not returned with public_only filter: {public_exp_id}",
        )
        self.assertNotIn(
            private_exp_id,
            public_experiment_uuids,
            f"Non-public experiment returned with public_only filter: {private_exp_id}",
        )

    def test_experiments_with_public_filters_error(self):
        """Tests that exclude_public and public_only cannot both be True."""
        with self.assertRaisesRegex(
            ValueError, "exclude_public and public_only cannot both be True"
        ):
            self.get_experiments(exclude_public=True, public_only=True)

    def test_experiments_with_exclude_mine(self):
        """Tests retrieving experiments with exclude_mine filter."""
        # Note that we cannot specify the owner when creating the experiment, the value comes
        # from the user profile via the token so we would have to use different test accounts
        # to explicitly create separately-owned experiments. We should be able to assume that
        # there is at least one experiment owned by another user in the integration test
        # environment though.
        exp_id = self._create_experiment()
        exp_owner = self.service.experiment(exp_id).owner

        not_my_experiments = self.get_experiments(exclude_mine=True)
        # The experiment we just created should not be in the set.
        not_mine_experiment_uuids = []
        for experiment in not_my_experiments:
            self.assertNotEqual(
                experiment["owner"],
                exp_owner,  # pylint: disable=no-member
                f"My experiment should not be returned with "
                f"exclude_mine filter: {experiment['experiment_id']}",
            )
            not_mine_experiment_uuids.append(experiment["experiment_id"])
        self.assertNotIn(
            exp_id,
            not_mine_experiment_uuids,
            f"My experiment returned with exclude_mine filter: {exp_id}",
        )

    def test_experiments_with_mine_only(self):
        """Tests retrieving experiments with mine_only filter."""
        # Note that we cannot specify the owner when creating the experiment, the value comes
        # from the user profile via the token so we would have to use different test accounts
        # to explicitly create separately-owned epxeriments. We should be able to assume that
        # there is at least one experiment owned by another user in the integration test
        # environment though.
        exp_id = self._create_experiment()
        exp_owner = self.service.experiment(exp_id).owner
        my_experiments = self.get_experiments(mine_only=True)
        my_experiment_uuids = []
        for experiment in my_experiments:
            self.assertEqual(
                experiment.owner,
                exp_owner,  # pylint: disable=no-member
                f"Only my experiments should be returned with "
                f"mine_only filter: {experiment.experiment_id}",
            )
            my_experiment_uuids.append(experiment.experiment_id)
        self.assertIn(
            exp_id,
            my_experiment_uuids,
            f"My experiment not returned with mine_only filter: {exp_id}",
        )

    def test_experiments_with_owner_filters_error(self):
        """Tests that exclude_mine and mine_only cannot both be True."""
        with self.assertRaisesRegex(
            ValueError, "exclude_mine and mine_only cannot both be True"
        ):
            self.get_experiments(exclude_mine=True, mine_only=True)

    def test_experiments_with_limit(self):
        """Test retrieving experiments with limit."""
        self._create_experiment()
        experiments = self.get_experiments(limit=1)
        self.assertEqual(1, len(experiments))

    def test_experiments_with_no_limit(self):
        """Test retrieving experiments with no limit."""
        tags = [str(uuid.uuid4())]
        exp_id = self._create_experiment(tags=tags)
        experiments = self.get_experiments(limit=None, tags=tags)
        self.assertEqual(1, len(experiments))
        self.assertEqual(exp_id, experiments[0].experiment_id)

    def test_experiments_with_sort_by(self):
        """Test retrieving experiments with sort_by."""
        tags = [str(uuid.uuid4())]
        exp1 = self._create_experiment(
            tags=tags,
            experiment_type=f"{self.default_exp_type}1",
            start_datetime=datetime.now() - timedelta(hours=1),
        )
        exp2 = self._create_experiment(
            tags=tags,
            experiment_type=f"{self.default_exp_type}2",
            start_datetime=datetime.now(),
        )
        exp3 = self._create_experiment(
            tags=tags,
            experiment_type=f"{self.default_exp_type}1",
            start_datetime=datetime.now() - timedelta(hours=2),
        )

        subtests = [
            (["experiment_type:asc"], [exp1, exp3, exp2]),
            (["experiment_type:desc"], [exp2, exp1, exp3]),
            (["start_datetime:asc"], [exp3, exp1, exp2]),
            (["start_datetime:desc"], [exp2, exp1, exp3]),
            (["experiment_type:asc", "start_datetime:asc"], [exp3, exp1, exp2]),
            (["experiment_type:asc", "start_datetime:desc"], [exp1, exp3, exp2]),
            (["experiment_type:desc", "start_datetime:asc"], [exp2, exp3, exp1]),
            (["experiment_type:desc", "start_datetime:desc"], [exp2, exp1, exp3]),
        ]

        for sort_by, expected in subtests:
            with self.subTest(sort_by=sort_by):
                experiments = self.get_experiments(
                    tags=tags,
                    sort_by=sort_by,
                    experiment_type_operator="like",
                    experiment_type=self.default_exp_type,
                )
                self.assertEqual(expected, [exp.experiment_id for exp in experiments])

    def test_experiments_with_bad_sort_by(self):
        """Test retrieving experiments with bad sort_by."""
        subtests = [
            "experiment_id:asc",
            "experiment_type",
            "experiment_type:foo",
            "foo:bar",
        ]

        for sort_by in subtests:
            with self.subTest(sort_by=sort_by):
                with self.assertRaises(ValueError):
                    self.get_experiments(sort_by=sort_by)

    def test_experiments_with_device_components(self):
        """Test filtering experiments with device components."""
        expr_id = self._create_experiment()
        self._create_analysis_result(
            exp_id=expr_id, device_components=self.device_components
        )
        experiments = self.get_experiments(device_components=self.device_components)
        self.assertIn(
            expr_id,
            [expr.experiment_id for expr in experiments],
            f"Experiment {expr_id} not found when filtering with "
            f"device components {self.device_components}",
        )

    def test_experiments_with_device_components_operator(self):
        """Test filtering experiments with device components operator."""
        backend_name, device_components = self._find_backend_device_components(3)
        if not backend_name:
            self.skipTest("Need at least 3 device components.")

        expr_id = self._create_experiment(backend_name=backend_name)
        self._create_analysis_result(
            exp_id=expr_id, device_components=device_components
        )
        experiments = self.get_experiments(
            device_components=device_components[:2],
            device_components_operator="contains",
        )

        self.assertIn(
            expr_id,
            [expr.experiment_id for expr in experiments],
            f"Experiment {expr_id} not found when filtering with "
            f"device components {device_components[:2]}",
        )

    def test_experiments_with_bad_components_operator(self):
        """Test filtering experiments with bad device components operator."""
        with self.assertRaises(ValueError):
            self.get_experiments(
                device_components=["Q1"], device_components_operator="foo"
            )

    def test_retrieve_experiment(self):
        """Test retrieving an experiment by its ID."""
        exp_id = self._create_experiment()
        rexp = self.service.experiment(exp_id)
        self.assertEqual(exp_id, rexp.experiment_id)
        for attr in ["hub", "group", "project", "owner", "share_level"]:
            self.assertIsNotNone(getattr(rexp, attr), f"{rexp} does not have a {attr}")

    def test_upload_experiment(self):
        """Test uploading an experiment."""
        exp_id = str(uuid.uuid4())
        new_exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type="qiskit_test",
                backend=self.backend.name,
                metadata={"foo": "bar"},
                experiment_id=exp_id,
                job_ids=["job1", "job2"],
                tags=["qiskit_test"],
                notes="some notes",
                share_level=ExperimentShareLevel.PROJECT,
                start_datetime=datetime.now(),
            ),
            provider=self.provider,
        )["uuid"]
        self.experiments_to_delete.append(new_exp_id)
        self.assertEqual(exp_id, new_exp_id)
        new_exp = self.service.experiment(new_exp_id)

        hub, group, project = list(self.provider._hgps)[0].split("/")
        self.assertEqual(hub, new_exp.hub)  # pylint: disable=no-member
        self.assertEqual(group, new_exp.group)  # pylint: disable=no-member
        self.assertEqual(project, new_exp.project)  # pylint: disable=no-member
        self.assertEqual("qiskit_test", new_exp.experiment_type)
        self.assertEqual(self.backend.name, new_exp.backend)
        self.assertEqual({"foo": "bar"}, new_exp.metadata)
        self.assertEqual(["job1", "job2"], new_exp.job_ids)
        self.assertEqual(["qiskit_test"], new_exp.tags)
        self.assertEqual("some notes", new_exp.notes)
        self.assertEqual(ExperimentShareLevel.PROJECT.value, new_exp.share_level)
        self.assertTrue(new_exp.creation_datetime)
        self.assertIsNotNone(
            new_exp.owner, "Owner should be set"
        )  # pylint: disable=no-member

        for dt_attr in [
            "start_datetime",
            "creation_datetime",
            "end_datetime",
            "updated_datetime",
        ]:
            datetime_attr = getattr(new_exp, dt_attr)
            self.assertTrue(datetime_attr is None or datetime_attr.tzinfo)

    def test_update_experiment(self):
        """Test updating an experiment."""
        new_exp_id = self._create_experiment()

        self.service.update_experiment(
            ExperimentData(
                experiment_id=new_exp_id,
                metadata={"foo": "bar"},
                job_ids=["job1", "job2"],
                tags=["qiskit_test"],
                notes="some notes",
                share_level=ExperimentShareLevel.PROJECT,
                end_datetime=datetime.now(),
            )
        )

        rexp = self.service.experiment(new_exp_id)
        self.assertEqual({"foo": "bar"}, rexp.metadata)
        self.assertEqual(["job1", "job2"], rexp.job_ids)
        self.assertEqual(["qiskit_test"], rexp.tags)
        self.assertEqual("some notes", rexp.notes)
        self.assertEqual(ExperimentShareLevel.PROJECT.value, rexp.share_level)
        self.assertTrue(rexp.end_datetime)

    def test_create_or_update_experiment(self):
        """Test updating an experiment."""
        new_exp_id = self.service.create_or_update_experiment(
            ExperimentData(experiment_type="qiskit_test", backend=self.backend.name),
            provider=self.provider,
        )

        self.service.create_or_update_experiment(
            ExperimentData(
                experiment_id=new_exp_id,
                metadata={"foo": "bar"},
                job_ids=["job1", "job2"],
                tags=["qiskit_test"],
                notes="some notes",
                share_level=ExperimentShareLevel.PROJECT,
                end_datetime=datetime.now(),
            ),
            create=False,
        )

        rexp = self.service.experiment(new_exp_id)
        self.assertEqual({"foo": "bar"}, rexp.metadata)
        self.assertEqual(["job1", "job2"], rexp.job_ids)
        self.assertEqual(["qiskit_test"], rexp.tags)
        self.assertEqual("some notes", rexp.notes)
        self.assertEqual(ExperimentShareLevel.PROJECT.value, rexp.share_level)
        self.assertTrue(rexp.end_datetime)

    def test_delete_experiment(self):
        """Test deleting an experiment."""
        new_exp_id = self._create_experiment(notes="delete me")

        with mock.patch("builtins.input", lambda _: "y"):
            self.service.delete_experiment(new_exp_id)

        with self.assertRaises(IBMExperimentEntryNotFound) as ex_cm:
            self.service.experiment(new_exp_id)
        self.assertIn("Not Found for url", ex_cm.exception.message)

    def test_upload_analysis_result(self):
        """Test uploading an analysis result."""
        exp_id = self._create_experiment()
        fit = dict(value=41.456, variance=4.051)
        result_id = str(uuid.uuid4())
        chisq = 1.3253
        aresult_id = self.service.create_analysis_result(
            AnalysisResultData(
                experiment_id=exp_id,
                result_type="qiskit_test",
                result_data=fit,
                device_components=self.device_components,
                tags=["qiskit_test"],
                quality=ResultQuality.GOOD,
                verified=True,
                result_id=result_id,
                chisq=chisq,
            )
        )

        rresult = self.service.analysis_result(aresult_id)
        self.assertEqual(exp_id, rresult.experiment_id)
        self.assertEqual("qiskit_test", rresult.result_type)
        self.assertEqual(fit, rresult.result_data)
        self.assertEqual(
            self.device_components, [str(comp) for comp in rresult.device_components]
        )
        self.assertEqual(["qiskit_test"], rresult.tags)
        self.assertEqual(ResultQuality.GOOD, rresult.quality)
        self.assertTrue(rresult.verified)
        self.assertEqual(result_id, rresult.result_id)
        self.assertEqual(chisq, rresult.chisq)

    def test_upload_multiple_analysis_results(self):
        """Test uploading multiple analysis results."""
        exp_id = self._create_experiment()
        num_results = 10
        results = []
        for i in range(num_results):
            fit = dict(value=i + 5, variance=2)
            chisq = 1.3253
            result = AnalysisResultData(
                experiment_id=exp_id,
                result_type=f"{i}_qiskit_test",
                result_data=fit,
                device_components=self.device_components,
                tags=["qiskit_test"],
                quality=ResultQuality.GOOD,
                verified=True,
                chisq=chisq,
            )
            results.append(result)
        self.service.create_analysis_results(results, blocking=True)
        rresults = self.service.analysis_results(
            experiment_id=exp_id, limit=num_results
        )
        self.assertEqual(len(rresults), num_results)
        for rresult in rresults:
            if rresult.result_type == "qiskit_test":
                print(rresult)
            i = int(re.match(r"(\d+)_", rresult.result_type)[1])
            fit = dict(value=i + 5, variance=2)
            self.assertEqual(exp_id, rresult.experiment_id)
            self.assertEqual(f"{i}_qiskit_test", rresult.result_type)
            self.assertEqual(fit, rresult.result_data)
            self.assertEqual(
                self.device_components,
                [str(comp) for comp in rresult.device_components],
            )
            self.assertEqual(["qiskit_test"], rresult.tags)
            self.assertEqual(ResultQuality.GOOD, rresult.quality)
            self.assertTrue(rresult.verified)
            self.assertEqual(chisq, rresult.chisq)

    def test_upload_multiple_analysis_results_nonblocking(self):
        """Test uploading multiple analysis results."""
        exp_id = self._create_experiment()
        num_results = 100
        results = []
        for i in range(num_results):
            fit = dict(value=i + 5, variance=2)
            chisq = 1.3253
            result = AnalysisResultData(
                experiment_id=exp_id,
                result_type=f"{i}_qiskit_test",
                result_data=fit,
                device_components=self.device_components,
                tags=["qiskit_test"],
                quality=ResultQuality.GOOD,
                verified=True,
                chisq=chisq,
            )
            results.append(result)
        handler = self.service.create_analysis_results(results, blocking=False)
        handler.block_for_save()
        rresults = self.service.analysis_results(
            experiment_id=exp_id, limit=num_results
        )
        self.assertEqual(len(rresults), num_results)
        for rresult in rresults:
            if rresult.result_type == "qiskit_test":
                print(rresult)
            i = int(re.match(r"(\d+)_", rresult.result_type)[1])
            fit = dict(value=i + 5, variance=2)
            self.assertEqual(exp_id, rresult.experiment_id)
            self.assertEqual(f"{i}_qiskit_test", rresult.result_type)
            self.assertEqual(fit, rresult.result_data)
            self.assertEqual(
                self.device_components,
                [str(comp) for comp in rresult.device_components],
            )
            self.assertEqual(["qiskit_test"], rresult.tags)
            self.assertEqual(ResultQuality.GOOD, rresult.quality)
            self.assertTrue(rresult.verified)
            self.assertEqual(chisq, rresult.chisq)

    def test_upload_multiple_analysis_results_failures(self):
        """Test uploading multiple analysis results."""
        exp_id = self._create_experiment()
        fake_exp_id = f"FAKE_ID_{exp_id}"
        num_results = 9
        results = []
        for i in range(num_results):
            fit = dict(value=i + 5, variance=2)
            chisq = 1.3253
            result = AnalysisResultData(
                experiment_id=exp_id if i % 2 == 0 else fake_exp_id,
                result_type=f"{i}_qiskit_test",
                result_data=fit,
                device_components=self.device_components,
                tags=["qiskit_test"],
                quality=ResultQuality.GOOD,
                verified=True,
                chisq=chisq,
            )
            results.append(result)
        save_status = self.service.create_analysis_results(results, blocking=True)
        self.assertEqual(len(save_status["running"]), 0)
        self.assertEqual(len(save_status["fail"]), num_results // 2)
        self.assertEqual(len(save_status["done"]), num_results - (num_results // 2))
        for result in save_status["done"]:
            i = int(re.match(r"(\d+)_", result[0].result_type)[1])
            self.assertEqual(i % 2, 0)
        for result in save_status["fail"]:
            i = int(re.match(r"(\d+)_", result["data"][0].result_type)[1])
            self.assertEqual(i % 2, 1)
            self.assertTrue(isinstance(result["exception"], IBMApiError))

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

    def test_create_or_update_analysis_result(self):
        """Test updating an analysis result."""
        experiment_id = self._create_experiment()
        result_type = "qiskit_test"
        result_data = {}
        result_id = self.service.create_or_update_analysis_result(
            AnalysisResultData(
                experiment_id=experiment_id,
                result_data=result_data,
                result_type=result_type,
            )
        )
        fit = dict(value=41.456, variance=4.051)
        chisq = 1.3253

        self.service.create_or_update_analysis_result(
            AnalysisResultData(
                result_id=result_id,
                result_data=fit,
                tags=["qiskit_test"],
                quality=ResultQuality.GOOD,
                verified=True,
                chisq=chisq,
            ),
            create=False,
        )

        rresult = self.service.analysis_result(result_id)
        self.assertEqual(result_id, rresult.result_id)
        self.assertEqual(fit, rresult.result_data)
        self.assertEqual(["qiskit_test"], rresult.tags)
        self.assertEqual(ResultQuality.GOOD, rresult.quality)
        self.assertTrue(rresult.verified)
        self.assertEqual(chisq, rresult.chisq)

    def test_analysis_results(self):
        """Test retrieving all analysis results."""
        result_id = self._create_analysis_result()
        results = self.service.analysis_results()
        found = False
        for res in results:
            self.assertIsInstance(res.verified, bool)
            self.assertIsInstance(res.result_data, dict)
            self.assertTrue(res.result_id, f"{res} does not have an uuid!")
            for dt_attr in ["creation_datetime", "updated_datetime"]:
                result_datetime = getattr(res, dt_attr)
                self.assertTrue(result_datetime is None or result_datetime.tzinfo)
            if res.result_id == result_id:
                found = True
        self.assertTrue(found)

    def test_analysis_results_device_components(self):
        """Test filtering analysis results with device components."""
        result_id = self._create_analysis_result(
            device_components=self.device_components
        )
        results = self.service.analysis_results(
            device_components=self.device_components
        )

        found = False
        for res in results:
            self.assertEqual(
                self.device_components, [str(comp) for comp in res.device_components]
            )
            if res.result_id == result_id:
                found = True
        self.assertTrue(
            found,
            f"Result {result_id} not found when filtering by "
            f"device components {self.device_components}",
        )

    def test_analysis_results_device_components_operator(self):
        """Test filtering analysis results with device components operator."""
        backend_name, device_components = self._find_backend_device_components(3)
        if not backend_name:
            self.skipTest("Need at least 3 device components.")

        expr_id = self._create_experiment(backend_name=backend_name)
        result_id = self._create_analysis_result(
            exp_id=expr_id, device_components=device_components
        )
        results = self.service.analysis_results(
            device_components=device_components[:2],
            device_components_operator="contains",
        )

        found = False
        for res in results:
            self.assertTrue(
                set(device_components[:2])
                <= {str(comp) for comp in res.device_components}
            )
            if res.result_id == result_id:
                found = True
        self.assertTrue(
            found,
            f"Result {result_id} not found when filtering by "
            f"device components {device_components[:2]}",
        )

    def test_analysis_results_experiment_id(self):
        """Test filtering analysis results with experiment id."""
        expr_id = self._create_experiment()
        result_id1 = self._create_analysis_result(exp_id=expr_id)
        result_id2 = self._create_analysis_result(exp_id=expr_id)

        results = self.service.analysis_results(experiment_id=expr_id)
        self.assertEqual(2, len(results))
        self.assertEqual({result_id1, result_id2}, {res.result_id for res in results})

    def test_analysis_results_with_created_at(self):
        """Test retrieving an analysis result by its created_at timestamp."""
        ref_start_dt = datetime.now()
        ref_start_dt = ref_start_dt.replace(tzinfo=tz.tzlocal())
        exp_id = self._create_experiment(start_datetime=ref_start_dt)
        result_id = self._create_analysis_result(exp_id=exp_id)

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
                analysis_results = self.service.analysis_results(
                    experiment_id=exp_id,
                    creation_datetime_after=start_dt,
                    creation_datetime_before=end_dt,
                )
                found = False
                for result in analysis_results:
                    if start_dt:
                        self.assertGreaterEqual(result.creation_datetime, start_dt)
                    if end_dt:
                        self.assertLessEqual(result.creation_datetime, end_dt)
                    if result.result_id == result_id:
                        found = True
                self.assertEqual(
                    found,
                    expected,
                    f"Analysis result {result_id} (not)found unexpectedly when filter using"
                    f"start_dt={start_dt}, end_dt={end_dt}. Found={found}",
                )

    def test_analysis_results_type(self):
        """Test filtering analysis results with type."""
        result_type = "qiskit_test"
        result_id = self._create_analysis_result(result_type=result_type)
        results = self.service.analysis_results(result_type=result_type)
        found = False
        for res in results:
            self.assertEqual(result_type, res.result_type)
            if res.result_id == result_id:
                found = True
        self.assertTrue(
            found,
            f"Result {result_id} not returned when filtering by " f"type {result_type}",
        )

    def test_analysis_results_type_operator(self):
        """Test filtering analysis results with type operator."""
        result_type = "qiskit_test_1234"
        result_id = self._create_analysis_result(result_type=result_type)

        results = self.service.analysis_results(
            result_type="foo", result_type_operator="like"
        )
        self.assertNotIn(result_id, [res["result_id"] for res in results])

        subtests = ["qiskit_test", "test_1234"]
        for filter_type in subtests:
            with self.subTest(filter_type=filter_type):
                results = self.service.analysis_results(
                    result_type=filter_type, result_type_operator="like"
                )

                found = False
                for res in results:
                    self.assertIn(filter_type, res.result_type)
                    if res.result_id == result_id:
                        found = True
                self.assertTrue(
                    found,
                    f"Result {result_id} not returned when filtering by "
                    f"type substring {filter_type}",
                )

    def test_analysis_results_bad_type_operator(self):
        """Test retrieving all experiments with a bad type operator."""
        with self.assertRaises(ValueError):
            self.service.analysis_results(result_type="foo", result_type_operator="bad")

    def test_analysis_results_quality(self):
        """Test filtering analysis results with quality."""
        expr_id = self._create_experiment()
        result_id1 = self._create_analysis_result(
            exp_id=expr_id, quality=ResultQuality.GOOD
        )
        result_id2 = self._create_analysis_result(
            exp_id=expr_id, quality=ResultQuality.BAD
        )
        result_id3 = self._create_analysis_result(
            exp_id=expr_id, quality=ResultQuality.UNKNOWN
        )

        subtests = [
            (ResultQuality.GOOD, {result_id1}),
            (ResultQuality.BAD.value, {result_id2}),
            ("unknown", {result_id3}),
            ([ResultQuality.UNKNOWN], {result_id3}),
            ([ResultQuality.GOOD, ResultQuality.UNKNOWN], {result_id1, result_id3}),
            (["Good", "Bad"], {result_id1, result_id2}),
            ([ResultQuality.UNKNOWN, ResultQuality.BAD], {result_id3, result_id2}),
            (
                [ResultQuality.GOOD, ResultQuality.BAD, ResultQuality.UNKNOWN],
                {result_id1, result_id2, result_id3},
            ),
        ]

        for quality, expected in subtests:
            with self.subTest(quality=quality):
                results = self.service.analysis_results(quality=quality)
                if not isinstance(quality, list):
                    quality = [quality]
                qual_set = []
                for qual in quality:
                    if isinstance(qual, str):
                        qual = ResultQuality(qual.upper())
                    qual_set.append(qual)
                res_ids = set()
                for res in results:
                    self.assertIn(res.quality, qual_set)
                    res_ids.add(res.result_id)
                self.assertTrue(
                    expected <= res_ids,
                    f"Result {expected} not returned "
                    f"when filter with quality {quality}",
                )

    def test_analysis_results_backend_name(self):
        """Test filtering analysis results with backend name."""
        result_id = self._create_analysis_result()
        results = self.service.analysis_results(backend_name=self.backend.name)
        self.assertIn(result_id, [res.result_id for res in results])

    def test_analysis_results_verified(self):
        """Test filtering analysis results with verified."""
        result_id = self._create_analysis_result(verified=True)
        results = self.service.analysis_results(verified=True)
        found = False
        for res in results:
            self.assertTrue(res.verified)
            if res.result_id == result_id:
                found = True
        self.assertTrue(
            found, f"Result {result_id} not found when " f"filtering with verified=True"
        )

    def test_analysis_results_with_tags(self):
        """Test filtering analysis results using tags."""
        ref_tags = ["qiskit_test", "foo"]
        result_id = self._create_analysis_result(tags=ref_tags)

        phantom_tag = uuid.uuid4().hex
        sub_tests = [
            (ref_tags, "AND", True),
            (ref_tags, "OR", True),
            (ref_tags[:1], "OR", True),
            (ref_tags + [phantom_tag], "AND", False),
            (ref_tags + [phantom_tag], "OR", True),
            ([phantom_tag], "OR", False),
        ]
        for tags, operator, found in sub_tests:
            with self.subTest(tags=tags, operator=operator):
                results = self.service.analysis_results(
                    tags=tags, tags_operator=operator
                )
                res_found = False
                for res in results:
                    msg = f"Tags {tags} not fond in result tags {res.tags}"
                    if operator == "AND":
                        self.assertTrue(all(f_tag in res.tags for f_tag in tags), msg)
                    else:
                        self.assertTrue(any(f_tag in res.tags for f_tag in tags), msg)
                    if res.result_id == result_id:
                        res_found = True
                self.assertTrue(
                    res_found == found,
                    f"Result tags {ref_tags} unexpectedly (not)found. Found={found}",
                )

    def test_analysis_results_with_limit(self):
        """Test retrieving analysis results with limit."""
        self._create_analysis_result()
        results = self.service.analysis_results(limit=1)
        self.assertEqual(1, len(results))

    def test_analysis_results_with_no_limit(self):
        """Test retrieving analysis results with no limit."""
        tags = [str(uuid.uuid4())]
        result_id = self._create_analysis_result(tags=tags)
        results = self.service.analysis_results(limit=None, tags=tags)
        self.assertEqual(1, len(results))
        self.assertEqual(result_id, results[0].result_id)

    def test_analysis_results_with_sort_by(self):
        """Test retrieving analysis results with sort_by."""
        tags = [str(uuid.uuid4())]
        backend, components = self._find_backend_device_components(3)
        backend_name = backend or self.backend.name
        device_components = components or self.device_components
        if len(device_components) < 3:
            device_components = [None] * 3  # Skip testing device components.
        device_components.sort()
        expr_id = self._create_experiment(backend_name=backend_name)

        res1 = self._create_analysis_result(
            exp_id=expr_id,
            tags=tags,
            result_type="qiskit_test1",
            device_components=device_components[2],
        )
        res2 = self._create_analysis_result(
            exp_id=expr_id,
            tags=tags,
            result_type="qiskit_test2",
            device_components=device_components[0],
        )
        res3 = self._create_analysis_result(
            exp_id=expr_id,
            tags=tags,
            result_type="qiskit_test1",
            device_components=device_components[1],
        )

        subtests = [
            (["result_type:asc"], [res3, res1, res2]),
            (["result_type:desc"], [res2, res3, res1]),
            (["creation_datetime:asc"], [res1, res2, res3]),
            (["creation_datetime:desc"], [res3, res2, res1]),
            (["result_type:asc", "creation_datetime:asc"], [res1, res3, res2]),
            (["result_type:asc", "creation_datetime:desc"], [res3, res1, res2]),
            (["result_type:desc", "creation_datetime:asc"], [res2, res1, res3]),
            (["result_type:desc", "creation_datetime:desc"], [res2, res3, res1]),
        ]
        if device_components[0]:
            subtests += [
                (["device_components:asc"], [res2, res3, res1]),
                (["device_components:desc"], [res1, res3, res2]),
                (["result_type:asc", "device_components:desc"], [res1, res3, res2]),
            ]

        for sort_by, expected in subtests:
            with self.subTest(sort_by=sort_by):
                results = self.service.analysis_results(tags=tags, sort_by=sort_by)
                self.assertEqual(expected, [res.result_id for res in results])

    def test_analysis_results_with_bad_sort_by(self):
        """Test retrieving analysis results with bad sort_by."""
        subtests = ["result_id:asc", "result_type", "result_type:foo", "foo:bar"]

        for sort_by in subtests:
            with self.subTest(sort_by=sort_by):
                with self.assertRaises(ValueError):
                    self.service.analysis_results(sort_by=sort_by)

    def test_analysis_results_with_creation_datetime(self):
        """Test retrieving analysis_results with creation_datetime"""
        # Create an analysis_result and get it back to get its creation_datetime value.
        result1_id = self._create_analysis_result()
        result1 = self.service.analysis_result(result1_id)
        self.assertIsNotNone(result1.creation_datetime)
        cdt1 = result1.creation_datetime
        # Assert that the UTC timestamp was converted to the local time.
        self.assertIsNotNone(cdt1.tzinfo)
        self.log.debug(
            "Created first analysis result %s with creation_datetime %s",
            result1_id,
            cdt1.isoformat(),
        )
        # Get the analysis result back using the exact creation timestamp
        # using both ge and le prefixes.
        results = self.service.analysis_results(
            creation_datetime_after=cdt1, creation_datetime_before=cdt1
        )
        # Chances are that we should only get exactly one analysis result
        # back but to be safe check for at least 1.
        self.assertGreaterEqual(len(results), 1, results)
        result_ids = [r.result_id for r in results]
        self.assertIn(result1_id, result_ids)
        # Create another analysis result on the same experiment.
        result2_id = self._create_analysis_result(exp_id=result1.experiment_id)
        result2 = self.service.analysis_result(result2_id)
        cdt2 = result2.creation_datetime
        # self.log.debug('Created second analysis result %s with creation_datetime %s',
        #                result2_id, cdt2.isoformat())
        # Get both results using their creation timestamps as a range.
        results = self.service.analysis_results(
            creation_datetime_after=cdt1, creation_datetime_before=cdt2
        )
        self.assertGreaterEqual(len(results), 2, results)
        result_ids = [r.result_id for r in results]
        for result_id in [result1_id, result2_id]:
            self.assertIn(result_id, result_ids)

    def test_delete_analysis_result(self):
        """Test deleting an analysis result."""
        result_id = self._create_analysis_result()
        with mock.patch("builtins.input", lambda _: "y"):
            self.service.delete_analysis_result(result_id)

        with self.assertRaises(IBMExperimentEntryNotFound):
            self.service.analysis_result(result_id)

    def test_backend_components(self):
        """Test retrieving all device components."""
        device_components = self.service.device_components()
        self.assertTrue(device_components)

    def test_backend_components_backend_name(self):
        """Test retrieving device components for a specific backend."""
        device_components = self.service.device_components()
        backend = list(device_components.keys())[0]
        backend_components = self.service.device_components(backend)
        self.assertEqual(device_components[backend], backend_components)

    def test_retrieve_backends(self):
        """Test retrieving all backends."""
        backends = self.service.backends()
        self.assertIn(self.backend.name, [b["name"] for b in backends])

    def test_create_figure(self):
        """Test creating a figure."""
        hello_bytes = str.encode("hello world")
        file_name = "hello_world.svg"
        figure_name = "hello.svg"
        with open(file_name, "wb") as file:
            file.write(hello_bytes)
        self.assertTrue(os.path.isfile(file_name), f"File {file_name} was not created")
        self.addCleanup(os.remove, file_name)

        subtests = [
            (hello_bytes, None),
            (hello_bytes, figure_name),
            (file_name, None),
            (file_name, file_name),
        ]

        for figure, figure_name in subtests:
            title = f"figure_name={figure_name}" if figure_name else f"figure={figure}"
            with self.subTest(title=title):
                expr_id = self._create_experiment()
                name, _ = self.service.create_figure(
                    experiment_id=expr_id, figure=figure, figure_name=figure_name
                )
                if figure_name:
                    self.assertEqual(figure_name, name)
                elif isinstance(figure, str):
                    self.assertEqual(figure, name)
                expr = self.service.experiment(expr_id)
                self.assertIn(name, expr.figure_names)

    def test_create_multiple_figures(self):
        """Test creating multiple figures at once."""
        file_names = []
        figure_names = []
        for name in ["hello world", "another test"]:
            bytes_data = str.encode(name)
            words = name.split(" ")
            file_name = f"{words[0]}_{words[1]}.svg"
            file_names.append(file_name)
            figure_names.append(f"{words[0]}.svg")
            with open(file_names[-1], "wb") as file:
                file.write(bytes_data)
            self.assertTrue(
                os.path.isfile(file_name), f"File {file_name} was not created"
            )
            self.addCleanup(os.remove, file_name)

        expr_id = self._create_experiment()
        figure_list = zip(file_names, figure_names)
        self.service.create_figures(experiment_id=expr_id, figure_list=figure_list)
        expr = self.service.experiment(expr_id)
        for name in figure_names:
            self.assertIn(name, expr.figure_names)

    def test_figure(self):
        """Test getting a figure."""
        hello_bytes = str.encode("hello world")
        figure_name = "hello.svg"
        expr_id = self._create_experiment()
        self.service.create_figure(
            experiment_id=expr_id, figure=hello_bytes, figure_name=figure_name
        )
        file_name = "hello_world.svg"
        self.addCleanup(os.remove, file_name)

        subtests = [(figure_name, None), (figure_name, file_name)]

        for figure_name, file_name in subtests:
            with self.subTest(file_name=file_name):
                fig = self.service.figure(expr_id, figure_name, file_name)
                if file_name:
                    with open(file_name, "rb") as file:
                        self.assertEqual(hello_bytes, file.read())
                else:
                    self.assertEqual(hello_bytes, fig)

    def test_update_figure(self):
        """Test uploading and updating plot data."""
        figure_name = "hello.svg"
        expr_id = self._create_experiment()
        self.service.create_figure(
            experiment_id=expr_id,
            figure=str.encode("hello world"),
            figure_name=figure_name,
        )
        friend_bytes = str.encode("hello friend!")
        name, _ = self.service.update_figure(
            experiment_id=expr_id, figure=friend_bytes, figure_name=figure_name
        )
        self.assertEqual(name, figure_name)
        rplot = self.service.figure(expr_id, figure_name)
        self.assertEqual(rplot, friend_bytes, "Retrieved plot not equal updated plot.")

    def test_create_or_update_figure(self):
        """Test uploading and updating plot data using create_or_update method"""
        figure_name = "hello.svg"
        expr_id = self._create_experiment()
        self.service.create_or_update_figure(
            experiment_id=expr_id,
            figure=str.encode("hello world"),
            figure_name=figure_name,
        )
        friend_bytes = str.encode("hello friend!")
        name, _ = self.service.create_or_update_figure(
            experiment_id=expr_id, figure=friend_bytes, figure_name=figure_name
        )
        self.assertEqual(name, figure_name)
        rplot = self.service.figure(expr_id, figure_name)
        self.assertEqual(rplot, friend_bytes, "Retrieved plot not equal updated plot.")

    def test_delete_figure(self):
        """Test deleting a figure."""
        figure_name = "hello.svg"
        expr_id = self._create_experiment()
        self.service.create_figure(
            experiment_id=expr_id,
            figure=str.encode("hello world"),
            figure_name=figure_name,
        )
        with mock.patch("builtins.input", lambda _: "y"):
            self.service.delete_figure(expr_id, figure_name)
        self.assertRaises(
            IBMExperimentEntryNotFound, self.service.figure, expr_id, figure_name
        )

    def test_experiment_coders(self):
        """Test custom encoder and decoder for an experiment."""
        metadata = {"complex": 2 + 3j, "numpy": np.zeros(2)}
        expr_id = self._create_experiment(
            metadata=metadata, json_encoder=ExperimentEncoder
        )
        rexp = self.service.experiment(expr_id, json_decoder=ExperimentDecoder)
        rmetadata = rexp.metadata
        self.assertEqual(metadata["complex"], rmetadata["complex"])
        self.assertTrue((metadata["numpy"] == rmetadata["numpy"]).all())

        new_metadata = {"complex": 4 + 5j, "numpy": np.ones(3)}
        self.service.update_experiment(
            ExperimentData(expr_id, metadata=new_metadata),
            json_encoder=ExperimentEncoder,
        )
        rexp = self.service.experiment(expr_id, json_decoder=ExperimentDecoder)
        rmetadata = rexp.metadata
        self.assertEqual(new_metadata["complex"], rmetadata["complex"])
        self.assertTrue((new_metadata["numpy"] == rmetadata["numpy"]).all())

    def test_analysis_result_coders(self):
        """Test custom encoder and decoder for an analysis result."""
        data = {"complex": 2 + 3j, "numpy": np.zeros(2), "numpy_int": np.int64(42)}
        result_id = self._create_analysis_result(
            result_data=data, json_encoder=ExperimentEncoder
        )
        rresult = self.service.analysis_result(
            result_id, json_decoder=ExperimentDecoder
        )
        rdata = rresult.result_data
        self.assertEqual(data["complex"], rdata["complex"])
        self.assertTrue((data["numpy"] == rdata["numpy"]).all())
        self.assertEqual(data["numpy_int"], rdata["numpy_int"])

        new_data = {"complex": 4 + 5j, "numpy": np.ones(3), "numpy_int": np.int64(127)}
        self.service.update_analysis_result(
            AnalysisResultData(result_id=result_id, result_data=new_data),
            json_encoder=ExperimentEncoder,
        )
        rresult = self.service.analysis_result(
            result_id, json_decoder=ExperimentDecoder
        )
        rdata = rresult.result_data
        self.assertEqual(new_data["complex"], rdata["complex"])
        self.assertTrue((new_data["numpy"] == rdata["numpy"]).all())
        self.assertEqual(new_data["numpy_int"], rdata["numpy_int"])

    def test_file_upload(self):
        """Test the file upload and download API"""
        exp_id = self._create_experiment()
        # basic functionality
        data = {"string": "a-string", "int": 174, "float": 3.14}
        filename = "data_file"
        self.service.file_upload(exp_id, filename, data)
        rdata = self.service.file_download(exp_id, filename)
        self.assertEqual(data, rdata)
        file_list = self.service.files(exp_id)["files"]
        self.assertEqual(len(file_list), 1)
        self.assertEqual(file_list[0]["Key"], filename + ".json")
        self.assertTrue(self.service.experiment_has_file(exp_id, filename + ".json"))

        # updating existing file
        data = {"string": "a-string", "int": 89, "float": 2.71, "null": None}
        filename = "data_file"
        self.service.file_upload(exp_id, filename, data)
        rdata = self.service.file_download(exp_id, filename)
        self.assertEqual(data, rdata)
        file_list = self.service.files(exp_id)["files"]
        self.assertEqual(len(file_list), 1)

        # adding additional file
        data = {"string": "b-string", "int": 10, "float": 0.333}
        filename = "another_data_file"
        self.service.file_upload(exp_id, filename, data)
        rdata = self.service.file_download(exp_id, filename)
        self.assertEqual(data, rdata)
        file_list = self.service.files(exp_id)["files"]
        self.assertEqual(len(file_list), 2)

    def test_file_upload_formats(self):
        """Test file upload/download for JSON and YAML formats"""
        exp_id = self._create_experiment()
        data = {"string": "b-string", "int": 10, "float": 0.333}
        yaml_data = yaml.dump(data)
        json_data = json.dumps(data)
        yaml_filename = "data.yaml"
        json_filename = "data.json"

        self.service.file_upload(exp_id, json_filename, json_data)
        rjson_data = self.service.file_download(exp_id, json_filename)
        self.assertEqual(data, rjson_data)

        self.service.file_upload(exp_id, yaml_filename, yaml_data)
        ryaml_data = self.service.file_download(exp_id, yaml_filename)
        self.assertEqual(data, ryaml_data)
        file_list = self.service.files(exp_id)["files"]
        self.assertEqual(len(file_list), 2)

    def _create_experiment(
        self,
        experiment_type: Optional[str] = None,
        backend_name: Optional[str] = None,
        json_encoder: Optional[json.JSONEncoder] = None,
        **kwargs,
    ) -> str:
        """Create a new experiment."""
        experiment_type = experiment_type or "qiskit_test"
        backend_name = backend_name or self.backend.name
        exp_id = self.service.create_experiment(
            ExperimentData(
                experiment_type=experiment_type,
                backend=backend_name,
                **kwargs,
            ),
            json_encoder=json_encoder,
        )["uuid"]
        self.experiments_to_delete.append(exp_id)
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

    def _find_backend_device_components(self, min_components):
        """Find a backend with the minimum number of device components."""
        backend_name = self.backend.name
        device_components = self.device_components
        if len(device_components) < min_components:
            all_components = self.service.device_components()
            for key, val in all_components.items():
                if len(val) >= min_components:
                    backend_name = key
                    device_components = val
                    break
        if len(device_components) < min_components:
            return None, None

        return backend_name, device_components


if __name__ == "__main__":
    unittest.main()
