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
from cards import Cards, Card
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
        self.cards = Cards()
        self.cards.open(':memory:')

    def tearDown(self):
        self.cards.close()

    def test_getCard(self):
        card1 = Card(1, 'question', 'answer', 'qhint', 'ahint', 13)
        card2 = Card(2, 'frage', 'antwort', 'qhint', 'ahint2', 20)
        id1 = self.cards.addCard(card1)
        id2 = self.cards.addCard(card2)
        card1a = self.cards.getCard(id1)
        card2a = self.cards.getCard(id2)
        self.assertEqual(card1, card1a)
        self.assertEqual(card2, card2a)


    def test_getCardCount(self):
        self.cards.addCard(Card(None, 'co', 'tutaj'))
        self.cards.addCard(Card(None, 'ale', 'fajnie'))
        self.assertEqual(self.cards.getCardsCount(), 2)


    def test_deleteCard(self):
        id1 = self.cards.addCard(Card(None, 'one', 'eins'))
        id2 = self.cards.addCard(Card(None, 'two', 'zwei'))
        id3 = self.cards.addCard(Card(None, 'three', 'drei'))
        # delete card 1, check if other exist
        self.cards.deleteCard(id1)
        self.assertFalse(self.cards.existsCard(id1))
        self.assertTrue(self.cards.existsCard(id2))
        self.assertTrue(self.cards.existsCard(id3))
        # add and delete next card
        id4 = self.cards.addCard(Card(4, 'four', 'vier'))
        self.cards.deleteCard(id4)
        self.assertFalse(self.cards.existsCard(id4))
        self.assertTrue(self.cards.existsCard(id2))
        self.assertTrue(self.cards.existsCard(id3))


    def test_updateCard(self):
        id1 = self.cards.addCard(Card(None, 'one', 'eins'))
        id2 = self.cards.addCard(Card(None, 'two', 'zwei'))
        id3 = self.cards.addCard(Card(None, 'three', 'drei'))
        # update second card and check if update is successful
        # and the other cards are intact
        self.cards.updateCard(Card(id2, 'two!', 'zwei!'))
        self.assertEqual(self.cards.getCard(id2), Card(id2, 'two!', 'zwei!'))
        self.assertEqual(self.cards.getCard(id1), Card(id1, 'one', 'eins'))
        self.assertEqual(self.cards.getCard(id3), Card(id3, 'three', 'drei'))


    def test_getCardHeaders(self):
        id1 = self.cards.addCard(Card(None, 'one', 'eins'))
        id2 = self.cards.addCard(Card(None, 'two', 'zwei'))
        id3 = self.cards.addCard(Card(None, 'three', 'drei'))
        id4 = self.cards.addCard(Card(None, 'four', 'vier'))
        id5 = self.cards.addCard(Card(None, 'five', 'fuenf'))
        id6 = self.cards.addCard(Card(None, 'six', 'sechs'))
        id7 = self.cards.addCard(Card(None, 'seven', 'sieben'))
        id8 = self.cards.addCard(Card(None, 'eight', 'acht'))
        id9 = self.cards.addCard(Card(None, 'nine', 'neun'))
        # retrieve card from rownum 0 to 0
        cards = self.cards.getCardHeaders('', 0, 1)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0], (1, 'one'))
        # retrieve cards from rownum 1 to 1
        cards = self.cards.getCardHeaders('', 1, 2)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0], (2, 'two'))
        # retrieve cards from rownum 2 to 4
        cards = self.cards.getCardHeaders('', 2, 6)
        self.assertEqual(len(cards), 4)
        self.assertEqual(cards[0], (3, 'three'))
        self.assertEqual(cards[1], (4, 'four'))
        self.assertEqual(cards[2], (5, 'five'))
        self.assertEqual(cards[3], (6, 'six'))

        # delete some and check retrieve again
        # retrieve cards < 7
        self.cards.deleteCard(id3)
        self.cards.deleteCard(id4)
        cards = self.cards.getCardHeaders('ID < 7', 2, 4)
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0], (5, 'five'))
        self.assertEqual(cards[1], (6, 'six'))

        # add some cards and check retrieve again
        # retrieve last 3 cards
        id10 = self.cards.addCard(Card(None, 'ten', 'zehn'))
        id11 = self.cards.addCard(Card(None, 'eleven', 'einzehn'))
        id12 = self.cards.addCard(Card(None, 'twelve', 'zwoelf'))
        cards = self.cards.getCardHeaders('', 7, 13)
        self.assertEqual(len(cards), 3)
        self.assertEqual(cards[0], (id10, 'ten'))
        self.assertEqual(cards[1], (id11, 'eleven'))
        self.assertEqual(cards[2], (id12, 'twelve'))

        # check for query when no range is added
        cards = self.cards.getCardHeaders()
        self.assertEqual(len(cards), 10)

        # check for assertion error when invalid minrow, maxrow
        self.assertRaises(AssertionError, self.cards.getCardHeaders, '', 4, 1)



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
