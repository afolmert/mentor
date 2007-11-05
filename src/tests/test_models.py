#!/usr/bin/env python
# -*- coding: iso-8859-2 -*-
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
#
"""This is the test module for models used in Mentor GUI"""


from PyQt4.QtCore import *
import unittest
from models import CardModel
from utils import log

class DummyView(QObject):

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.model = None
        self.got_reset = False
        self.got_dataChanged = False

    def setModel(self, model):
        self.model = model
        self.connect(self.model, SIGNAL('modelReset()'), self.on_reset)
        self.connect(self.model, SIGNAL('dataChanged(QModelIndex)'), self.on_dataChanged)

    def on_reset(self):
        self.got_reset = True

    def on_dataChanged(self, index):
        self.got_dataChanged = True



class TestCardModel(unittest.TestCase):

    def setUp(self):

        self.model = CardModel()
        self.model.open(':memory:')
        self.view = DummyView()
        self.view.setModel(self.model)


    def tearDown(self):
        self.model.close()


    def testFilePath(self):
        # test on open model
        self.assertEqual(self.model.filepath(), ':memory:')
        # test on closed model
        self.model.close()
        self.assertEqual(self.model.filepath(), None)


    def testIsActive(self):
        self.assertEqual(self.model.isActive(), True)
        # test on closed model
        self.model.close()
        self.assertEqual(self.model.isActive(), False)


    def testColumnCount(self):
        # test on empty model
        self.assertEqual(self.model.columnCount(), 1)
        # test on closed model
        self.model.close()
        self.assertEqual(self.model.columnCount(), 0)


    def testRowCount(self):
        # test on empty database
        self.assertEqual(self.model.rowCount(), 0)
        # add three empty rows
        self.model.addNewCard()
        self.model.addNewCard()
        self.model.addNewCard()
        self.assertEqual(self.model.rowCount(), 3)
        # test on closed model
        self.model.close()
        self.assertEqual(self.model.rowCount(), 0)


    def testCheckIndex(self):
        # test if _checkIndex raises correct exception
        # test on None
        self.assertRaises(CardModel.InvalidIndexError, self.model._checkIndex, None)
        # test on empty
        idx = QModelIndex()
        self.assertRaises(CardModel.InvalidIndexError, self.model._checkIndex, idx)


    def testIndex(self):
        # test index on empty model
        idx1 = self.model.index(0, 0)
        self.assertEqual(idx1, QModelIndex())
        # add two cards and check their ids
        self.model.addNewCard()
        self.model.addNewCard()
        idx1 = self.model.index(0, 0)
        idx2 = self.model.index(1, 0)
        idx3 = self.model.index(2, 0)
        self.assertEqual(idx1.internalId(), 1)
        self.assertEqual(idx2.internalId(), 2)
        self.assertEqual(idx3, QModelIndex())


    def testData(self):
        # test if generates error with invalid index
        idx = QModelIndex()
        self.assertRaises(CardModel.InvalidIndexError, self.model.data, idx)


    def testPreviousNextIndex(self):
        # previous index on empty index
        self.model.addNewCard()
        self.model.addNewCard()
        idx1 = self.model.index(0, 0)
        idx2 = self.model.index(1, 1)
        # test previous
        self.assertEqual(self.model.getPreviousIndex(idx2).internalId(), idx1.internalId())
        # test next
        self.assertEqual(self.model.getNextIndex(idx1).internalId(), idx2.internalId())


    def testAddNewCard(self):
        # test if adding new card generates a proper signal
        self.assertEqual(self.view.got_reset, False)
        self.model.addNewCard()
        self.model.addNewCard()
        self.model.addNewCard()
        self.assertEqual(self.view.got_reset, True)


    def testDeleteCard(self):
        # test if deleting card generates a proper signal
        # add 2 cards
        self.assertEqual(self.view.got_reset, False)
        self.model.addNewCard()
        self.model.addNewCard()
        self.assertEqual(self.view.got_reset, True)
        # reset view
        self.view.got_reset = False
        # delete first
        index = self.model.index(0, 0)
        self.model.deleteCard(index)
        # did it generate signal ?
        self.assertEqual(self.view.got_reset, True)

        # delete again
        self.view.got_reset = False
        index = self.model.index(0, 0)
        self.model.deleteCard(index)
        # did it generate signal?
        self.assertEqual(self.view.got_reset, True)

        # row count should be 0 now
        self.assertEqual(self.model.rowCount(), 0)

        # try to delete on empty model
        index = self.model.index(0, 0)
        self.assertEqual(index, QModelIndex())
        # should generate invalid index
        self.assertRaises(CardModel.InvalidIndexError, self.model.deleteCard, index)



    def testUpdateCard(self):
        self.model.addNewCard()
        idx = self.model.index(0, 0)

        self.model.updateCard(idx, 'test_question', 'test_answer')

        # test if got signal
        self.assertEqual(self.view.got_dataChanged, True)

        # test if data is correct
        data = self.model.data(idx, Qt.UserRole)

        self.assertEqual(data.question, 'test_question')
        self.assertEqual(data.answer, 'test_answer')



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCardModel))
    return suite
