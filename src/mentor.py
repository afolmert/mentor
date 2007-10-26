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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils_qt import lazyshow, tr, Styles, show_info
from utils import log
from cards import Card, CardDb
import sys
import mentor_rc




class CardModel(QAbstractListModel):
    """Model to be used for list and tree view."""

    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        self.items = ['1', '2', '3', '4', '5', '6' ,'7']

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return len(self.items)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return self.count

    def data(self, index, role=Qt.DisplayRole):
        log('returning data for index = ' + str(index.row()))
        if role not in (Qt.DisplayRole, Qt.UserRole):
            return QVariant()

        if role == Qt.UserRole:
            return QVariant(10)
        else:
            return QVariant(self.items[index.row()])

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

    def getPreviousIdx(self, index):
        """Returns previous index before given or given if it's first."""
        assert index is not None and index.isValid(), "getPreviousIdx: Invalid index given!"
        if index.row() == 0:
            return index
        else:
            return self.index(index.row() - 1, 0)


    def getNextIdx(self, index):
        """Returns next index after given or given if it's last."""
        assert index is not None and index.isValid(), "getNextIdx: Invalid index given!"
        if index.row() == self.rowCount() - 1:
            return index
        else:
            return self.index(index.row() + 1, 0)

    # TODO
    # add special handlers like rowsAboutToBeInserted etc .
    # right now only model to be reset

    # TODO
    # why signals do not work?
    # when I call them in model ?
    #


    def addNewCard(self):
        """Adds a new empty card."""
        self.emit(SIGNAL('modelAboutToBeReset()'))
        self.items.append(str(len(self.items)))
        return self.createIndex(len(self.items) - 1, 0)
        # TODO
        # why these do not work ?
        self.reset()
        self.emit(SIGNAL('modelReset()'))


    def deleteCard(self, index):
        assert index is not None and index.isValid(), "deleteCard: Invalid index given!"
        self.emit(SIGNAL('modelAboutToBeReset()'))
        del self.items[index.row()]
        # why these do not work??
        self.reset()
        self.emit(SIGNAL('modelReset()'))

    # TODO question
    # how to update card if peg is somewhere else ?
    # maybe keep blob as well ?
    # the items are then splitted
    def updateCard(self, index, question, answer):
        assert index is not None and index.isValid(), "updateCard: Invalid index given!"
        self.items[index.row()] = question
        # TODO
        # update data in the model
        self.emit(SIGNAL('dataChanged(QModelIndex)'), index)




# main gui parts
# card widget is a sort of delegate and it should behave as one
# it currently has card model assigned
# or is it like more like listwidget

class AbstractCardWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        # these control what it looks for
        self.cardModel = None
        self.cardModelIdx = None


    def updateWidget(self):
        # this is virtual method to be subclassed
        pass

    def setCardModel(self, cardModel):
        self.cardModel = cardModel
        # invalidate cardModelIdx
        self.cardModelIdx = None
        self.updateWidget()

    def cardModel(self):
        return self.cardModel


    def setCardModelIdx(self, index):
        log('setCardModelIdx for index %d ' % index.row())
        assert self.cardModel is not None, "Invalid card model"
        assert index is not None and index.isValid(), "Invalid card model index"
        # setting only if different
        self.cardModelIdx = index
        self.updateWidget()


    def cardModelIdx(self):
        return self.cardModelIdx



class CardWidget(AbstractCardWidget):
    """Widget for displaying current card.
    May be later subclassed to display all kinds of cards:
     RTF , graphical, simple etc.
    """
    # TODO add splitter between question and answer
    # answer by default a little lower
    #
    def __init__(self, parent=None):
        AbstractCardWidget.__init__(self, parent)
        self.dirty = False

        self.txtQuestion = QTextEdit()
        self.txtQuestion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.txtQuestion.setFont(QFont("Tahoma", 18, QFont.Bold))
        self.txtQuestion.setText("question text..")
        self.txtQuestion.setStyle(Styles.windowsStyle())

        self.txtAnswer = QTextEdit()
        self.txtAnswer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.txtAnswer.setFont(QFont("Tahoma", 18, QFont.Bold))
        self.txtAnswer.setText("answer text..")
        self.txtAnswer.setStyle(Styles.windowsStyle())

        self.connect(self.txtAnswer, SIGNAL('textChanged()'), self.setDirty)
        self.connect(self.txtQuestion, SIGNAL('textChanged()'), self.setDirty)

        layout = QVBoxLayout()
        layout.addWidget(self.txtQuestion)
        layout.addWidget(self.txtAnswer)

        self.setLayout(layout)


    def updateWidget(self):
        if self.cardModelIdx and self.cardModelIdx.isValid():
            try:
                question = self.cardModel.data(self.cardModelIdx).toString()
                answer = self.cardModel.data(self.cardModelIdx).toString()
            except:
                question = ''
                answer = ''
            self.txtQuestion.setText(question)
            self.txtAnswer.setText(answer)
        else:
            self.txtQuestion.setText('')
            self.txtAnswer.setText('')

    # TODO
    # update data only on focus lost event if is dirty
    # right now it updates

    def setDirty(self, dirty=True):
        self.dirty = dirty
        if self.cardModelIdx:
            self.cardModel.updateCard(self.cardModelIdx, \
                 self.txtQuestion.toPlainText(), self.txtAnswer.toPlainText())
        self.dirty = False

    def dirty():
        return self.dirty



