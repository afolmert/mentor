#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Adam Folmert <afolmert@gmail.com>
#
# This file is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
#
"""
This is a test file for cards module.
"""

import unittest
from database import CardDb, Card
from utils import log


# TODO
# define setup method to automatically setup database in memoery and provide
# cards object

class TestCard(unittest.TestCase):

    def test_equals(self):
        card1 = Card(None, 'ala', 'ma', 'ala2', 'dupa3', 1)
        card2 = Card(None, 'ala', 'ma', 'ala2', 'dupa3', 1)
        self.assertEqual(card1, card2)


class TestCards(unittest.TestCase):



    def setUp(self):
        self.cards = CardDb()
        self.cards.open(':memory:')

    def tearDown(self):
        self.cards.close()

    def test_get_card(self):
        card1 = Card(1, 'question', 'answer', 'qhint', 'ahint', 13)
        card2 = Card(2, 'frage', 'antwort', 'qhint', 'ahint2', 20)
        id1 = self.cards.add_card(card1)
        id2 = self.cards.add_card(card2)
        card1a = self.cards.get_card(id1)
        card2a = self.cards.get_card(id2)
        self.assertEqual(card1, card1a)
        self.assertEqual(card2, card2a)


    def test_get_card_count(self):
        self.cards.add_card(Card(None, 'co', 'tutaj'))
        self.cards.add_card(Card(None, 'ale', 'fajnie'))
        self.assertEqual(self.cards.get_cards_count(), 2)


    def test_delete_card(self):
        id1 = self.cards.add_card(Card(None, 'one', 'eins'))
        id2 = self.cards.add_card(Card(None, 'two', 'zwei'))
        id3 = self.cards.add_card(Card(None, 'three', 'drei'))
        # delete card 1, check if other exist
        self.cards.delete_card(id1)
        self.assertFalse(self.cards.exists_card(id1))
        self.assertTrue(self.cards.exists_card(id2))
        self.assertTrue(self.cards.exists_card(id3))
        # add and delete next card
        id4 = self.cards.add_card(Card(4, 'four', 'vier'))
        self.cards.delete_card(id4)
        self.assertFalse(self.cards.exists_card(id4))
        self.assertTrue(self.cards.exists_card(id2))
        self.assertTrue(self.cards.exists_card(id3))


    def test_update_card(self):
        id1 = self.cards.add_card(Card(None, 'one', 'eins'))
        id2 = self.cards.add_card(Card(None, 'two', 'zwei'))
        id3 = self.cards.add_card(Card(None, 'three', 'drei'))
        # update second card and check if update is successful
        # and the other cards are intact
        self.cards.update_card(Card(id2, 'two!', 'zwei!'))
        self.assertEqual(self.cards.get_card(id2), Card(id2, 'two!', 'zwei!'))
        self.assertEqual(self.cards.get_card(id1), Card(id1, 'one', 'eins'))
        self.assertEqual(self.cards.get_card(id3), Card(id3, 'three', 'drei'))


    def test_get_card_headers(self):
        id1 = self.cards.add_card(Card(None, 'one', 'eins'))
        id2 = self.cards.add_card(Card(None, 'two', 'zwei'))
        id3 = self.cards.add_card(Card(None, 'three', 'drei'))
        id4 = self.cards.add_card(Card(None, 'four', 'vier'))
        id5 = self.cards.add_card(Card(None, 'five', 'fuenf'))
        id6 = self.cards.add_card(Card(None, 'six', 'sechs'))
        id7 = self.cards.add_card(Card(None, 'seven', 'sieben'))
        id8 = self.cards.add_card(Card(None, 'eight', 'acht'))
        id9 = self.cards.add_card(Card(None, 'nine', 'neun'))
        # retrieve card from rownum 0 to 0
        cards = self.cards.get_card_headers('', 0, 1)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0], (1, 'one'))
        # retrieve cards from rownum 1 to 1
        cards = self.cards.get_card_headers('', 1, 2)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0], (2, 'two'))
        # retrieve cards from rownum 2 to 4
        cards = self.cards.get_card_headers('', 2, 6)
        self.assertEqual(len(cards), 4)
        self.assertEqual(cards[0], (3, 'three'))
        self.assertEqual(cards[1], (4, 'four'))
        self.assertEqual(cards[2], (5, 'five'))
        self.assertEqual(cards[3], (6, 'six'))

        # delete some and check retrieve again
        # retrieve cards < 7
        self.cards.delete_card(id3)
        self.cards.delete_card(id4)
        cards = self.cards.get_card_headers('ID < 7', 2, 4)
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0], (5, 'five'))
        self.assertEqual(cards[1], (6, 'six'))

        # add some cards and check retrieve again
        # retrieve last 3 cards
        id10 = self.cards.add_card(Card(None, 'ten', 'zehn'))
        id11 = self.cards.add_card(Card(None, 'eleven', 'einzehn'))
        id12 = self.cards.add_card(Card(None, 'twelve', 'zwoelf'))
        cards = self.cards.get_card_headers('', 7, 13)
        self.assertEqual(len(cards), 3)
        self.assertEqual(cards[0], (id10, 'ten'))
        self.assertEqual(cards[1], (id11, 'eleven'))
        self.assertEqual(cards[2], (id12, 'twelve'))

        # check for query when no range is added
        cards = self.cards.get_card_headers()
        self.assertEqual(len(cards), 10)

        # check for assertion error when invalid minrow, maxrow
        self.assertRaises(AssertionError, self.cards.get_card_headers, '', 4, 1)



    # TODO
    # write a model using cards
    # a list control
    # and a list with text boxes
    # import cards from file export to file
    # adding modifing deleting
    # q a in separate text boxes
    #
    #


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCard))
    suite.addTest(unittest.makeSuite(TestCards))
    return suite
