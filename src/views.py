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
"""This is the module for views used in Mentor GUI"""


import release
__author__  = '%s <%s>' % \
              ( release.authors['afolmert'][0], release.authors['afolmert'][1])

__license__ = release.license
__version__ = release.version


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils_qt import tr


# main gui parts
# card widget is a sort of delegate and it should behave as one
# it currently has card model assigned
# or is it like more like listwidget

# helper widget classes
# TODO move this to views module
class MyTextEdit(QTextEdit):
    """Overriden to emit focusLost signals."""
    # TODO maybe better is to subclass the event procedure?

    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)

    def focusOutEvent(self, event):
        QTextEdit.focusOutEvent(self, event)
        self.emit(SIGNAL('focusLost()'))


class AbstractCardView(QAbstractItemView):
    """Base abstract class for card widgets."""

    # current index is stored in selection model
    # it is updated by connecting changing of current index in other views with
    # currentChanged slots in here

    def __init__(self, parent=None):
        QAbstractItemView.__init__(self, parent)
        self._dirty = False
        # self.setSelectionModel(QAbstractItemView.SingleSelection)
        # these control what it looks for

    def currentChanged(self, current, previous):
        # TODO how to check if two indexes are equal/inequal?
        if current != self.getCurrentIndex():
            # save pending changes
            self.saveChanges()
            self.setCurrentIndex(current)
            self._updateView(self.model(), current)


    def dataChanged(self, index):
        # TODO do this only if index is the one as currently used
        # TODO how to check whether this is the model
        if index == self.getCurrentIndex():
            self._updateView(self.model(), index)

    def dirty(self):
        return self._dirty

    def setDirty(self, dirty):
        self._dirty = dirty


    def saveChanges(self):
        if self.dirty():
            self._updateModel(self.model(), self.getCurrentIndex())
        self.setDirty(False)


    def reset(self):
        # what in here ?
        # the changes will not be saved
        # external app must call save
        self._updateView(self.model(), self.getCurrentIndex())

    def _updateModel(self, model, index):
        # to be overridden
        pass

    def _updateView(self, model, index):
        # to be overridden
        pass

    def getCurrentIndex(self):
        """Returns currently selected item"""
        selection = self.selectionModel()
        # get current selection
        selectedIndex = selection.selectedIndexes()
        if len(selectedIndex) > 0:
            return selectedIndex[0]
        else:
            return None

    def setCurrentIndex(self, index):
        """Returns currenly selected item from the model"""
        selection = self.selectionModel()
        selection.select(index, QItemSelectionModel.Select | QItemSelectionModel.Current)

    # must override pure virtual functions
    # perhaps I should abandon the idea of having this as abstractitemview?
    def verticalOffset(self):
        return 1

    def horizontalOffset(self):
        return 1

    def visualRegionForSelection(self, selection):
        return QRegion(0, 0, 1, 1)

    def visualRect(self):
        return QRect(0, 0, 1, 1)



