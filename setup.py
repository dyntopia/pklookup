#!/usr/bin/env python3

from typing import Iterator
from setuptools import setup

import pklookup


def get_requirements(filename: str) -> Iterator[str]:
    with open(filename, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line and not line.startswith("#"):
                name, *_ = line.split("=")[0].split()
                yield name


setup(
    name="pklookup",
    version=pklookup.__version__,
    install_requires=list(get_requirements("requirements/requirements.txt")),
    entry_points={
        "console_scripts": ["pklookup = pklookup.cli:cli"]
    }
)
