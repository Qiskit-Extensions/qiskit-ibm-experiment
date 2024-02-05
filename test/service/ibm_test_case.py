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

"""Custom TestCase for IBM Provider."""

import inspect
import logging
import os
import unittest
import warnings

from test.utils.utils import setup_test_logging

import fixtures
import testtools

from qiskit_ibm_experiment import QISKIT_IBM_EXPERIMENT_LOGGER_NAME


# Note: this code is largely based on how qiskit-experiments sets up its
# TestCase subclass (which was based on how Qiskit set its up).

# Fail tests that take longer than this
TEST_TIMEOUT = int(os.environ.get("TEST_TIMEOUT", 60))
# Use testtools by default as a (mostly) drop in replacement for
# unittest's TestCase. This will enable the fixtures used for capturing stdout
# stderr, and pylogging to attach the output to stestr's result stream.
USE_TESTTOOLS = os.environ.get("QE_USE_TESTTOOLS", "TRUE").lower() not in (
    "false",
    "0",
    "no",
)


def create_base_test_case(use_testtools: bool) -> unittest.TestCase:
    """Create the base test case class for package tests

    This function produces the base class for qiskit-experiments tests using
    either ``unittest.TestCase`` or ``testtools.TestCase`` for the base class.
    The creation of the class is done in this function rather than directly
    executed in the module so that, even when ``USE_TESTTOOLS`` is true, a
    ``unittest`` base class can be produced for ``test_base.py`` to check that
    no hard-dependence on ``testtools`` has been introduced.
    """
    if use_testtools:

        class BaseTestCase(testtools.TestCase):
            """Base test class."""

            # testtools maintains their own version of assert functions which mostly
            # behave as value adds to the std unittest assertion methods. However,
            # for assertEquals and assertRaises modern unittest has diverged from
            # the forks in testtools and offer more (or different) options that are
            # incompatible testtools versions. Just use the stdlib versions so that
            # our tests work as expected.
            assertRaises = unittest.TestCase.assertRaises
            assertEqual = unittest.TestCase.assertEqual

            def setUp(self):
                super().setUp()
                if os.environ.get("QISKIT_TEST_CAPTURE_STREAMS"):
                    stdout = self.useFixture(fixtures.StringStream("stdout")).stream
                    self.useFixture(fixtures.MonkeyPatch("sys.stdout", stdout))
                    stderr = self.useFixture(fixtures.StringStream("stderr")).stream
                    self.useFixture(fixtures.MonkeyPatch("sys.stderr", stderr))
                    self.useFixture(
                        fixtures.LoggerFixture(nuke_handlers=False, level=None)
                    )

    else:

        class BaseTestCase(unittest.TestCase):
            """Base test class."""

            def useFixture(self, fixture):  # pylint: disable=invalid-name
                """Shim so that useFixture can be called in subclasses

                useFixture is a testtools.TestCase method. The actual fixture is
                not used when using unittest.
                """

    class QIETestCase(BaseTestCase):
        """qiskit-ibm-experiment specific extra functionality for test cases."""

        def setUp(self):
            super().setUp()
            self.useFixture(fixtures.Timeout(TEST_TIMEOUT, gentle=True))

        @classmethod
        def setUpClass(cls):
            """Set-up test class."""
            super().setUpClass()
            cls.log = logging.getLogger(cls.__name__)
            filename = f"{os.path.splitext(inspect.getfile(cls))[0]}s.log"
            setup_test_logging(cls.log, filename)
            cls._set_logging_level(logging.getLogger(QISKIT_IBM_EXPERIMENT_LOGGER_NAME))

            warnings.filterwarnings("error", category=DeprecationWarning)
            # Tests should not generate any warnings unless testing those
            # warnings. In that case, the test should catch the warning
            # assertWarns or warnings.catch_warnings.
            warnings.filterwarnings("error", module="qiskit_ibm_experiment")

        @classmethod
        def simple_job_callback(cls, job_id, job_status, job, **kwargs):
            """A callback function that logs current job status."""
            # pylint: disable=unused-argument
            queue_info = kwargs.get("queue_info", "unknown")
            cls.log.info(
                "Job %s status is %s, queue_info is %s", job_id, job_status, queue_info
            )

        @classmethod
        def _set_logging_level(cls, logger: logging.Logger) -> None:
            """Set logging level for the input logger.

            Args:
                logger: Logger whose level is to be set.
            """
            if logger.level is logging.NOTSET:
                try:
                    logger.setLevel(cls.log.level)
                except Exception as ex:  # pylint: disable=broad-except
                    logger.warning(
                        'Error while trying to set the level for the "%s" logger to %s. %s.',
                        logger,
                        os.getenv("LOG_LEVEL"),
                        str(ex),
                    )
            if not any(
                isinstance(handler, logging.StreamHandler)
                for handler in logger.handlers
            ):
                logger.addHandler(logging.StreamHandler())
                logger.propagate = False

    return QIETestCase


IBMTestCase = create_base_test_case(USE_TESTTOOLS)
