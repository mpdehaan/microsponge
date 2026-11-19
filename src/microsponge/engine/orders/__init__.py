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

"""Standing orders: what a civilization asks its helper AI to do, the things that take orders, and armies and divisions.

The model describes them under "Priorities and the helper AI" (`GAME_RULES.md`). The kinds of
order are definitions that a theme lists and may subclass (`order.py`), an order given in a
game is data (`given_order.py`), and the helper AI carries the orders out
(`players/hand.py`). The orders of `turns/orders.py` are the single actions of one turn, which
the helper AI uses to carry these out.
"""
