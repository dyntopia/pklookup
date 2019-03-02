#!/usr/bin/env python3

from setuptools import setup

import pklookup

setup(
    name="pklookup",
    version=pklookup.__version__,
    entry_points={
        "console_scripts": ["pklookup = pklookup.cli:cli"]
    }
)
