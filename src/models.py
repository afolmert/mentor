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
from cards import Card, Cards
from utils import isstring, log
from utils_qt import tr


class CardModel(QAbstractItemModel):
    """Model to be used for list and tree view."""

    class InvalidIndexError(Exception): pass
    class ModelNotActiveError(Exception): pass

    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        self.cards = Cards()


    def _checkIndex(self, index):
        if index is None or not index.isValid() or index == QModelIndex():
            raise CardModel.InvalidIndexError, "Invalid index given"

    def _checkActive(self):
        if not self.isActive():
            raise CardModel.ModelNotActiveError, "Model is not active. Use open first."


    def open(self, dbpath):
        self.cards.open(str(dbpath))
        # FIXME why these do not work??
        self.reset()
        # ^ self.emit(SIGNAL('modelReset()'))

    def close(self):
        self.emit(SIGNAL('modelAboutToBeReset()'))
        self.cards.close()
        self.reset()


    def filepath(self):
        """Returns path to currently open database"""
        if self.cards.is_open():
            return self.cards.db_path
        else:
            return None

    def isActive(self):
        return self.cards.is_open()


    def parent(self, index):
        return QModelIndex()


    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            if self.cards.is_open():
                return self.cards.get_cards_count()
            else:
                return 0


    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            if self.cards.is_open():
                return 5
            else:
                return 0


    def index(self, row, column, parent=QModelIndex()):
        if row < 0 or column < 0 or not self.cards.is_open():
            return QModelIndex()
        else:
            #  returns index with given card id
            header = self.cards.get_card_headers('', row, row + 1)
            if len(header) == 1:
                return self.createIndex(row, column, int(header[0][0]))
            else:
                return QModelIndex()

    # for display role only id+question in following columns will be
    # for specific data , in the following columns

    def data(self, index, role=Qt.DisplayRole):
        self._checkIndex(index)
        if role not in (Qt.DisplayRole, Qt.UserRole):
            return QVariant()

        card = self.cards.get_card(index.internalId())
        if role == Qt.UserRole:
            return card
        else:
            if index.column() == 0:
                return QVariant('#%d %s' % (card.id, str(card.question).strip()))
            elif index.column() == 1:
                return QVariant('%s' % str(card.answer).strip())
            elif index.column() == 2:
                return QVariant('%s' % str(card.question_hint).strip())
            elif index.column() == 3:
                return QVariant('%s' % str(card.answer_hint).strip())
            elif index.column() == 4:
                return QVariant('%s' % str(card.score))
            else:
                return QVariant()


    def flags(self, index):
        return QAbstractListModel.flags(self, index) | Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return QVariant("Question")
                elif section == 1:
                    return QVariant("Answer")
                elif section == 2:
                    return QVariant(tr("Question hint"))
                elif section == 3:
                    return QVariant(tr("Answer hint"))
                elif section == 4:
                    return QVariant(tr("Score"))
                else:
                    return QVariant()
            else:
                return QVariant(str(section))
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

        rowid = self.cards.add_card(Card())
        # TODO is it ok to return it here?
        result = self.createIndex(self.cards.get_cards_count(), 0, rowid)

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

        self.cards.delete_card(index.internalId())

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
        self.cards.update_card(card)

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
        self.emit(SIGNAL('modelAboutToBeReset()'))
        self._checkActive()
        if isstring(file):
            file = open(file, 'rt')
        if clean:
            self.cards.delete_all_cards()
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
                        self.cards.add_card(card, False)
                    card = Card()
                if line.strip() != '':
                    if prefix == 'Q:':
                        card.question += line
                    else: # prefix == a
                        card.answer += line
        # add last card
        if not card.is_empty():
            self.cards.add_card(card)

        # TODO do it in a real transaction way
        # in case of error do a rollback
        self.cards.commit()
        self.reset()



# FIXME
# How should I design it ?
# Right now it is just a container (stack) for a bunch of cards which get
# randomized

class DrillModel(QAbstractItemModel):
    """Model for drilling cards"""

    # scores
    Good, Bad = range(2)

    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.cards = []


    def parent(self, index=QModelIndex()):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return len(self.cards)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return 1

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()
        else:
            if row >= 0 and row < len(self.cards) and column == 0:
                return self.createIndex(row, column, None)
            else:
                return QModelIndex()


    def data(self, index, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole,):
            return QVariant()
        else:
            if index.row() < len(self.cards):
                card = self.cards[index.row()]
                return QVariant("%d %s" % (card.id, card.question))
            else:
                return QVariant()


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return QVariant(str(section))
        # return QAbstractItemModel.headerData(self, section, orientation, role)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def addCard(self, card):
        self.emit(SIGNAL('modelAboutToBeReset()'))
        self.cards.append(card)
        self.reset()

    def clear(self):
        self.emit(SIGNAL('modelAboutToBeReset()'))
        self.cards.clear()
        self.reset()


    def selectNextCard(self):
        # take from the stack and put it on top
        if len(self.cards) > 0:
            self.emit(SIGNAL('modelAboutToBeReset()'))
            result = self.cards[0]
            self.cards = self.cards[1:]
            self.cards.append(result)
            self.reset()
            return result
        else:
            return Card()

    def removeCard(self, card):
        try:
            self.emit(SIGNAL('modelAboutToBeReset()'))
            self.cards.remove(card)
            self.reset()
        except:
            pass


    def scoreCard(self, card, score):
        if score == DrillModel.Good:
            log("Card: $card will be removed from drill.")
            self.removeCard(card)


    def shuffleCards(self):
        from random import shuffle
        self.emit(SIGNAL('modelAboutToBeReset()'))
        shuffle(self.cards)
        self.reset()


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


