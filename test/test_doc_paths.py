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

"""Every source, test, tool and screenshot path the documents name exists.

The documents for Claude and for people name files in backticks, like `src/microsponge/cli.py`
or `tools/loose_strings.py`. When a module moves, those names go stale unless something notices,
so this test reads every document and checks that each such path is a real file, so that a rename
has to carry its documentation with it. A new document for people, like a guide, is added to
DOCUMENTS when it's written.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_DOCUMENT = ROOT / 'CLAUDE.md'
DOCUMENTS = [
    CLAUDE_DOCUMENT,
    ROOT / 'ARCHITECTURE.md',
    ROOT / 'GAME_RULES.md',
    ROOT / 'IDEAS.md',
    ROOT / 'INSTALL.md',
    ROOT / 'PHILOSOPHY.md',
    ROOT / 'README.md',
    *sorted((ROOT / '.claude').glob('*.md')),
]
# A path in backticks that starts in one of the repository's folders and ends in a file suffix.
PATH_IN_BACKTICKS = re.compile(r'`((?:src|test|tools|docs)/[A-Za-z0-9_./-]+\.(?:py|svg|sh|md))`')
ENCODING = 'utf-8'
NO_PATHS = 0


def paths_named_in(document):
    """Return the repository paths a document names in backticks, in order, without repeats."""
    found = PATH_IN_BACKTICKS.findall(document.read_text(encoding=ENCODING))
    return list(dict.fromkeys(found))


class TestDocumentPaths(unittest.TestCase):

    def test_every_path_the_documents_name_exists(self):
        for document in DOCUMENTS:
            for path in paths_named_in(document):
                with self.subTest(document=document.relative_to(ROOT), path=path):
                    self.assertTrue((ROOT / path).is_file(), path)

    def test_the_documents_name_some_paths(self):
        # If the pattern stopped matching, the test above would pass by checking nothing.
        self.assertGreater(len(paths_named_in(CLAUDE_DOCUMENT)), NO_PATHS)


if __name__ == '__main__':
    unittest.main()