class CardMainView(AbstractCardView):
    """Widget for displaying current card.
    May be later subclassed to display all kinds of cards:
     RTF , graphical, simple etc.
    """
    def __init__(self, parent=None):
        AbstractCardView.__init__(self, parent)
        self._updatingView = False
        self._updatingModel = False


        self.lblQuestion = QLabel("&Question:")
        self.txtQuestion = MyTextEdit()
        self.txtQuestion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.txtQuestion.setFont(QFont("Courier New", 13, QFont.Bold))
        self.txtQuestion.setText("")
        self.txtQuestion.setMinimumHeight(100)
        self.lblQuestion.setBuddy(self.txtQuestion)


        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.lblAnswer = QLabel("&Answer:")
        self.txtAnswer = MyTextEdit()
        self.txtAnswer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.txtAnswer.setFont(QFont("Courier New", 13, QFont.Bold))
        self.txtAnswer.setText("")
        self.txtAnswer.setMinimumHeight(100)
        self.lblAnswer.setBuddy(self.txtAnswer)

        self.connect(self.txtAnswer, SIGNAL('textChanged()'), self.txtAnswer_textChanged)
        self.connect(self.txtQuestion, SIGNAL('textChanged()'), self.txtQuestion_textChanged)
        self.connect(self.txtAnswer, SIGNAL('focusLost()'), self.saveChanges)
        self.connect(self.txtQuestion, SIGNAL('focusLost()'), self.saveChanges)

        self.splitter.addWidget(self.txtQuestion)
        self.splitter.addWidget(self.txtAnswer)
        self.splitter.setSizes([200, 100])


        # FIXME how to block splitter from hiding one window completely ??
        layout = QHBoxLayout()
        layout.setMargin(2)
        layout.setSpacing(2)
        layout.addWidget(self.splitter)

        self.setLayout(layout)

    def _updateModel(self, model, index):
        self._updatingModel = True
        if index:
            model.updateCard(index, \
                self.txtQuestion.toPlainText(), self.txtAnswer.toPlainText())
        self._updatingModel = False

    def _updateView(self, model, index):
        self._updatingView = True
        try:
            assert index and index.isValid(), "Invalid card model"
            card = model.data(index, Qt.UserRole)
            self.txtQuestion.setText(card.question)
            self.txtAnswer.setText(card.answer)
            self.txtQuestion.setEnabled(True)
            self.txtAnswer.setEnabled(True)
        # TODO narrow it to No data found exception !
        except:
            self.txtQuestion.setText("")
            self.txtQuestion.setEnabled(False)
            self.txtAnswer.setText("")
            self.txtAnswer.setEnabled(False)
        self._updatingView = False


    def txtAnswer_focusLost(self):
        if self._dirty:
            self._updateModel(self.model(), self.getCurrentIndex())

    def txtQuestion_focusLost(self):
        if self._dirty:
            self._updateModel(self.model(), self.getCurrentIndex())

    def txtAnswer_textChanged(self):
        if not self._updatingView:
            self.setDirty(True)

    def txtQuestion_textChanged(self):
        if not self._updatingView:
            self.setDirty(True)

    # FIXME
    # these functions are not really connected with the model/view thing
    # the question is : should this be connected with a model and be descended
    # from QAbstractItemView or just be a standalone control for displaying
    # cards?
    def displayCard(self, card, readonly=True, showAnswer=True):
        self.txtQuestion.setEnabled(not readonly)
        self.txtAnswer.setEnabled(not readonly)
        self.txtQuestion.setText(card.question)
        if showAnswer:
            self.txtAnswer.setText(card.answer)
        else:
            self.txtAnswer.setText("")



