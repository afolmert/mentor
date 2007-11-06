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


import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from database import Card, CardDb
from utils import isstring, log



class CardModel(QAbstractListModel):
    """Model to be used for list and tree view."""

    class InvalidIndexError(Exception): pass
    class ModelNotActiveError(Exception): pass

    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        self.cardDb = CardDb()


    def _checkIndex(self, index):
        if index is None or not index.isValid() or index == QModelIndex():
            raise CardModel.InvalidIndexError, "Invalid index given"

    def _checkActive(self):
        if not self.isActive():
            raise CardModel.ModelNotActiveError, "Model is not active. Use open first."


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
            if self.cardDb.is_open():
                return 1
            else:
                return 0


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
        self._checkIndex(index)
        if role not in (Qt.DisplayRole, Qt.UserRole):
            return QVariant()

        card = self.cardDb.get_card(index.internalId())
        if role == Qt.UserRole:
            return card
        else:
            return QVariant('#%d %s' % (card.id, str(card.question).strip()))


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
        self._checkIndex(index)
        if index.row() == 0:
            return index
        else:
            return self.index(index.row() - 1, 0)
        # pointer , get row before


    def getNextIndex(self, index):
        """Returns next index after given or given if it's last."""
        self._checkIndex(index)
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
        self._checkIndex(index)
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
        self._checkIndex(index)

        card = Card(index.internalId(), question, answer)
        self.cardDb.update_card(card)

        # update data in the model
        self.emit(SIGNAL('dataChanged(QModelIndex)'), index)



    # TODO model should not have any algorithms - it should be just as a proxy
    # between database and any more advanced algorithm
    # e.g. database importer
    # btw. they should use the same classes with the probe program
    # TODO progress bar for importing and possibility to cancel if is a long
    # operatoin
    def importQAFile(self, file, clean=True):
        """Import cards from given question&answer file.
        @param file can be file name or file like object
        """
        self._checkActive()
        if isstring(file):
            file = open(file, 'rt')
        if clean:
            self.cardDb.delete_all_cards()
        prefix = ''
        last_prefix = ''
        card = Card()
        for line in file.readlines():
            if line.upper().startswith('Q:') or line.upper().startswith('A:'):
                last_prefix = prefix
                prefix = line[:2].upper()
                line = line[3:]
                # if new card then recreate
                if prefix == 'Q:' and prefix != last_prefix:
                    if not card.is_empty():
                        self.cardDb.add_card(card, False)
                    card = Card()
                if line.strip() != '':
                    if prefix == 'Q:':
                        card.question += line
                    else: # prefix == a
                        card.answer += line
        # add last card
        if not card.is_empty():
            self.cardDb.add_card(card)

        # TODO do it in a real transaction way
        # in case of error do a rollback
        self.cardDb.commit()
        self.reset()



# FIXME
# How should I design it ?
# Right now it is just a container (stack) for a bunch of cards which get
# randomized

class DrillModel(QObject):
    """Model for drilling cards"""

    # scores
    Good, Bad = range(2)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.cards = []

    def addCard(self, card):
        self.cards.append(card)

    def clear(self):
        self.cards.clear()


    def selectNextCard(self):
        # take from the stack and put it on top
        if len(self.cards) > 0:
            result = self.cards[0]
            self.cards = self.cards[1:]
            self.cards.append(result)
            return result
        else:
            return Card()

    def removeCard(self, card):
        try:
            self.cards.remove(card)
        except:
            pass


    def scoreCard(self, card, score):
        if score == DrillModel.Good:
            log("Card: $card will be removed from drill.")
            self.cards.remove(card)


    def shuffleCards(self):
        from random import shuffle
        shuffle(self.cards)
        log('Cards were shuffled.')


    def printCards(self):
        print "Printing cards..."
        sys.stdout.flush()
        i = 0
        for card in self.cards:
            print "%d %s\n" % (i, str(card))
            sys.stdout.flush()
            i += 1
        print "Done."
        sys.stdout.flush()






def main():
    pass

if __name__ == '__main__':
    main()

