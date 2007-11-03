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

"""This is mentor main program.

Mentor is a simple flashcard-like app with special focus on creating flashcards
out of text and image snippets. It's main purpose is quickly import knowledge
from selected snippets and transform it into knowledge by performing drills.

The drill is done via hiding part of the card (creating a cloze) and obscuring
it. The user has to think of an answer and then reveal the cloze to see if she
remembered it right. Then she gives herself a score (1-5) depending on how well
she felt to remember the cloze. The score is used to schedule the next
repetition period.

It enables text-mode and graphical-mode snippet creation and drill.

It also provides functionality for scheduling repetitions for created cards,
which is useful if one wants to make repetitions over longer time period.

"""


import release
__author__  = '%s <%s>' % \
              ( release.authors['afolmert'][0], release.authors['afolmert'][1])

__license__ = release.license
__version__ = release.version

import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils_qt import lazyshow, tr, show_info
from utils import log
from config import config
from database import Card, CardDb
import mentor_rc


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
        # self.setSelectionModel(QAbstractItemView.SingleSelection)
        # these control what it looks for

    def currentChanged(self, current, previous):
        # TODO how to check if two indexes are equal/inequal?
        if current != self.getCurrentIndex():
            self.setCurrentIndex(current)
            self.updateView(self.model(), current)


    def dataChanged(self, index):
        # TODO do this only if index is the one as currently used
        # TODO how to check whether this is the model
        if index == self.getCurrentIndex():
            self.updateView(self.model(), index)


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
        self._dirty = False
        self._updatingView = False
        self._updatingModel = False


        self.lblQuestion = QLabel("&Question:")
        self.txtQuestion = MyTextEdit()
        self.txtQuestion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.txtQuestion.setFont(QFont("Courier New", 13, QFont.Bold))
        self.txtQuestion.setText("question text..")
        self.txtQuestion.setMinimumHeight(100)
        self.lblQuestion.setBuddy(self.txtQuestion)


        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.lblAnswer = QLabel("&Answer:")
        self.txtAnswer = MyTextEdit()
        self.txtAnswer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.txtAnswer.setFont(QFont("Courier New", 13, QFont.Bold))
        self.txtAnswer.setText("answer text..")
        self.txtAnswer.setMinimumHeight(100)
        self.lblAnswer.setBuddy(self.txtAnswer)

        self.connect(self.txtAnswer, SIGNAL('textChanged()'), self.txtAnswer_textChanged)
        self.connect(self.txtQuestion, SIGNAL('textChanged()'), self.txtQuestion_textChanged)
        self.connect(self.txtAnswer, SIGNAL('focusLost()'), self.txtAnswer_focusLost)
        self.connect(self.txtQuestion, SIGNAL('focusLost()'), self.txtQuestion_focusLost)

        self.splitter.addWidget(self.txtQuestion)
        self.splitter.addWidget(self.txtAnswer)
        self.splitter.setSizes([200, 100])


        # FIXME how to block splitter from hiding one window completely ??
        layout = QHBoxLayout()
        layout.setMargin(2)
        layout.setSpacing(2)
        layout.addWidget(self.splitter)

        self.setLayout(layout)

    def updateModel(self, model, index):
        self._updatingModel = True
        if index:
            model.updateCard(index, \
                self.txtQuestion.toPlainText(), self.txtAnswer.toPlainText())
        self._updatingModel = False

    def updateView(self, model, index):
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
            self.updateModel(self.model(), self.getCurrentIndex())

    def txtQuestion_focusLost(self):
        if self._dirty:
            self.updateModel(self.model(), self.getCurrentIndex())

    def txtAnswer_textChanged(self):
        if not self._updatingView:
            self._dirty = True

    def txtQuestion_textChanged(self):
        if not self._updatingView:
            self._dirty = True


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


    def updateView(self, model, index):
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

    def updateView(self, model, index):
        self._updatingView = True
        try:
            assert index and index.isValid(), "Invalid card model index!"
            self.txtSource.setText(model.data(index).toString())
            self.txtSource.setEnabled(True)
        except:
            self.txtSource.setText("")
            self.txtSource.setEnabled(False)

        self._updatingView = False


