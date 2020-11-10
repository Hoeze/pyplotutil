#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

requirements = [
    "seaborn",
    "numpy",
    "pandas",
    "scikit-learn",
]

test_requirements = [
]


setup(
    name='pyplotutil',
    version='0.0.1',
    description="Python plot utilities",
    author="Florian Hölzlwimmer",
    author_email='git.ich@frhoelzlwimmer.de',
    url='https://github.com/Hoeze/pyplotutil',
    long_description="Python plot utilities",
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        "develop": ["bumpversion",
                    "wheel",
                    "pytest",
                    "pytest-pep8",
                    "pytest-cov"],
    },
    license="MIT license",
    zip_safe=False,
    test_suite='tests',
    tests_require=test_requirements
)
