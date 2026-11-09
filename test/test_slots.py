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

A theme's kinds are classes that only hold constants, and a kind that changes nothing about its
base, like a resource that is only a name, holds only the constants it inherits. So a class
counts as holding only constants when it and every class it builds on define nothing but
constants, and at least one constant between them.
"""

import importlib
import inspect
import pkgutil
import unittest

import microsponge
from microsponge.engine.civilizations.civilization import Civilization

PACKAGE = 'microsponge'
# A __main__ module starts the program when it's imported, so it's left out. It defines no classes.
STARTS_THE_PROGRAM = '__main__'
SLOTS = '__slots__'
SPECIAL_EDGES = '__'
# The classes the last test makes, and what it gives them.
PLAIN_CLASS = 'Plain'
CONSTANTS_CLASS = 'Constants'
INHERITS_CONSTANTS_CLASS = 'InheritsConstants'
ADDS_A_METHOD_CLASS = 'AddsAMethod'
A_METHOD = 'method'
OUTSIDE_CLASS = 'Outside'
A_CONSTANT = 'LIMIT'
A_VALUE = 1
A_NAME = 'Atlantis'
A_MISSPELLED_MEMBER = '_nmae'


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


def defined_names(kind):
    """Return the names a class and the classes it builds on define, leaving out Python's own like __doc__."""
    return [name for base in kind.__mro__ if base is not object for name in vars(base) if not name.startswith(SPECIAL_EDGES)]


def only_holds_constants(kind):
    """Return whether a class is just a group of named constants, its own or inherited, which nothing makes objects of."""
    names = defined_names(kind)
    return bool(names) and all(name.isupper() for name in names)


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
        inherits_constants = type(INHERITS_CONSTANTS_CLASS, (constants,), {})
        adds_a_method = type(ADDS_A_METHOD_CLASS, (constants,), {A_METHOD: len})
        self.assertTrue(needs_slots(plain))
        self.assertFalse(needs_slots(constants))
        self.assertFalse(needs_slots(outside))
        self.assertTrue(only_holds_constants(inherits_constants))
        self.assertFalse(only_holds_constants(adds_a_method))

    def test_an_object_cannot_be_given_a_member_its_class_does_not_declare(self):
        civilization = Civilization(A_NAME)
        with self.assertRaises(AttributeError):
            setattr(civilization, A_MISSPELLED_MEMBER, A_NAME)


if __name__ == '__main__':
    unittest.main()