class MainWindow(QMainWindow):
    """Central window for the Mentor app"""

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)

        # set up controls
        # items panel
        self._cardModel = CardModel()
        self._cardModelIndex = QModelIndex()  # current index for card model

        self.setWindowTitle("Mentor")
        self.move(50, 50)
        self.createCentralWidget()
        self.createActions()
        self.createMenus()
        self.createToolbars()
        self.createStatusBar()

        self.connect(qApp, SIGNAL('aboutToQuit()'), self.qApp_aboutToQuit)

        self._windowEntered = False


    def createCentralWidget(self):

        ##########################
        # setup central widget

        # question and answer panel
        self.cardMainView = CardMainView(self)
        self.cardMainView.setModel(self._cardModel)

        self.setCentralWidget(self.cardMainView)


        ##########################
        # items view
        self.lstDrill = QListView(self)
        self.lstDrill.setModel(self._cardModel)
        # self.lstDrill.setSelectionModel(Qt.SingleSelection)

        dock1 = QDockWidget('List', self)
        dock1.setWidget(self.lstDrill)

        self.addDockWidget(Qt.LeftDockWidgetArea, dock1)



        ##########################
        # details widget
        self.cardDetailView = CardDetailView(self)
        self.cardDetailView.setModel(self._cardModel)

        dock2 = QDockWidget('Details', self)
        dock2.setWidget(self.cardDetailView)

        self.addDockWidget(Qt.BottomDockWidgetArea , dock2)


        ##########################
        # card source widget
        self.cardSourceView = CardSourceView(self)
        self.cardSourceView.setModel(self._cardModel)

        dock3 = QDockWidget('Source', self)
        dock3.setWidget(self.cardSourceView)

        self.addDockWidget(Qt.BottomDockWidgetArea, dock3)


        ##########################
        # buttons widget
        self.buttons = QWidget(self)

        self.btnMoveUp = QPushButton("Up")
        self.btnMoveDown = QPushButton("Down")
        self.btnShowSelection = QPushButton("Show selection")
        self.btnAdd = QPushButton("Add")
        self.btnDelete = QPushButton("Delete")
        self.btnLoad = QPushButton("Load...")

        # todo move this to actions
        self.connect(self.btnAdd, SIGNAL("clicked()"), self.btnAdd_clicked)
        self.connect(self.btnDelete, SIGNAL("clicked()"), self.btnDelete_clicked)
        self.connect(self.btnLoad, SIGNAL("clicked()"), self.btnLoad_clicked)
        self.connect(self.btnMoveUp, SIGNAL("clicked()"), self.btnMoveUp_clicked)
        self.connect(self.btnMoveDown, SIGNAL("clicked()"), self.btnMoveDown_clicked)
        self.connect(self.btnShowSelection, SIGNAL("clicked()"), self.btnShowSelection_clicked)

        buttonsLayout = QVBoxLayout()

        buttonsLayout.addWidget(self.btnMoveUp)
        buttonsLayout.addWidget(self.btnMoveDown)
        buttonsLayout.addWidget(self.btnShowSelection)
        buttonsLayout.addWidget(self.btnAdd)
        buttonsLayout.addWidget(self.btnDelete)
        buttonsLayout.addWidget(self.btnLoad)


        self.buttons.setLayout(buttonsLayout)


        dock = QDockWidget('Buttons', self)
        dock.setWidget(self.buttons)

        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        ##########################
        # connecting
        # FIXME connecting these 4 times cause sometimes I don't get proper
        # messages
        # when I edit something and press Down
        # and then click on what I edited then selection changed does not catch
        # it

        self.connect(self.lstDrill.selectionModel(), \
                        SIGNAL('currentChanged(QModelIndex, QModelIndex)'), \
                        self.lstDrill_currentChanged)
        self.connect(self.lstDrill,
                        SIGNAL('activated(QModelIndex)'), \
                        self.lstDrill_activated)
        self.connect(self.lstDrill,
                        SIGNAL('clicked(QModelIndex)'), \
                        self.lstDrill_activated)

        self.connect(self, SIGNAL('cardModelIndexChanged'), self.lstDrill_cardModelIndexChanged)
        self.connect(self, SIGNAL('cardModelIndexChanged'), self.cardMainView.currentChanged)
        self.connect(self, SIGNAL('cardModelIndexChanged'), self.cardSourceView.currentChanged)
        self.connect(self, SIGNAL('cardModelIndexChanged'), self.cardDetailView.currentChanged)


    def cardModel(self):
        return self._cardModel

    def setCardModel(self, model):
        self._cardModel = model

    def cardModelIndex(self):
        return self._cardModelIndex

    def setCardModelIndex(self, index):
        old = self._cardModelIndex
        # if old != index:
        self._cardModelIndex = index
        self.emit(SIGNAL('cardModelIndexChanged'), index, old)


    def createActions(self):
        # File actions
        self.actNew = QAction(QIcon(":/images/world.png"), tr("&New pack..."), self)
        self.actNew.setStatusTip(tr("Create a new pack..."))
        self.connect(self.actNew, SIGNAL("triggered()"), self.on_actNew_triggered)

        self.actOpen = QAction(QIcon(":/images/world.png"), tr("&Open pack..."), self)
        self.actOpen.setShortcut(QKeySequence(tr("Ctrl+O")))
        self.actOpen.setStatusTip(tr("Open an existing pack..."))
        self.connect(self.actOpen, SIGNAL("triggered()"), self.on_actOpen_triggered)

        self.actClose = QAction(QIcon(":/images/world.png"), tr("&Close pack"), self)
        self.actClose.setStatusTip(tr("Close currently active pack"))
        self.connect(self.actClose, SIGNAL("triggered()"), self.on_actClose_triggered)

        self.actCopy = QAction(tr("&Copy pack..."), self)
        self.actCopy.setStatusTip(tr("Copy an existing pack..."))
        self.connect(self.actCopy, SIGNAL("triggered()"), self.on_actCopy_triggered)

        self.actDelete = QAction(tr("&Delete pack..."), self)
        self.actDelete.setStatusTip(tr("Delete an existing pack..."))
        self.connect(self.actDelete, SIGNAL("triggered()"), self.on_actDelete_triggered)

        self.actRepair = QAction(tr("&Repair pack..."), self)
        self.actRepair.setStatusTip(tr("Repair an existing pack..."))
        self.connect(self.actRepair, SIGNAL("triggered()"), self.on_actRepair_triggered)

        self.actMerge = QAction(tr("&Merge pack..."), self)
        self.actMerge.setStatusTip(tr("Merge an existing pack..."))
        self.connect(self.actMerge, SIGNAL("triggered()"), self.on_actMerge_triggered)

        self.actImportQA = QAction(tr("&Import from QA file..."), self)
        self.actImportQA.setStatusTip(tr("Import from QA file..."))
        self.connect(self.actImportQA, SIGNAL("triggered()"), self.on_actImportQA_triggered)

        self.actImportXML = QAction(tr("&Import from XML file..."), self)
        self.actImportXML.setStatusTip(tr("Import from XML file..."))
        self.connect(self.actImportXML, SIGNAL("triggered()"), self.on_actImportXML_triggered)

        self.actImportProbe = QAction(tr("&Import from PRB file..."), self)
        self.actImportProbe.setStatusTip(tr("Import from a PRB file..."))
        self.connect(self.actImportProbe, SIGNAL("triggered()"), self.on_actImportProbe_triggered)

        self.actImportSuperMemo = QAction(tr("&Import from SuperMemo..."), self)
        self.actImportProbe.setStatusTip(tr("Import from a SuperMemo..."))
        self.connect(self.actImportProbe, SIGNAL("triggered()"), self.on_actImportProbe_triggered)

        self.actExportQA = QAction(tr("&Export to QA file..."), self)
        self.actExportQA.setStatusTip(tr("Export to QA file..."))
        self.connect(self.actExportQA, SIGNAL("triggered()"), self.on_actExportQA_triggered)

        self.actExportXML = QAction(tr("&Export to XML file..."), self)
        self.actExportXML.setStatusTip(tr("Export to XML file..."))
        self.connect(self.actExportXML, SIGNAL("triggered()"), self.on_actExportXML_triggered)

        self.actExportProbe = QAction(tr("&Export to PRB file..."), self)
        self.actExportProbe.setStatusTip(tr("Export to PRB file..."))
        self.connect(self.actExportProbe, SIGNAL("triggered()"), self.on_actExportProbe_triggered)

        self.actExportSuperMemo = QAction(tr("&Export to SuperMemo..."), self)
        self.actExportProbe.setStatusTip(tr("Export to SuperMemo..."))
        self.connect(self.actExportProbe, SIGNAL("triggered()"), self.on_actExportProbe_triggered)

        self.actProperties = QAction(tr("&Properties..."), self)
        self.actExportProbe.setStatusTip(tr("Display pack properties..."))
        self.connect(self.actExportProbe, SIGNAL("triggered()"), self.on_actExportProbe_triggered)

        # Recent file actions
        self.actRecentFiles = []
        for i in range(config.GUI_RECENTFILES_MAX):
            self.actRecentFiles.append(QAction(self))
            self.actRecentFiles[i].setVisible(False)
            self.connect(self.actRecentFiles[i], SIGNAL("triggered()"), self.on_actRecentFiles_triggered)

        self.actExit = QAction(QIcon(":/images/clock_play.png"), tr("E&xit"), self)
        self.actExit.setShortcut(QKeySequence(tr("Ctrl+Q")))
        self.actExit.setStatusTip(tr("Exits the application."))
        self.connect(self.actExit, SIGNAL("triggered()"), qApp, SLOT("quit()"))

        # Edit actions
        self.actNewItem = QAction(QIcon(":/images/world.png"), tr("Add a new i&tem"), self)
        self.actNewItem.setShortcut(QKeySequence(tr("Alt+A")))
        self.actNewArticle = QAction(QIcon(":/images/clock_pause.png"), tr("Add a new &article"), self)
        self.actNewArticle.setShortcut(QKeySequence(tr("Ctrl+Alt+N")))
        self.actNewTask = QAction(QIcon(":/images/style_edit.png"), tr("Add a &new task"), self)
        self.actNewTask.setShortcut(QKeySequence("Ctrl+Alt+A"))

        # Search actions
        self.actFindElements = QAction(QIcon(":/images/style_edit.png"), tr("&Find elements"), self)
        self.actFindElements.setShortcut(QKeySequence(tr("Ctrl+F")))
        self.actFindTexts = QAction(QIcon(":/images/style_edit.png"), tr("Fi&nd texts"), self)
        self.actFindTexts.setShortcut(QKeySequence(tr("Ctrl+S")))
        self.actFindWord = QAction(QIcon(":/images/style_edit.png"), tr("Fin&d word"), self)
        self.actFindString = QAction(QIcon(":/images/style_edit.png"), tr("Find st&ring"), self)
        self.actFindString.setShortcut(QKeySequence(tr("F3")))
        self.actTextRegistry = QAction(QIcon(":/images/style_edit.png"), tr("Te&xt registry"), self)
        self.actTextRegistry.setShortcut(QKeySequence(tr("Ctrl+Alt+X")))
        self.actImages =  QAction(QIcon(":/images/style_edit.png"), tr("&Images"), self)
        self.actSounds =  QAction(QIcon(":/images/style_edit.png"), tr("&Sounds"), self)
        self.actTemplates = QAction(QIcon(":/images/style_edit.png"), tr("&Templates"), self)
        self.actCategories = QAction(QIcon(":/images/style_edit.png"), tr("&Categories"), self)
        self.actTasklists = QAction(QIcon(":/images/style_edit.png"), tr("Tas&klists"), self)
        self.actOtherRegistries = QAction(QIcon(":/images/style_edit.png"), tr("&Other registries"), self)
        self.actGotoAncestor = QAction(QIcon(":/images/style_edit.png"), tr("Go to &ancestor"), self)
        self.actGotoAncestor.setShortcut(QKeySequence(tr("Alt+P")))
        self.actGotoElement = QAction(QIcon(":/images/style_edit.png"), tr("&Go to element"), self)
        self.actGotoElement.setShortcut(QKeySequence(tr("Ctrl+G")))


        # View actions
        self.actAll = QAction(QIcon(":/images/style_edit.png"), tr("&All"), self)
        self.actOutstanding = QAction(QIcon(":/images/style_edit.png"), tr("&Outstanding"), self)
        self.actMemorized = QAction(QIcon(":/images/package_link.png"), tr("&Memorized"), self)
        self.actPending = QAction(QIcon(":/images/world_add.png"), tr("&Pending"), self)
        self.actDismissed = QAction(QIcon(":/images/style_edit.png"), tr("&Dismissed"), self)
        self.actTopic = QAction(QIcon(":/images/style_edit.png"), tr("&Topic"), self)
        self.actItems = QAction(QIcon(":/images/clock_stop.png"), tr("&Items"), self)
        self.actTasks = QAction(QIcon(":/images/style_edit.png"), tr("Ta&ks"), self)
        self.actLastBrowser = QAction(QIcon(":/images/style_edit.png"), tr("&Last browser"), self)
        self.actSearchResults = QAction(QIcon(":/images/style_edit.png"), tr("&Search results"), self)
        self.actSubset = QAction(QIcon(":/images/clock_pause.png"), tr("S&ubset"), self)
        self.actFilter = QAction(QIcon(":/images/style_edit.png"), tr("&Filter"), self)
        self.actLeeches  = QAction(QIcon(":/images/chart_pie.png"), tr("&Leeches"), self)
        self.actLeeches.setShortcut(QKeySequence("Shift+F3"))
        self.actSemiLeeches = QAction(QIcon(":/images/style_edit.png"), tr("&Semi-leeches"), self)
        self.actDrill = QAction(QIcon(":/images/style_edit.png"), tr("&Drill"), self)
        self.actRange = QAction(QIcon(":/images/script_palette.png"), tr("&Range"), self)
        self.actHistory = QAction(QIcon(":/images/style_edit.png"), tr("&History"), self)
        self.actBranch = QAction(QIcon(":/images/telephone_link.png"), tr("&Branch"), self)

        # Help actions
        self.actWelcome = QAction(QIcon(":/images/script_palette.png"), tr("&Welcome - ABC"), self)
        self.actGuide = QAction(QIcon(":/images/script_palette.png"), tr("&Guide"), self)
        self.actTroubleshooter = QAction(QIcon(":/images/script_palette.png"), tr("&Troubleshooter"), self)
        self.actFaq = QAction(QIcon(":/images/script_palette.png"), tr("&FAQ"), self)
        self.actHintsAndTips = QAction(QIcon(":/images/script_palette.png"), tr("&Hints and tips"), self)
        self.actContext = QAction(QIcon(":/images/script_palette.png"), tr("C&ontext F1"), self)
        self.actContext.setShortcut(QKeySequence("F1"))
        self.actOnlineHelp = QAction(QIcon(":/images/script_palette.png"), tr("&On-line help"), self)
        self.actNews = QAction(QIcon(":/images/script_palette.png"), tr("&News"), self)
        self.actWebFaq = QAction(QIcon(":/images/script_palette.png"), tr("&FAQ"), self)
        self.actLibrary = QAction(QIcon(":/images/script_palette.png"), tr("SuperMemo &Library"), self)
        self.actSupport = QAction(QIcon(":/images/script_palette.png"), tr("&Support"), self)
        self.actBugReport = QAction(QIcon(":/images/script_palette.png"), tr("&Bug report"), self)
        self.actQuestionnaire = QAction(QIcon(":/images/script_palette.png"), tr("&Questionnaire"), self)
        self.actRecommended = QAction(QIcon(":/images/script_palette.png"), tr("&Recommended SuperMemo"), self)
        self.actQuestionOfDay = QAction(QIcon(":/images/script_palette.png"), tr("&Question of the Day"), self)
        self.actAbout = QAction(QIcon(":/images/script_palette.png"), tr("&About"), self)
        self.actAbout.setStatusTip(tr("Show the program and author information"))

        self.connect(self.actAbout, SIGNAL("triggered()"), self.on_actAbout_triggered)




    def createMenus(self):
        # File menu
        mnuFile = self.menuBar().addMenu(tr("&File"))
        mnuFile.addAction(self.actNew)
        mnuFile.addAction(self.actOpen)
        mnuFile.addAction(self.actClose)
        mnuFile.addSeparator()

        mnuFile.addAction(self.actCopy)
        mnuFile.addAction(self.actDelete)
        mnuFile.addAction(self.actRepair)
        mnuFile.addAction(self.actMerge)

        mnuFile.addSeparator()

        mnuImport = mnuFile.addMenu(tr("Import"))
        mnuImport.addAction(self.actImportQA)
        mnuImport.addAction(self.actImportXML)
        mnuImport.addAction(self.actImportProbe)
        mnuImport.addAction(self.actImportSuperMemo)
        mnuExport = mnuFile.addMenu(tr("Export"))
        mnuExport.addAction(self.actExportQA)
        mnuExport.addAction(self.actExportXML)
        mnuExport.addAction(self.actExportProbe)
        mnuExport.addAction(self.actExportSuperMemo)

        mnuFile.addSeparator()

        mnuFile.addAction(self.actProperties)

        mnuFile.addSeparator()
        for act in self.actRecentFiles:
            mnuFile.addAction(act)

        mnuFile.addSeparator()
        mnuFile.addAction(self.actExit)

        # Edit menu
        mnuEdit = self.menuBar().addMenu(tr("&Edit"))
        mnuEdit.addAction(self.actNewItem)
        mnuEdit.addAction(self.actNewArticle)
        mnuEdit.addAction(self.actNewTask)
        mnuEdit.addSeparator()
        actImportWeb = mnuEdit.addAction(tr("Import &web pages"))
        actImportWeb.setShortcut(QKeySequence("Shift+F8"))
        mnuEdit.addSeparator()
        actAddToCategory = mnuEdit.addAction(tr("Add &to category"))
        actAddToReading = mnuEdit.addAction(tr("Add to &reading list"))
        actAddToTasklist = mnuEdit.addAction(tr("Add to ta&sklist"))
        mnuEdit.addSeparator()
        actCreateCategory = mnuEdit.addAction(tr("Create &category"))
        actCreateTasklist = mnuEdit.addAction(tr("Create &tasklist"))

        # Search menu
        mnuSearch = self.menuBar().addMenu(tr("&Search"))
        mnuSearch.addAction(self.actFindElements)
        mnuSearch.addAction(self.actFindTexts)
        mnuSearch.addAction(self.actFindWord)
        mnuSearch.addAction(self.actFindString)
        mnuSearch.addSeparator()
        mnuSearch.addAction(self.actTextRegistry)
        mnuSearch.addAction(self.actImages)
        mnuSearch.addAction(self.actSounds)
        mnuSearch.addSeparator()
        mnuSearch.addAction(self.actTemplates)
        mnuSearch.addAction(self.actCategories)
        mnuSearch.addAction(self.actTasklists)
        mnuSearchOtherReg = mnuSearch.addMenu(tr("&Other registries"))
        mnuSearch.addSeparator()
        mnuSearch.addAction(self.actGotoAncestor)
        mnuSearch.addAction(self.actGotoElement)

        # Learn menu
        mnuLearn = self.menuBar().addMenu(tr("&Learn"))

        # View menu
        mnuView = self.menuBar().addMenu(tr("&View"))

        mnuView.addAction(self.actAll)
        mnuView.addAction(self.actOutstanding)
        mnuView.addSeparator()
        mnuView.addAction(self.actMemorized)
        mnuView.addAction(self.actPending)
        mnuView.addAction(self.actDismissed)
        mnuView.addSeparator()
        mnuView.addAction(self.actTopic)
        mnuView.addAction(self.actItems)
        mnuView.addAction(self.actTasks)
        mnuView.addSeparator()
        mnuView.addAction(self.actLastBrowser)
        mnuView.addAction(self.actSearchResults)
        mnuView.addAction(self.actSubset)
        mnuView.addAction(self.actFilter)
        mnuView.addSeparator()
        mnuOtherBrowsers = mnuView.addMenu(tr("Other &browsers"))
        mnuOtherBrowsers.addAction(self.actLeeches)
        mnuOtherBrowsers.addAction(self.actSemiLeeches)
        mnuOtherBrowsers.addAction(self.actDrill)
        mnuOtherBrowsers.addAction(self.actRange)
        mnuOtherBrowsers.addAction(self.actHistory)
        mnuOtherBrowsers.addAction(self.actBranch)



        # Tools mehu
        mnuTools = self.menuBar().addMenu(tr("T&ools"))
        actWorkload = mnuTools.addAction(tr("&Workload"))
        actWorkload.setShortcut(QKeySequence(tr("Ctrl+W")))
        actPlan = mnuTools.addAction(tr("&Plan"))
        actPlan.setShortcut(QKeySequence(tr("Ctrl+P")))
        actMercy = mnuTools.addAction(tr("&Mercy"))
        actMercy.setShortcut(QKeySequence(tr("Ctrl+Y")))
        actTasklist = mnuTools.addAction(tr("&Tasklist"))
        actTasklist.setShortcut(QKeySequence(tr("F4")))
        actReadingList = mnuTools.addAction(tr("&Reading list"))
        actReadingList.setShortcut(QKeySequence(tr("Ctrl+F4")))
        actStatistics = mnuTools.addAction(tr("&Statistics"))
        mnuTools.addSeparator()
        actRandomize = mnuTools.addAction(tr("Randomi&ze"))
        actRandomTest = mnuTools.addAction(tr("R&andom test"))
        actRandomReview = mnuTools.addAction(tr("Ra&ndom review"))
        mnuTools.addSeparator()
        actOptions = mnuTools.addAction(tr("&Options..."))
        actOptions.setShortcut(QKeySequence("Ctrl+Alt+O"))

        # Window menu
        mnuWindow = self.menuBar().addMenu(tr("&Window"))


        # Help menu
        mnuHelp = self.menuBar().addMenu(tr("&Help"))
        mnuHelp.addAction(self.actWelcome)
        mnuHelp.addAction(self.actGuide)
        mnuHelp.addAction(self.actTroubleshooter)
        mnuHelp.addAction(self.actFaq)
        mnuHelp.addAction(self.actHintsAndTips)
        mnuHelp.addAction(self.actContext)
        mnuHelp.addSeparator()
        mnuHelpWeb = mnuHelp.addMenu(tr("W&eb"))
        mnuHelpWeb.addAction(self.actOnlineHelp)
        mnuHelpWeb.addAction(self.actNews)
        mnuHelpWeb.addAction(self.actWebFaq)
        mnuHelpEmail = mnuHelp.addMenu(tr("E-&mail"))
        mnuHelpEmail.addAction(self.actSupport)
        mnuHelpEmail.addAction(self.actLibrary)
        mnuHelpEmail.addSeparator()
        mnuHelpEmail.addAction(self.actBugReport)
        mnuHelpEmail.addAction(self.actQuestionnaire)
        mnuHelpEmail.addAction(self.actRecommended)
        mnuHelp.addSeparator()
        mnuHelp.addAction(self.actQuestionOfDay)
        mnuHelp.addSeparator()
        mnuHelp.addAction(self.actAbout)


    def createToolbars(self):
        # File toolbar
        tbFile = self.addToolBar(tr("File"))

        tbFile.addAction(self.actAbout)
        tbFile.addAction(self.actNew)
        tbFile.addAction(self.actExit)

        tbFile.addAction(self.actNewItem)
        tbFile.addAction(self.actNewArticle)
        tbFile.addAction(self.actNewTask)


        tbFile.addAction(self.actMemorized)
        tbFile.addAction(self.actPending)
        tbFile.addAction(self.actDismissed)
        tbFile.addAction(self.actTasks)
        tbFile.addAction(self.actLastBrowser)
        tbFile.addAction(self.actSubset)
        tbFile.addAction(self.actLeeches)


        # Other toolbar
        tbView = self.addToolBar(tr("View"))
        tbView.addAction(self.actLeeches)
        tbView.addAction(self.actSemiLeeches)
        tbView.addAction(self.actDrill)
        tbView.addAction(self.actRange)
        tbView.addAction(self.actHistory)
        tbView.addAction(self.actBranch)



    def createStatusBar(self):
        self.statusBar().showMessage(tr("Ready."))


    def enterEvent(self, event):
        # on first show, open file from config files
        if not self._windowEntered:
            if config.get_most_recent_file():
                self._openPackFile(config.get_most_recent_file())

        self._windowEntered = True



    def _refreshAppState(self):
        """Sets control active or inactive depending on the database state."""
        # active/inactive actions
        self.btnAdd.setEnabled(self._cardModel.isActive())
        self.btnDelete.setEnabled(self._cardModel.isActive())
        self.btnMoveUp.setEnabled(self._cardModel.isActive())
        self.btnMoveDown.setEnabled(self._cardModel.isActive())
        self.btnShowSelection.setEnabled(self._cardModel.isActive())
        # window title
        if self._cardModel.isActive():
            basename = os.path.basename(self._cardModel.filepath())
            self.setWindowTitle('Mentor - ' + os.path.splitext(basename)[0])
        else:
            self.setWindowTitle('Mentor')
        # recent files list
        for i in range(len(config.GUI_RECENTFILES)):
            self.actRecentFiles[i].setVisible(True)
            self.actRecentFiles[i].setText(config.GUI_RECENTFILES[i])
            self.actRecentFiles[i].setData(QVariant(config.GUI_RECENTFILES[i]))

        for i in range(len(config.GUI_RECENTFILES), config.GUI_RECENTFILES_MAX):
            self.actRecentFiles[i].setVisible(False)


    def _openPackFile(self, fname):
        """Open pack with givem file name."""
        fname = str(fname)
        problem = False
        # FIXME running setCardModelIndex to empty
        # to clean all other views
        # I must redesign the model/view thing
        self.setCardModelIndex(QModelIndex())
        self.cardModel().close()
        try:
            self.cardModel().open(fname)
            self.setCardModelIndex(self.cardModel().index(0, 0))
            config.add_most_recent_file(fname)
        except:
            config.remove_recent_file(fname)
            self.setCardModelIndex(QModelIndex())
            problem = True
        finally:
            self._refreshAppState()
            if problem:
                show_info('Problem opening pack file %s.' % fname)


    def _newPackFile(self, fname):
        """Creates a new pack with given file name."""
        fname = str(fname)
        problem = False
        # FIXME running setCardModelIndex with QModelIndex is  HACK to clean
        # all other views - it must be run before closing cardModel
        # I must redesign the model/view thing
        self.setCardModelIndex(QModelIndex())
        self.cardModel().close()
        try:
            # we want to overwrite
            if os.path.isfile(fname):
                os.remove(fname)
            self.cardModel().open(fname)
            self.setCardModelIndex(self.cardModel().index(0, 0))
            config.add_most_recent_file(fname)
        except:
            config.remove_most_recent_file(fname)
            self.setCardModelIndex(QModelIndex())
            problem = True
        finally:
            self._refreshAppState()
            if problem:
                show_info('Problem creating a new pack file %s.' % fname)


    def qApp_aboutToQuit(self):
        config.save()

    def on_actNew_triggered(self):
        fileName = QFileDialog.getSaveFileName(self, \
            tr("New pack"), ".", tr("Mentor pack files (*.mpk)"))
        if fileName:
            self._newPackFile(fileName)



    def on_actOpen_triggered(self):
        fname = QFileDialog.getOpenFileName(self, \
            tr("Open pack"), ".", tr("Mentor pack files (*.mpk)"))
        if fname:
            self._openPackFile(fname)

    def on_actClose_triggered(self):
        self.setCardModelIndex(QModelIndex())
        self.cardModel().close()
        self._refreshAppState()


    def on_actAbout_triggered(self):
        show_info(tr("MENTOR version %s\nA learning tool\n\nDistributed under license: %s.\n\nAuthors: \n%s" \
            % (__version__, __license__, str(__author__))), self)

    def on_actCopy_triggered(self):
        pass

    def on_actDelete_triggered(self):
        pass

    def on_actRepair_triggered(self):
        pass

    def on_actMerge_triggered(self):
        pass

    def on_actImportQA_triggered(self):
        pass

    def on_actImportXML_triggered(self):
        pass

    def on_actImportProbe_triggered(self):
        pass

    def on_actImportProbe_triggered(self):
        pass

    def on_actExportQA_triggered(self):
        pass

    def on_actExportXML_triggered(self):
        pass

    def on_actExportProbe_triggered(self):
        pass

    def on_actExportProbe_triggered(self):
        pass

    def on_actExportProbe_triggered(self):
        pass

    def on_actRecentFiles_triggered(self):
        self._openPackFile(self.sender().text())


    def lstDrill_currentChanged(self, current, previous):
        self.setCardModelIndex(current)

    def lstDrill_activated(self, current):
        self.setCardModelIndex(current)


    def lstDrill_cardModelIndexChanged(self, current, previous):
        selection = self.lstDrill.selectionModel()
        selectedIndex = selection.selectedIndexes()
        if len(selectedIndex) > 0:
            selectedIndex = selectedIndex[0]
        else:
            selectedIndex = QModelIndex()
        # if is changed then update list view and card model
        if current != selectedIndex:
            selection.setCurrentIndex(current, QItemSelectionModel.SelectCurrent)


    def btnAdd_clicked(self):
        self.cardModel().addNewCard()
        # TODO what if it's not added at the end?
        newIndex = self.cardModel().index(self.cardModel().rowCount() - 1, 0)
        # go to newly added record
        self.setCardModelIndex(newIndex)


    def btnDelete_clicked(self):
        currentIndex = self.cardModelIndex()
        if currentIndex.isValid():
            # try to find currently selected row
            # and go to the same row
            # if rows are missing then go to last
            currentRow = currentIndex.row()
            self.cardModel().deleteCard(currentIndex)
            # go to new index
            newIndex = self.cardModel().index(min(currentRow, self.cardModel().rowCount() - 1), 0)
            self.setCardModelIndex(newIndex)


    def btnLoad_clicked(self):
        show_info('button load was clicked!')


    def btnMoveUp_clicked(self):
        """Moves current selection up by 1 row. If no selection is made then
        selects last item."""
        # move row up
        currentIndex = self.cardModelIndex()
        prevIndex = self._cardModel.getPreviousIndex(currentIndex)
        self.setCardModelIndex(prevIndex)


    def btnMoveDown_clicked(self):
        """Moves current selection down by 1 row. If no selection is made then
        selects first item."""
        currentIndex = self.cardModelIndex()
        nextIndex = self.cardModel().getNextIndex(currentIndex)
        self.setCardModelIndex(nextIndex)



    def btnShowSelection_clicked(self):
        """Displays currenly selected indexes from drill list."""
        current = self.cardModelIndex()
        show_info(self.cardModel().data(current).toString())




def main():
    app = QApplication(sys.argv)
    # app.setStyle('cde')

    w = MainWindow()
    w.resize(700, 600)
    lazyshow(w)
    app.exec_()

if __name__ == "__main__":
    main()