class CardDetailView(AbstractCardView):
    """Widget for displaying card details (score, hints, review dates etc.)"""
    def __init__(self, parent=None):
        AbstractCardView.__init__(self, parent)

        self._updatingView = False
        self.setFont(QFont("vt100", 8))

        self.lblId             = QLabel("Id:")
        self.edId              = QLabel("edId")
        self.lblScore          = QLabel("Score:")
        self.edScore           = QLabel("edScore")
        self.lblDesc           = QLabel("Description:")
        self.edDesc            = QLabel("edDescription")
        self.lblRepetitions    = QLabel("Repetitions:")
        self.edRepetitions     = QLabel("edRepetitions")
        self.lblInterval       = QLabel("Interval:")
        self.edInterval        = QLabel("edInterval")
        self.lblLastRepetition = QLabel("Last repetition:")
        self.edLastRepetition  = QLabel("edLast repetition")
        self.lblNextRepetition = QLabel("Next repetition:")
        self.edNextRepetition  = QLabel("edNext repetition")
        self.lblAFactor        = QLabel("A-Factor:")
        self.edAFactor         = QLabel("edA-Factor")
        self.lblUFactor        = QLabel("U-Factor:")
        self.edUFactor         = QLabel("edU-Factor")
        self.lblForgettingIndex  = QLabel("Forgetting index:")
        self.edForgettingIndex   = QLabel("edForgetting index")
        self.lblFutureRep      = QLabel("Future reptition:")
        self.edFutureRep       = QLabel("edFuture reptition")
        self.lblOrdinal        = QLabel("Ordinal:")
        self.edOrdinal         = QLabel("edOrdinal")
        self.lblDifficulty     = QLabel("Difficulty:")
        self.edDifficulty      = QLabel("edDifficulty")
        self.lblFirstGrade     = QLabel("First grade:")
        self.edFirstGrade      = QLabel("edFirst grade")
        self.lblType           = QLabel("Type:")
        self.edType            = QLabel("edType")

        layout = QGridLayout()
        layout.addWidget(self.lblId            , 0, 0)
        layout.addWidget(self.edId             , 0, 1)
        layout.addWidget(self.lblScore         , 1, 0)
        layout.addWidget(self.edScore          , 1, 1)
        layout.addWidget(self.lblDesc          , 2, 0)
        layout.addWidget(self.edDesc           , 2, 1)
        layout.addWidget(self.lblRepetitions   , 3, 0)
        layout.addWidget(self.edRepetitions    , 3, 1)
        layout.addWidget(self.lblInterval      , 4, 0)
        layout.addWidget(self.edInterval       , 4, 1)
        layout.addWidget(self.lblLastRepetition, 5, 0)
        layout.addWidget(self.edLastRepetition , 5, 1)
        layout.addWidget(self.lblNextRepetition, 6, 0)
        layout.addWidget(self.edNextRepetition , 6, 1)
        layout.addWidget(self.lblAFactor       , 7, 0)
        layout.addWidget(self.edAFactor        , 7, 1)
        layout.addWidget(self.lblUFactor       , 8, 0)
        layout.addWidget(self.edUFactor        , 8, 1)
        layout.addWidget(self.lblForgettingIndex , 9, 0)
        layout.addWidget(self.edForgettingIndex  , 9, 1)
        layout.addWidget(self.lblFutureRep     , 10, 0)
        layout.addWidget(self.edFutureRep      , 10, 1)
        layout.addWidget(self.lblOrdinal       , 11, 0)
        layout.addWidget(self.edOrdinal        , 11, 1)
        layout.addWidget(self.lblDifficulty    , 12, 0)
        layout.addWidget(self.edDifficulty     , 12, 1)
        layout.addWidget(self.lblFirstGrade    , 13, 0)
        layout.addWidget(self.edFirstGrade     , 13, 1)
        layout.addWidget(self.lblType          , 14, 0)
        layout.addWidget(self.edType           , 14, 1)

        layout.setMargin(1)
        layout.setSpacing(1)
        self.setLayout(layout)


    def _updateView(self, model, index):
        # display information from the current cardModel and cardModelIndex
        self._updatingView = True
        try:
            assert index and index.isValid(), "Invalid cardModel index!"
            self.edId.setText(model.data(index).toString()[:10])
            self.edScore.setText(model.data(index).toString()[:10])
            self.edDesc.setText(model.data(index).toString()[:10])
        except:
            self.edId.setText("")
            self.edScore.setText("")
            self.edDesc.setText("")
        self._updatingView = False


class CardSourceView(AbstractCardView):
    """Widget for displaying XML source for card"""
    def __init__(self, parent=None):
        AbstractCardView.__init__(self, parent)
        self._updatingView = False

        #self.lblSource = QLabel("&Source:")
        self.txtSource = MyTextEdit()
        self.setFont(QFont("vt100", 8))
        #self.lblSource.setBuddy(self.txtSource)

        layout = QVBoxLayout(self)
        layout.setMargin(2)
        layout.setSpacing(2)
        #layout.addWidget(self.lblSource)
        layout.addWidget(self.txtSource)

        self.setLayout(layout)

    def _updateView(self, model, index):
        self._updatingView = True
        try:
            assert index and index.isValid(), "Invalid card model index!"
            self.txtSource.setText(model.data(index).toString())
            self.txtSource.setEnabled(True)
        except:
            self.txtSource.setText("")
            self.txtSource.setEnabled(False)

        self._updatingView = False



class CardGridView(QTableView):

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.setSortingEnabled(False)
        self.setShowGrid(False)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)


        self.setFont(QFont("vt100", 8))


