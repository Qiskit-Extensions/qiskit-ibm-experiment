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
from datetime import timedelta, datetime
from test.service.ibm_test_case import IBMTestCase
import pandas as pd
from qiskit_ibm_experiment import IBMExperimentService, AnalysisResultData
from qiskit_ibm_experiment.service.constants import RESULT_QUALITY_FROM_DATAFRAME


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

    def test_dataframe_to_analysis_result_list(self):
        """Test conversion from dataframe to result list"""
        num_values = 2
        analysis_result_values = [
            {"str": "foo", "float": 3.14},
            {"int": 3, "float": 2.78},
        ]
        result_ids = [
            "9347d04d97464c5c80bf10b064064914",
            "ca2a0a92d4224ea1802c48d1785a6ce7",
        ]

        experiment_ids = [
            "4347d04d97364c5c80bf10b064064914",
            "ba2a0a92d4224ea1802c48d1785a6ce8",
        ]

        tags = [["qiskit_test", "foo"], []]
        result_types = ["type_A", "type_B"]
        result_quality = ["good", "bad"]
        backends = ["backend1", "backend2"]
        device_components = [["Q0", "Q1"], ["Q2"]]
        experiments = ["T1", "T2"]
        chisqs = [0.3, 0.5]
        sources = ["qiskit", "qiskit"]
        extras = [None, None]
        created_times = [
            datetime.now() - timedelta(days=1),
            datetime.now() - timedelta(days=2),
        ]
        d = {
            "_result_id": result_ids,
            "_experiment_id": experiment_ids,
            "_tags": tags,
            "value": analysis_result_values,
            "name": result_types,
            "quality": result_quality,
            "components": device_components,
            "backend": backends,
            "experiment": experiments,
            "created_time": created_times,
            "chisq": chisqs,
            "_source": sources,
            "_extra": extras,
        }
        df = pd.DataFrame(data=d)
        results = IBMExperimentService.dataframe_to_analysis_result_list(df)
        expected_results = [
            AnalysisResultData(
                result_id=result_ids[i],
                experiment_id=experiment_ids[i],
                result_data={
                    "_value": analysis_result_values[i],
                    "_experiment": experiments[i],
                    "_source": sources[i],
                    "_extra": extras[i],
                },
                result_type=result_types[i],
                quality=RESULT_QUALITY_FROM_DATAFRAME[result_quality[i]],
                backend_name=backends[i],
                creation_datetime=created_times[i],
                device_components=device_components[i],
                tags=tags[i],
                chisq=chisqs[i],
            )
            for i in range(num_values)
        ]
        for (result, expected_result) in zip(results, expected_results):
            self.assertEqual(result, expected_result)

        result_df = IBMExperimentService.analysis_result_list_to_dataframe(results)
        self.assertEqual(result_df.to_dict(), df.to_dict())


if __name__ == "__main__":
    unittest.main()
