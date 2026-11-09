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

"""Every class declares its data members with __slots__, so none can be added by mistake.

With __slots__, a class lists exactly what its objects hold, and assigning anything else, like a
misspelled name, raises an error. Each class in a hierarchy needs its own, even if empty, or its
objects quietly get a dictionary again.

The exceptions are classes that only hold constants, which are never made into objects, and
subclasses of classes from outside microsponge, such as Textual's screens, enums and exceptions,
whose bases already give every object a dictionary. A base from outside that declares its own
empty slots, like abc.ABC, doesn't excuse a class.

The program has no classes yet, so the last test makes classes of each kind and checks that the
rule tells them apart. When the first model class arrives, a test that one of its objects cannot
be given a new member belongs here too.
"""

import importlib
import inspect
import pkgutil
import unittest

import microsponge

PACKAGE = 'microsponge'
# A __main__ module starts the program when it's imported, so it's left out. It defines no classes.
STARTS_THE_PROGRAM = '__main__'
SLOTS = '__slots__'
# The classes the last test makes, and what it gives them.
PLAIN_CLASS = 'Plain'
CONSTANTS_CLASS = 'Constants'
OUTSIDE_CLASS = 'Outside'
A_CONSTANT = 'LIMIT'
A_VALUE = 1


def every_module():
    """Import and return every module in microsponge."""
    modules = [microsponge]
    for found in pkgutil.walk_packages(microsponge.__path__, prefix=f'{PACKAGE}.'):
        if not found.name.endswith(STARTS_THE_PROGRAM):
            modules.append(importlib.import_module(found.name))
    return modules


def classes_defined_in(module):
    return [kind for _, kind in inspect.getmembers(module, inspect.isclass) if kind.__module__ == module.__name__]


def extends_an_outside_class(kind):
    """Return whether a class builds on a class from outside microsponge that gives its objects a dictionary anyway.

    A base like abc.ABC declares empty slots itself, so classes built on it still need theirs.
    """
    return any(
        base is not object and not base.__module__.startswith(PACKAGE) and SLOTS not in vars(base)
        for base in kind.__mro__[1:]
    )


def only_holds_constants(kind):
    """Return whether a class is just a group of named constants, which nothing makes objects of."""
    own = [name for name in vars(kind) if not name.startswith('__')]
    return bool(own) and all(name.isupper() for name in own)


def needs_slots(kind):
    return not extends_an_outside_class(kind) and not only_holds_constants(kind)


class TestSlots(unittest.TestCase):

    def test_every_class_declares_its_slots(self):
        for module in every_module():
            for kind in classes_defined_in(module):
                if needs_slots(kind):
                    with self.subTest(module=module.__name__, kind=kind.__name__):
                        self.assertIn(SLOTS, vars(kind))

    def test_the_rule_recognizes_the_classes_it_checks(self):
        plain = type(PLAIN_CLASS, (), {})
        constants = type(CONSTANTS_CLASS, (), {A_CONSTANT: A_VALUE})
        outside = type(OUTSIDE_CLASS, (Exception,), {})
        self.assertTrue(needs_slots(plain))
        self.assertFalse(needs_slots(constants))
        self.assertFalse(needs_slots(outside))


if __name__ == '__main__':
    unittest.main()
