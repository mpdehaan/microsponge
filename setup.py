# microsponge: a strategy game
# Copyright (C) 2026  Michael DeHaan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Installs microsponge.

    pip install .

This adds the microsponge command, which starts the game.
"""

import re
from pathlib import Path

from setuptools import find_packages, setup

HERE = Path(__file__).resolve().parent
# The version is read from the code's own version.py, as text, so that installing doesn't run it.
VERSION_FILE = HERE / 'src' / 'microsponge' / 'support' / 'version.py'
VERSION_LINE = re.compile(r"^VERSION = '([^']+)'$", re.MULTILINE)
VERSION = VERSION_LINE.search(VERSION_FILE.read_text(encoding='utf-8')).group(1)

setup(
    name='microsponge',
    version=VERSION,
    description='A turn based strategy game played in a text UI',
    long_description=(HERE / 'README.md').read_text(encoding='utf-8'),
    long_description_content_type='text/markdown',
    author='Michael DeHaan',
    license='GPL-3.0-or-later',
    python_requires='>=3.15',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=(HERE / 'requirements.txt').read_text(encoding='utf-8').split(),
    entry_points={'console_scripts': ['microsponge = microsponge.cli:main']},
)
