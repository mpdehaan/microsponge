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

"""What the tools that report on a theme share: finding the theme named on the command line, and printing a report."""

from microsponge.engine.kinds.kind import shown_name
from microsponge.themes import THEMES
from microsponge.ui_strings import MSG_LIST_SEPARATOR, MSG_NAME_ONE_THEME

SUCCEEDED = 0
FAILED = 1
# The command line flag that asks for Markdown, to paste into a theme's guide.
MARKDOWN_FLAG = '--markdown'


def theme_called(name):
    """Return the theme whose name as people read it is name, or None."""
    for theme in THEMES:
        if shown_name(theme) == name:
            return theme
    return None


def theme_names():
    return MSG_LIST_SEPARATOR.join(shown_name(theme) for theme in THEMES)


def parse(arguments):
    """Return (the theme named, whether Markdown was asked for) from the command line's arguments, with None for no theme or one that does not exist."""
    markdown = MARKDOWN_FLAG in arguments
    names = [argument for argument in arguments if argument != MARKDOWN_FLAG]
    theme = theme_called(names[0]) if len(names) == 1 else None
    return theme, markdown


def run_theme_tool(*, arguments, report):
    """Print a tool's report on the one theme named in the command line's arguments, as Markdown when asked, and return the exit code; with no theme, or one that does not exist, print the themes there are and fail."""
    theme, markdown = parse(arguments)
    if theme is None:
        print(MSG_NAME_ONE_THEME.format(themes=theme_names(), flag=MARKDOWN_FLAG))
        return FAILED
    for line in report(theme, markdown=markdown):
        print(line)
    return SUCCEEDED

