#!/usr/bin/env python3
# coding: utf-8

import sys
import os.path
from distutils.core import setup

with open(os.path.join(os.path.dirname(sys.argv[0]), 'egt'), "rt") as fd:
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
    url='https://github.com/ARPA-SIMC/provami/',
    requires=["tornado", "dballe"],
    license="http://www.gnu.org/licenses/gpl-3.0.html",
    packages=['dballe_web'],
    scripts=['dballe-web'],
)
