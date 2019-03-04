#!/usr/bin/env python3
# coding: utf-8

import sys
import os.path
from setuptools import setup

with open("dballe-web") as fd:
    for line in fd:
        if line.startswith('VERSION ='):
            version = eval(line.split(' = ')[-1])

setup(
    name='dballe-web',
    version=version,
    description="Graphical interactive interface to DB-All.e",
    # long_description=''
    author=['Enrico Zini'],
    author_email=['enrico@enricozini.org'],
    url='https://github.com/ARPA-SIMC/dballe-web/',
    requires=["tornado", "dballe"],
    license="http://www.gnu.org/licenses/gpl-3.0.html",
    packages=['dballe_web'],
    scripts=['dballe-web'],
    include_package_data=True,
)
