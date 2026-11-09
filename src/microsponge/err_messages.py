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

"""Every error message the program raises or reports, as templates filled in with .format().

Each constant starts with ERR_, and a message lives here and nowhere else, so that wording can be
kept consistent and a string in test code is never mistaken for a data key. The groups are by
the module that raises them, in the order of the modules' names.
"""


# version.py
ERR_BAD_VERSION_TEXT = 'version must be three integers separated by dots, such as 1.0.2, got {value!r}'
