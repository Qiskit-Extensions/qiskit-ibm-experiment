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

# pylint: disable=method-hidden
# pylint: disable=arguments-differ

"""Utility functions for experiment testing."""

from typing import Any
import json
import os
import logging

import numpy as np


class ExperimentEncoder(json.JSONEncoder):
    """A test json encoder for experiments"""

    def default(self, o: Any) -> Any:
        if isinstance(o, complex):
            return {"__type__": "complex", "__value__": [o.real, o.imag]}
        if hasattr(o, "tolist"):
            return {"__type__": "array", "__value__": o.tolist()}

        return json.JSONEncoder.default(self, o)


class ExperimentDecoder(json.JSONDecoder):
    """JSON Decoder for Numpy arrays and complex numbers."""

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        """Object hook."""
        if "__type__" in obj:
            if obj["__type__"] == "complex":
                val = obj["__value__"]
                return val[0] + 1j * val[1]
            if obj["__type__"] == "array":
                return np.array(obj["__value__"])
        return obj


def setup_test_logging(logger: logging.Logger, filename: str):
    """Set logging to file and stdout for a logger.

    Args:
        logger: Logger object to be updated.
        filename: Name of the output file, if log to file is enabled.
    """
    # Set up formatter.
    log_fmt = f"{logger.name}.%(funcName)s:%(levelname)s:%(asctime)s:" " %(message)s"
    formatter = logging.Formatter(log_fmt)

    if os.getenv("STREAM_LOG", "true"):
        # Set up the stream handler.
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    if os.getenv("FILE_LOG", "false"):
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))