class CardDetailWidget(AbstractCardWidget):
    """Widget for displaying card details (score, hints, review dates etc.)"""
    def __init__(self, parent=None):
        AbstractCardWidget.__init__(self, parent)

    def updateWidget(self):
        # display information from the current cardModel and cardModelIdx
        pass



class CardSourceWidget(AbstractCardWidget):
    """Widget for displaying XML source for card """
    def __init__(self, parent=None):
        AbstractCardWidget.__init__(self, parent)

    def updateWidget(self):
        # display information from the current cardModel and cardModelIdx
        pass


class MainWindow(QMainWindow):
    """My widget subclass."""

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)


        self.setWindowTitle("Mentor")

        self.move(50, 50)


        self.createCentralWidget()
        self.createActions()
        self.createMenus()
        self.createToolbars()
        self.createStatusBar()


    def createCentralWidget(self):
        self.central = QWidget(self)
        self.central.move(40, 40)

        # set up controls
        # items panel
        self.cardModel = CardModel()

        self.lstDrill = QListView()
        self.lstDrill.setMaximumWidth(140)
        self.lstDrill.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.lstDrill.setFocus()
        self.lstDrill.setStyle(Styles.windowsStyle())

        self.lstDrill.setModel(self.cardModel)

        #self.treeContents = QTreeWidget()
        #self.treeContents.addTopLevelItem(QTreeWidgetItem(["Sample1"]))
        #self.treeContents.addTopLevelItem(QTreeWidgetItem(["Sample2"]))
        #self.treeContents.addTopLevelItem(QTreeWidgetItem(["Sample3"]))
        #self.treeContents.setMaximumWidth(140)
        #self.treeContents.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        #self.treeContents.setStyle(Styles.windowsStyle())

        itemsLayout = QHBoxLayout()
        itemsLayout.addWidget(self.lstDrill)
        #itemsLayout.addWidget(self.treeContents)

        # question and answer panel

        self.cardWidget = CardWidget()
        self.cardWidget.setCardModel(self.cardModel)

        # buttons
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
        # FIXME connecting these 4 times cause sometimes I don't get proper
        # messages
        # when I edit something and press Down
        # and then click on what I edited then selection changed does not catch
        # it
        self.connect(self.lstDrill.selectionModel(), \
                        SIGNAL('currentChanged(QModelIndex, QModelIndex)'), \
                        self.lstDrill_currentChanged)
        self.connect(self.lstDrill.selectionModel(), \
                        SIGNAL('currentRowChanged(QModelIndex, QModelIndex)'), \
                        self.lstDrill_currentChanged)
        self.connect(self.lstDrill, \
                        SIGNAL('activated(QModelIndex)'), \
                        self.lstDrill_activated)
        self.connect(self.lstDrill, \
                        SIGNAL('clicked(QModelIndex)'), \
                        self.lstDrill_activated)


        buttonsLayout = QHBoxLayout()

        self.btnAdd.setStyle(Styles.windowsStyle())
        self.btnDelete.setStyle(Styles.windowsStyle())
        self.btnLoad.setStyle(Styles.windowsStyle())
        self.btnMoveUp.setStyle(Styles.windowsStyle())
        self.btnMoveDown.setStyle(Styles.windowsStyle())
        self.btnShowSelection.setStyle(Styles.windowsStyle())

        buttonsLayout.addWidget(self.btnMoveUp)
        buttonsLayout.addWidget(self.btnMoveDown)
        buttonsLayout.addWidget(self.btnShowSelection)
        buttonsLayout.addWidget(self.btnAdd)
        buttonsLayout.addWidget(self.btnDelete)
        buttonsLayout.addWidget(self.btnLoad)



        textLayout = QVBoxLayout()
        textLayout.addWidget(self.cardWidget)
        textLayout.addLayout(buttonsLayout)

        # main layout
        mainLayout = QHBoxLayout()
        mainLayout.addLayout(itemsLayout)
        mainLayout.addLayout(textLayout)

        self.central.setLayout(mainLayout)
        self.setCentralWidget(self.central)



    def createActions(self):
        # File actions
        self.actNew = QAction(QIcon(":/images/world.png"), tr("&Open..."), self)
        self.actNew.setShortcut(QKeySequence(tr("Ctrl+O")))
        self.actNew.setStatusTip(tr("Create a new file..."))
        self.connect(self.actNew, SIGNAL("tiggered()"), self.on_actNew_triggered)
        self.actExit = QAction(QIcon(":/images/clock_play.png"), tr("E&xit"), self)
        self.actExit.setShortcut(QKeySequence(tr("Ctrl+Q")))
        self.actExit.setStatusTip(tr("Exits the application."))

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


    def on_clicked(self):
        show_info("Hello world!")


    def on_actNew_triggered(self):
        show_info("actNew was pressed!", self)
        pass


    def on_actAbout_triggered(self):
        show_info(tr("MENTOR version %s\nA learning tool\n\nDistributed under license: %s.\n\nAuthors: \n%s" \
            % (__version__, __license__, str(__author__))), self)


    def lstDrill_currentChanged(self, current, previous):
        if current.row() <> previous.row():
            log('lstDrill_currentChanged for current: %d and previous: %d' % (current.row(), previous.row()))
            if current is None:
                current = previous
            self.cardWidget.setCardModelIdx(current)

    def lstDrill_activated(self, index):
        self.cardWidget.setCardModelIdx(index)


    def lstDrill_getSelectedIdx(self):
        """Returns currently selected index of the lstDrill."""
        selection = self.lstDrill.selectionModel()
        # get current selection
        selectedIdx = selection.selectedIndexes()
        if len(selectedIdx) == 0:
            selectedIdx = self.cardModel.index(self.cardModel.rowCount() - 1, 0)
        else:
            selectedIdx = selectedIdx[0]
        return selectedIdx


    def btnAdd_clicked(self):
        oldIdx = self.lstDrill_getSelectedIdx()
        newIdx = self.cardModel.addNewCard()
        self.cardModel.reset()
        # go to newly added record
        selection = self.lstDrill.selectionModel()
        selection.select(newIdx, QItemSelectionModel.Select | QItemSelectionModel.Current)
        # inform about changed selection
        selection.emit(SIGNAL('currentChanged(QModelIndex, QModelIndex)'), newIdx, oldIdx)



    def btnDelete_clicked(self):
        selectedIdx = self.lstDrill_getSelectedIdx()
        if selectedIdx and selectedIdx.isValid():
            # try to find where to go after deletion
            newIdx = self.cardModel.getNextIdx(selectedIdx)
            if newIdx.row() == selectedIdx.row():
                newIdx = self.cardModel.getPreviousIdx(selectedIdx)

            self.cardModel.deleteCard(selectedIdx)
            #
            self.cardModel.reset()
            # go to new index
            selection = self.lstDrill.selectionModel()
            selection.select(newIdx, QItemSelectionModel.Select | QItemSelectionModel.Current)
            # informat about chaging of the current
            selection.emit(SIGNAL('currentChanged(QModelIndex, QModelIndex)'), newIdx, QModelIndex())


    def btnLoad_clicked(self):
        show_info('button load was clicked!')


    def btnMoveUp_clicked(self):
        """Moves current selection up by 1 row. If no selection is made then
        selects last item."""
        selection = self.lstDrill.selectionModel()
        # get current selection
        selectedIdx = selection.selectedIndexes()
        if len(selectedIdx) == 0:
            selectedIdx = self.cardModel.index(self.cardModel.rowCount() - 1, 0)
        else:
            selectedIdx = selectedIdx[0]
        # move row up
        prev = self.cardModel.getPreviousIdx(selectedIdx)
        selection.select(prev, QItemSelectionModel.Select | QItemSelectionModel.Current)
        selection.emit(SIGNAL('currentChanged(QModelIndex, QModelIndex)'), prev, selectedIdx)


    def btnMoveDown_clicked(self):
        """Moves current selection down by 1 row. If no selection is made then
        selects first item."""
        selection = self.lstDrill.selectionModel()
        # get current selection
        selectedIdx = selection.selectedIndexes()
        if len(selectedIdx) == 0:
            selectedIdx = self.cardModel.index(0, 0)
        else:
            selectedIdx = selectedIdx[0]
        # move row down
        next = self.cardModel.getNextIdx(selectedIdx)
        selection.select(next, QItemSelectionModel.Select | QItemSelectionModel.Current)
        selection.emit(SIGNAL('currentChanged(QModelIndex, QModelIndex)'), next, selectedIdx)



    def btnShowSelection_clicked(self):
        """Displays currenly selected indexes from drill list."""
        selected = ''
        model = self.lstDrill.selectionModel()
        for index in model.selectedIndexes():
            selected = selected + self.cardModel.data(index).toString()
        show_info(selected)




def main():
    app = QApplication(sys.argv)
    app.setStyle('cde')

    w = MainWindow()
    w.resize(700, 600)
    lazyshow(w)
    app.exec_()

if __name__ == "__main__":
    main()
