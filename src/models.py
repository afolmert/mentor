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
"""This is the module for models used in Mentor GUI"""


import release
__author__  = '%s <%s>' % \
              ( release.authors['afolmert'][0], release.authors['afolmert'][1])

__license__ = release.license
__version__ = release.version


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from database import Card, CardDb



class CardModel(QAbstractListModel):
    """Model to be used for list and tree view."""

    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        self.cardDb = CardDb()

    def open(self, dbpath):
        self.cardDb.open(str(dbpath))
        # FIXME why these do not work??
        self.reset()
        # ^ self.emit(SIGNAL('modelReset()'))

    def close(self):
        self.cardDb.close()
        self.reset()

    def filepath(self):
        """Returns path to currently open database"""
        if self.cardDb.is_open():
            return self.cardDb.db_path
        else:
            return None

    def isActive(self):
        return self.cardDb.is_open()


    def rowCount(self, parent=QModelIndex()):
        # return cards
        if parent.isValid():
            return 0
        else:
            if self.cardDb.is_open():
                return self.cardDb.get_cards_count()
            else:
                return 0


    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return 1


    def index(self, row, column, parent=QModelIndex()):
        if row < 0 or column < 0 or not self.cardDb.is_open():
            return QModelIndex()
        else:
            # returns index with given card id
            header = self.cardDb.get_card_headers('', row, row + 1)
            if len(header) == 1:
                return self.createIndex(row, 0, int(header[0][0]))
            else:
                return QModelIndex()

    # for display role only id+question in following columns will be
    # for specific data , in the following columns

    def data(self, index, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole, Qt.UserRole):
            return QVariant()

        card = self.cardDb.get_card(index.internalId())
        if role == Qt.UserRole:
            return card
        else:
            return QVariant('#%d %s' % (card.id, str(card.question)))

    def flags(self, index):
        return QAbstractListModel.flags(self, index) | Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if section in range(0, 5):
                return QVariant(tr("Section %d" % section))
            else:
                return QVariant()
        else:
            return QVariant()


    def getPreviousIndex(self, index):
        """Returns previous index before given or given if it's first."""
        assert index is not None and index.isValid(), "getPreviousIndex: Invalid index given!"
        if index.row() == 0:
            return index
        else:
            return self.index(index.row() - 1, 0)
        # pointer , get row before


    def getNextIndex(self, index):
        """Returns next index after given or given if it's last."""
        assert index is not None and index.isValid(), "getNextIndex: Invalid index given!"
        if index.row() == self.rowCount() - 1:
            return index
        else:
            return self.index(index.row() + 1, 0)
        # get row after ?

    # TODO
    # what about inserting rows
    # and moving rows up and down ??
    # must have parameter position or display position ??

    # TODO
    # add special handlers like rowsAboutToBeInserted etc .
    # right now only model to be reset


    def addNewCard(self):
        """Adds a new empty card."""
        self.emit(SIGNAL('modelAboutToBeReset()'))

        rowid = self.cardDb.add_card(Card())
        # TODO is it ok to return it here?
        result = self.createIndex(self.cardDb.get_cards_count(), 0, rowid)

        # cards.addCard(Card())
        # TODO
        # why these do not work ?
        self.reset()
        # self.emit(SIGNAL('modelReset()'))
        #
        return result


    def deleteCard(self, index):
        assert index is not None and index.isValid(), "deleteCard: Invalid index given!"
        self.emit(SIGNAL('modelAboutToBeReset()'))

        self.cardDb.delete_card(index.internalId())

        # why these do not work??
        self.reset()
        # self.emit(SIGNAL('modelReset()'))
        # cards - delete_card  card_id

    # TODO question
    # how to update card if peg is somewhere else ?
    # maybe keep blob as well ?
    # the items are then splitted
    def updateCard(self, index, question, answer):
        assert index is not None and index.isValid(), "updateCard: Invalid index given!"

        card = Card(index.internalId(), question, answer)
        self.cardDb.update_card(card)

        # update data in the model
        self.emit(SIGNAL('dataChanged(QModelIndex)'), index)




