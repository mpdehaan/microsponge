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

"""Every ERR_ constant lives in err_messages.py and every MSG_ constant in ui_strings.py, and each is used.

The modules hold all of the program's visible text, so that wording can be read in one place and
a string in a test can't be mistaken for a data key. Nothing else may define a constant with one of
the prefixes, the modules' own constants all carry theirs, a name never repeats its prefix's word
(no ERR_ERROR_LINE), and a constant nothing uses is removed.

HELP_ is the third prefix, for the help text of each screen. No module holds help text yet, so
until the first screen brings one, no module may define a HELP_ constant at all. When that module
arrives, it joins OWN_PREFIX and REDUNDANT_WORDS here.
"""

import ast
import os
import re
import unittest

import microsponge
from microsponge import err_messages, ui_strings

SOURCE_FOLDER = os.path.dirname(microsponge.__file__)
TEST_FOLDER = os.path.dirname(os.path.abspath(__file__))
TOOLS_FOLDER = os.path.join(os.path.dirname(TEST_FOLDER), 'tools')
PYTHON_SUFFIX = '.py'
ERROR_PREFIX = 'ERR_'
MESSAGE_PREFIX = 'MSG_'
HELP_PREFIX = 'HELP_'
PREFIXES = (ERROR_PREFIX, MESSAGE_PREFIX, HELP_PREFIX)
OWN_PREFIX = {err_messages.__file__: ERROR_PREFIX, ui_strings.__file__: MESSAGE_PREFIX}
# Names that are allowed to be used by a module's own code alone, since nothing else can see them.
PRIVATE_PREFIX = '_'
# Words a constant's name must not repeat after its prefix, like ERR_ERROR_LINE or MSG_MESSAGE. A message
# about an error belongs in err_messages, so the message words and the error words are redundant in both modules.
MESSAGE_WORDS = ('ERR', 'ERROR', 'ERRORS', 'MSG', 'MESSAGE', 'MESSAGES')
REDUNDANT_WORDS = {ERROR_PREFIX: MESSAGE_WORDS, MESSAGE_PREFIX: MESSAGE_WORDS}
SOURCE_SEPARATOR = '\n'


def python_files(folder):
    for root, _, names in os.walk(folder):
        for name in names:
            if name.endswith(PYTHON_SUFFIX):
                yield os.path.join(root, name)


def source_of(path):
    with open(path) as file:
        return file.read()


def assigned_names(nodes):
    return [target.id for node in nodes if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)]


def defined_constants(path):
    """Return the names assigned at the top of a module and in its classes."""
    tree = ast.parse(source_of(path))
    names = assigned_names(tree.body)
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            names += assigned_names(node.body)
    return names


def module_constants(path):
    """Return only the names assigned at the top of a module, outside its classes."""
    return assigned_names(ast.parse(source_of(path)).body)


def prefixed(names):
    return [name for name in names if name.startswith(PREFIXES)]


class TestMessageConstants(unittest.TestCase):

    def test_only_the_text_modules_define_prefixed_constants(self):
        for path in python_files(SOURCE_FOLDER):
            if path in OWN_PREFIX:
                continue
            with self.subTest(path=path):
                self.assertEqual(prefixed(defined_constants(path)), [])

    def test_each_module_holds_only_its_own_prefix(self):
        for path, prefix in OWN_PREFIX.items():
            with self.subTest(path=path):
                wrong = [name for name in module_constants(path) if not name.startswith(prefix) and not name.startswith(PRIVATE_PREFIX)]
                self.assertEqual(wrong, [])

    def test_no_name_repeats_its_prefix(self):
        for path, prefix in OWN_PREFIX.items():
            for name in module_constants(path):
                with self.subTest(name=name):
                    words = name[len(prefix):].split(PRIVATE_PREFIX)
                    self.assertFalse(any(word in REDUNDANT_WORDS[prefix] for word in words))

    def test_every_constant_is_used(self):
        others = []
        for folder in (SOURCE_FOLDER, TEST_FOLDER, TOOLS_FOLDER):
            others += [source_of(path) for path in python_files(folder) if path not in OWN_PREFIX]
        everything = SOURCE_SEPARATOR.join(others)
        for path, prefix in OWN_PREFIX.items():
            own = source_of(path)
            for name in defined_constants(path):
                if not name.startswith(prefix):
                    continue
                with self.subTest(name=name):
                    used_elsewhere = re.search(rf'\b{name}\b', everything)
                    used_at_home = len(re.findall(rf'\b{name}\b', own)) > 1
                    self.assertTrue(used_elsewhere or used_at_home)


if __name__ == '__main__':
    unittest.main()
