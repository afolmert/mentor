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
from models import CardModel, DrillModel
from database import Card
from views import CardMainView, CardSourceView, CardDetailView, CardGridView
import mentor_rc




class DrillWindow(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.setWindowTitle('Mentor Drill')

        self.model = DrillModel()
        self.currentCard = Card()


        # card view
        self.cardView = CardMainView()

        # buttons bar
        self.buttons = QWidget(self)

        self.btnNext = QPushButton("&1. Next card")
        self.btnShowAnswer = QPushButton("&2. Show answer")
        self.btnGoodScore = QPushButton("&3. Good score")
        self.btnBadScore = QPushButton("&4. Bad score")
        self.btnShuffleCards = QPushButton("&5. Shuffle cards")
        self.btnPrintCards = QPushButton("&6. Print cards")
        self.btnClose = QPushButton("&7. Close")

        # todo move this to actions
        self.connect(self.btnNext, SIGNAL('clicked()'), self.on_btnNext_clicked)
        self.connect(self.btnShowAnswer, SIGNAL('clicked()'), self.on_btnShowAnswer_clicked)
        self.connect(self.btnGoodScore, SIGNAL('clicked()'), self.on_btnGoodScore_clicked)
        self.connect(self.btnBadScore, SIGNAL('clicked()'), self.on_btnBadScore_clicked)
        self.connect(self.btnShuffleCards, SIGNAL('clicked()'), self.on_btnShuffleCards_clicked)
        self.connect(self.btnPrintCards, SIGNAL('clicked()'), self.on_btnPrintCards_clicked)
        self.connect(self.btnClose, SIGNAL('clicked()'), self.on_btnClose_clicked)

        buttonsLayout = QHBoxLayout()

        buttonsLayout.addWidget(self.btnNext)
        buttonsLayout.addWidget(self.btnShowAnswer)
        buttonsLayout.addWidget(self.btnGoodScore)
        buttonsLayout.addWidget(self.btnBadScore)
        buttonsLayout.addWidget(self.btnShuffleCards)
        buttonsLayout.addWidget(self.btnPrintCards)
        buttonsLayout.addWidget(self.btnClose)

        self.buttons.setLayout(buttonsLayout)

        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setMargin(1)
        layout.addWidget(self.cardView)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        self.setGeometry(100, 100, 500, 500)

        self.cardView.displayCard(self.currentCard)


    def loadCards(self, cards):
        """Loads a list of cards to model."""
        for card in cards:
            self.model.addCard(card)
        self.currentCard = self.model.selectNextCard()
        self.cardView.displayCard(self.currentCard, True, False)

    def on_btnNext_clicked(self):
        self.currentCard = self.model.selectNextCard()
        self.cardView.displayCard(self.currentCard, True, False)

    def on_btnShowAnswer_clicked(self):
        self.cardView.displayCard(self.currentCard, True, True)

    def on_btnGoodScore_clicked(self):
        self.model.scoreCard(self.currentCard, DrillModel.Good)

    def on_btnBadScore_clicked(self):
        self.model.scoreCard(self.currentCard, DrillModel.Bad)

    def on_btnShuffleCards_clicked(self):
        self.model.shuffleCards()
        self.currentCard = self.model.selectNextCard()
        self.cardView.displayCard(self.currentCard, True, False)

    def on_btnPrintCards_clicked(self):
        self.model.printCards()

    def on_btnClose_clicked(self):
        self.close()



class MainWindow(QMainWindow):
    """Central window for the Mentor app"""

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)

        # set up controls
        # items panel
        self._cardModel = CardModel()
        self._cardModelIndex = QModelIndex()  # current index for card model

        self.setWindowTitle("Mentor")
        self.setWindowIcon(QIcon(QPixmap(":/images/mentor.png")))

        self.move(50, 50)
        self.createCentralWidget()
        self.createActions()
        self.createMenus()
        self.createToolbars()
        self.createStatusBar()

        self.connect(qApp, SIGNAL('aboutToQuit()'), self.qApp_aboutToQuit)

        QTimer.singleShot(0, self._openRecentFile)



    def createCentralWidget(self):

        ##########################
        # setup central widget

        # question and answer panel
        self.cardMainView = CardMainView(self)
        self.cardMainView.setModel(self._cardModel)

        self.setCentralWidget(self.cardMainView)


        ##########################
        # items view
        self.lstDrill = CardGridView(self)
        self.lstDrill.setModel(self._cardModel)

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
        self.actNew = QAction(tr("&New pack..."), self)
        self.actNew.setStatusTip(tr("Create a new pack..."))
        self.connect(self.actNew, SIGNAL("triggered()"), self.on_actNew_triggered)

        self.actOpen = QAction(tr("&Open pack..."), self)
        self.actOpen.setShortcut(QKeySequence(tr("Ctrl+O")))
        self.actOpen.setStatusTip(tr("Open an existing pack..."))
        self.connect(self.actOpen, SIGNAL("triggered()"), self.on_actOpen_triggered)
        self.actClose = QAction(tr("&Close pack"), self)
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
        #
        self.actExit = QAction(tr("E&xit"), self)
        self.actExit.setShortcut(QKeySequence(tr("Ctrl+Q")))
        self.actExit.setStatusTip(tr("Exits the application."))
        self.connect(self.actExit, SIGNAL("triggered()"), qApp, SLOT("quit()"))

        # Edit actions
        self.actUndo = QAction(tr("&Undo"), self)
        self.actUndo.setShortcut(QKeySequence(tr("Ctrl+Z")))
        self.actRedo = QAction(tr("Re&do"), self)
        self.actRedo.setShortcut(QKeySequence(tr("Ctrl+Y")))
        self.actCut = QAction(tr("Cu&t"), self)
        self.actCut.setShortcut(QKeySequence(tr("Ctrl+X")))
        self.actCopy = QAction(tr("&Copy"), self)
        self.actUndo.setShortcut(QKeySequence(tr("Ctrl+C")))
        self.actPaste = QAction(tr("&Paste"), self)
        self.actPaste.setShortcut(QKeySequence(tr("Ctrl+V")))
        self.actCutAppend = QAction(tr("Cut and append"), self)
        self.actCutAppend.setShortcut(QKeySequence(tr("Ctrl+Shift+X")))
        self.actCopyAppend = QAction(tr("Copy and append"), self)
        self.actCopyAppend.setShortcut(QKeySequence(tr("Ctrl+Shift+C")))
        self.actSelectAll = QAction(tr("Select &all"), self)
        self.actSelectAll.setShortcut(QKeySequence(tr("Ctrl+A")))
        self.actSelectLine = QAction(tr("Select &line"), self)
        self.actSelectWord = QAction(tr("Select &word"), self)
        self.actSelectWord.setShortcut(QKeySequence(tr("Ctrl+J")))
        self.actDelete = QAction(tr("&Delete"), self)
        self.actDelete.setShortcut(QKeySequence(tr("DEL")))
        self.actDeleteLine = QAction(tr("&Delete &line"), self)
        self.actDeleteLine.setShortcut(QKeySequence(tr("Ctrl+E")))
        self.actDeleteToStartLine = QAction(tr("Delete to &start of line"), self)
        self.actDeleteToStartLine.setShortcut(QKeySequence(tr("Ctrl+F11")))
        self.actDeleteToEndLine = QAction(tr("Delete to &end of line"), self)
        self.actDeleteToEndLine.setShortcut(QKeySequence(tr("Ctrl+F12")))



        # Cards actions
        self.actFirstCard = QAction(tr("&First"), self)
        self.actFirstCard.setShortcut(QKeySequence("Shift+Ctrl+PgUp"))
        self.connect(self.actFirstCard, SIGNAL("triggered()"), self.on_actFirstCard_triggered)
        self.actPreviousCard = QAction(tr("&Previous"), self)
        self.actPreviousCard.setShortcut(QKeySequence("Ctrl+PgUp"))
        self.connect(self.actPreviousCard, SIGNAL("triggered()"), self.on_actPreviousCard_triggered)
        self.actNextCard = QAction(tr("&Next"), self)
        self.actNextCard.setShortcut(QKeySequence("Ctrl+PgDown"))
        self.connect(self.actNextCard, SIGNAL("triggered()"), self.on_actNextCard_triggered)
        self.actLastCard = QAction(tr("&Last"), self)
        self.actLastCard.setShortcut(QKeySequence("Shift+Ctrl+PgDown"))
        self.connect(self.actLastCard, SIGNAL("triggered()"), self.on_actLastCard_triggered)

        self.actAddCard = QAction(tr("&Add"), self)
        self.actAddCard.setShortcut(QKeySequence(tr("Ctrl+N")))
        self.connect(self.actAddCard, SIGNAL("triggered()"), self.on_actAddCard_triggered)
        self.actInsertCard = QAction(tr("&Insert"), self)
        self.actInsertCard.setShortcut(QKeySequence(tr("Ctrl+Ins")))
        self.connect(self.actInsertCard, SIGNAL("triggered()"), self.on_actInsertCard_triggered)
        self.actDeleteCard = QAction(tr("&Delete"), self)
        self.actDeleteCard.setShortcut(QKeySequence(tr("Ctrl+Del")))
        self.connect(self.actDeleteCard, SIGNAL("triggered()"), self.on_actDeleteCard_triggered)

        self.actSort = QAction(tr("&Sort..."), self)
        self.actFilter = QAction(tr("&Filter..."), self)

        #  Cards action -> from Edit/SuperMemo

        self.actNewItem = QAction(tr("Add a new i&tem"), self)
        self.actNewItem.setShortcut(QKeySequence(tr("Alt+A")))
        self.actNewArticle = QAction(tr("Add a new &article"), self)
        self.actNewArticle.setShortcut(QKeySequence(tr("Ctrl+Alt+N")))
        self.actNewTask = QAction(tr("Add a &new task"), self)
        self.actNewTask.setShortcut(QKeySequence("Ctrl+Alt+A"))

        # Search actions
        self.actFindElements = QAction(tr("&Find elements"), self)
        self.actFindElements.setShortcut(QKeySequence(tr("Ctrl+F")))
        self.actFindTexts = QAction(tr("Fi&nd texts"), self)
        self.actFindTexts.setShortcut(QKeySequence(tr("Ctrl+S")))
        self.actFindWord = QAction(tr("Fin&d word"), self)
        self.actFindString = QAction(tr("Find st&ring"), self)
        self.actFindString.setShortcut(QKeySequence(tr("F3")))
        self.actTextRegistry = QAction(tr("Te&xt registry"), self)
        self.actTextRegistry.setShortcut(QKeySequence(tr("Ctrl+Alt+X")))
        self.actImages =  QAction(tr("&Images"), self)
        self.actSounds =  QAction(tr("&Sounds"), self)
        self.actTemplates = QAction(tr("&Templates"), self)
        self.actCategories = QAction(tr("&Categories"), self)
        self.actTasklists = QAction(tr("Tas&klists"), self)
        self.actOtherRegistries = QAction(tr("&Other registries"), self)
        self.actFont = QAction(tr("&Font"), self)
        self.actTranslation = QAction(tr("&Translation"), self)
        self.actPronunciationByWord = QAction(tr("&Pronunciation by word"), self)
        self.actPronunciationBySound = QAction(tr("Pronunciation by soun&d"), self)
        self.actComment = QAction(tr("&Comment"), self)
        self.actVideo = QAction(tr("&Video"), self)
        self.actScript = QAction(tr("&Script"), self)
        self.actProgram = QAction(tr("&OLE Object"), self)
        self.actGotoAncestor = QAction(tr("Go to &ancestor"), self)
        self.actGotoElement = QAction(tr("Go to &element"), self)
        self.actGotoElement.setShortcut(QKeySequence(tr("Ctrl+G")))

        # Learn actions
        self.actLearnAllStages = QAction(tr("&All stages"), self)
        self.actLearnAllStages.setShortcut(QKeySequence(tr("Ctrl+L")))
        self.actLearnOutstanding = QAction(tr("1. &Outstanding material"), self)
        self.actLearnNew = QAction(tr("2. &New material"), self)
        self.actLearnNew.setShortcut(QKeySequence(tr("Ctrl-F2")))
        self.actLearnFinalDrill = QAction(tr("3. &Final drill"), self)
        self.actLearnFinalDrill.setShortcut(QKeySequence(tr("Ctrl+F2")))
        self.connect(self.actLearnFinalDrill, SIGNAL("triggered()"), self.on_actFinalDrill_triggered)
        self.actReadingList = QAction(tr("&Reading list"), self)
        self.actReadingList.setShortcut(QKeySequence(tr("Shift+Ctrl+F4")))
        self.actPostponeTopics = QAction(tr("&Topics"), self)
        self.actPostponeItems = QAction(tr("&Items"), self)
        self.actPostponeAll = QAction(tr("&All"), self)
        self.actRandomizeRepetitions = QAction(tr("Randomi&ze repetitions"), self)
        self.actRandomizeRepetitions.setShortcut(QKeySequence("Shift+Ctrl+F11"))
        self.actRandomLearning = QAction(tr("Ran&dom learning"), self)
        self.actRandomLearning.setShortcut(QKeySequence("Ctrl+F11"))
        self.actCutDrills = QAction("&Cut drills", self)

        # View actions
        self.actAll = QAction(tr("&All"), self)
        self.actOutstanding = QAction(tr("&Outstanding"), self)
        self.actMemorized = QAction(tr("&Memorized"), self)
        self.actPending = QAction(tr("&Pending"), self)
        self.actDismissed = QAction(tr("&Dismissed"), self)
        self.actTopic = QAction(tr("&Topic"), self)
        self.actItems = QAction(tr("&Items"), self)
        self.actTasks = QAction(tr("Ta&ks"), self)
        self.actLastBrowser = QAction(tr("&Last browser"), self)
        self.actSearchResults = QAction(tr("&Search results"), self)
        self.actSubset = QAction(tr("S&ubset"), self)
        self.actFilter = QAction(tr("&Filter..."), self)
        self.actLeeches  = QAction(tr("&Leeches"), self)
        self.actLeeches.setShortcut(QKeySequence("Shift+F3"))
        self.actSemiLeeches = QAction(tr("&Semi-leeches"), self)
        self.actDrill = QAction(tr("&Drill"), self)
        self.actRange = QAction(tr("&Range"), self)
        self.actHistory = QAction(tr("&History"), self)
        self.actBranch = QAction(tr("&Branch"), self)

        # Tools actions
        self.actWorkload = QAction(tr("&Workload"), self)
        self.actWorkload.setShortcut(QKeySequence("Ctrl+W"))
        self.actPlan = QAction(tr("&Plan"), self)
        self.actWorkload.setShortcut(QKeySequence("Ctrl+P"))
        self.actMercy = QAction(tr("&Mercy"), self)
        self.actMercy.setShortcut(QKeySequence("Ctrl+Y"))
        self.actTasklist = QAction(tr("&Tasklist"), self)
        self.actTasklist.setShortcut(QKeySequence("F4"))
        self.actReadingList = QAction(tr("&Reading list"), self)
        self.actReadingList.setShortcut(QKeySequence(tr("Ctrl+F4")))
        self.actStatistics = QAction(tr("S&tatistics"), self)
        self.actElementData = QAction(tr("&Element data"), self)
        self.actAnalysis = QAction(tr("&Analysis"), self)
        self.actAnalysis.setShortcut(QKeySequence(tr("Ctrl+Alt+I")))
        self.actSimulation = QAction(tr("&Simulation"), self)
        self.actReport = QAction(tr("&Report"), self)
        self.actRandomizeDrill = QAction(tr("&Drill"), self)
        self.actRandomizePending = QAction(tr("&Pending"), self)
        self.actRandomTest = QAction(tr("&Resume test"), self)
        self.actRandomAll = QAction(tr("&All"), self)
        self.actRandomAll.setShortcut(QKeySequence(tr("Alt+F11")))
        self.actRandomPending = QAction(tr("&Pending"), self)
        self.actRandomMemorized = QAction(tr("&Memorized"), self)
        self.actRandomDismissed = QAction(tr("&Dismissed"), self)
        self.actRandomTopics = QAction(tr("&Topics"), self)
        self.actRandomItems = QAction(tr("&Items"), self)
        self.actRandomFilter = QAction(tr("&Filter"), self)
        self.actRandomLeeches = QAction(tr("&Leeches"), self)
        self.actRandomSubset = QAction(tr("&Subset"), self)
        self.actRandomBranch = QAction(tr("&Branch"), self)
        self.actOptions = QAction(tr("&Options"), self)
        self.actOptions.setShortcut(tr("Ctrl+Alt+O"))
        self.connect(self.actOptions, SIGNAL("triggered()"), self.on_actOptions_triggered)


        # Window actions
        self.actDock = QAction(tr("&Dock"), self)
        self.actToolbarRead = QAction(tr("&Read"), self)
        self.actToolbarCompose = QAction("&Compose", self)
        self.actToolbarFormat = QAction("&Format", self)
        self.actToolbarTime = QAction("&Time", self)
        self.actToolbarActions = QAction("&Actions", self)
        self.actDockToolbars = QAction("&Dock toolbars", self)
        self.actStatusBar = QAction(tr("&Status bar"), self)
        self.actBackground = QAction(tr("&Background"), self)
        self.actBackground.setShortcut(QKeySequence(tr("Ctrl+Alt+F10")))
        self.actHints = QAction(tr("H&ints"), self)
        self.actSelectCategory = QAction(tr("&Category"), self)
        self.actSelectCategory.setShortcut(QKeySequence(tr("Ctrl+Alt+C")))
        self.actSelectTasklist = QAction(tr("&Tasklist"), self)
        self.actSelectTasklist.setShortcut(QKeySequence(tr("Ctrl+Alt+T")))
        self.actSelectNextWindow = QAction(tr("&Next window"), self)
        self.actSelectNextWindow.setShortcut(QKeySequence(tr("Ctrl+F6")))
        self.actLayoutManager = QAction(tr("&Layout Manager"), self)
        self.actApplyDefaultLayout = QAction(tr("&Apply default layout"), self)
        self.actClassLayout = QAction(tr("&Class layout"), self)
        self.actClassLayout.setShortcut(QKeySequence(tr("F5")))
        self.actSaveCustomLayout = QAction(tr("&Save custom layout"), self)
        self.actSaveAsDefault = QAction(tr("Sa&ve as default"), self)
        self.actSaveAsDefault.setShortcut(QKeySequence(tr("Shift+Ctrl+F5")))
        self.actBackgroundColor = QAction(tr("&Background color"), self)
        self.actLayoutLastUsed = QAction(tr("Last used"), self)
        self.actLayoutContents = QAction(tr("Contents"), self)
        self.actLayoutClassic = QAction(tr("Classic"), self)
        self.actLayoutBrowser = QAction(tr("Browser"), self)

        # Help actions
        self.actWelcome = QAction(tr("&Welcome - ABC"), self)
        self.actGuide = QAction(tr("&Guide"), self)
        self.actTroubleshooter = QAction(tr("&Troubleshooter"), self)
        self.actFaq = QAction(tr("&FAQ"), self)
        self.actHintsAndTips = QAction(tr("&Hints and tips"), self)
        self.actContext = QAction(tr("C&ontext F1"), self)
        self.actContext.setShortcut(QKeySequence("F1"))
        self.actOnlineHelp = QAction(tr("&On-line help"), self)
        self.actNews = QAction(tr("&News"), self)
        self.actWebFaq = QAction(tr("&FAQ"), self)
        self.actLibrary = QAction(tr("SuperMemo &Library"), self)
        self.actSupport = QAction(tr("&Support"), self)
        self.actBugReport = QAction(tr("&Bug report"), self)
        self.actQuestionnaire = QAction(tr("&Questionnaire"), self)
        self.actRecommended = QAction(tr("&Recommended SuperMemo"), self)
        self.actQuestionOfDay = QAction(tr("&Question of the Day"), self)
        self.actAbout = QAction(tr("&About"), self)
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

        # Menu Edit
        mnuEdit = self.menuBar().addMenu(tr("&Edit"))
        mnuEdit.addAction(self.actUndo)
        mnuEdit.addAction(self.actRedo)
        mnuEdit.addSeparator()
        mnuEdit.addAction(self.actCut)
        mnuEdit.addAction(self.actCopy)
        mnuEdit.addAction(self.actPaste)
        mnuEdit.addAction(self.actCutAppend)
        mnuEdit.addAction(self.actCopyAppend)
        mnuEdit.addSeparator()
        mnuEdit.addAction(self.actSelectAll)
        mnuEdit.addAction(self.actSelectLine)
        mnuEdit.addAction(self.actSelectWord)
        mnuEdit.addSeparator()
        mnuEdit.addAction(self.actDelete)
        mnuEdit.addAction(self.actDeleteLine)
        mnuEdit.addAction(self.actDeleteToStartLine)
        mnuEdit.addAction(self.actDeleteToEndLine)

        # Cards menu
        mnuCards = self.menuBar().addMenu(tr("&Cards"))
        mnuCards.addAction(self.actFirstCard)
        mnuCards.addAction(self.actPreviousCard)
        mnuCards.addAction(self.actNextCard)
        mnuCards.addAction(self.actLastCard)
        mnuCards.addSeparator()
        mnuCards.addAction(self.actAddCard)
        mnuCards.addAction(self.actInsertCard)
        mnuCards.addAction(self.actDeleteCard)
        mnuCards.addSeparator()
        mnuCards.addAction(self.actSort)
        mnuCards.addAction(self.actFilter)
        mnuCards.addSeparator()
        mnuCards.addAction(self.actNewItem)
        mnuCards.addAction(self.actNewArticle)
        mnuCards.addAction(self.actNewTask)
        mnuCards.addSeparator()
        actImportWeb = mnuCards.addAction(tr("Import &web pages"))
        actImportWeb.setShortcut(QKeySequence("Shift+F8"))
        mnuCards.addSeparator()
        actAddToCategory = mnuCards.addAction(tr("Add &to category"))
        actAddToReading = mnuCards.addAction(tr("Add to &reading list"))
        actAddToTasklist = mnuCards.addAction(tr("Add to ta&sklist"))
        mnuCards.addSeparator()
        actCreateCategory = mnuCards.addAction(tr("Create &category"))
        actCreateTasklist = mnuCards.addAction(tr("Create &tasklist"))

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
        mnuSearchOtherReg.addAction(self.actFont)
        mnuSearchOtherReg.addSeparator()
        mnuSearchOtherReg.addAction(self.actTranslation)
        mnuSearchOtherReg.addAction(self.actPronunciationByWord)
        mnuSearchOtherReg.addAction(self.actPronunciationBySound)
        mnuSearchOtherReg.addAction(self.actComment)
        mnuSearchOtherReg.addSeparator()
        mnuSearchOtherReg.addAction(self.actVideo)
        mnuSearchOtherReg.addAction(self.actScript)
        mnuSearchOtherReg.addAction(self.actProgram)
        mnuSearch.addSeparator()
        mnuSearch.addAction(self.actGotoAncestor)
        mnuSearch.addAction(self.actGotoElement)


        # Learn menu
        mnuLearn = self.menuBar().addMenu(tr("&Learn"))
        mnuLearn.addAction(self.actLearnAllStages)
        mnuLearnSelected = mnuLearn.addMenu(tr("&Selected stages"))
        mnuLearnSelected.addAction(self.actLearnOutstanding)
        mnuLearnSelected.addAction(self.actLearnNew)
        mnuLearnSelected.addAction(self.actLearnFinalDrill)
        mnuLearnSelected.addSeparator()
        mnuLearnSelected.addAction(self.actReadingList)
        mnuPostpone = mnuLearn.addMenu(tr("&Postpone"))
        mnuPostpone.addAction(self.actPostponeTopics)
        mnuPostpone.addAction(self.actPostponeItems)
        mnuPostpone.addAction(self.actPostponeAll)
        mnuLearn.addSeparator()
        mnuRandom = mnuLearn.addMenu(tr("&Random"))
        mnuRandom.addAction(self.actRandomizeRepetitions)
        mnuRandom.addAction(self.actRandomLearning)
        mnuLearn.addAction(self.actCutDrills)

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
        mnuTools.addAction(self.actWorkload)
        mnuTools.addAction(self.actPlan)
        mnuTools.addAction(self.actMercy)
        mnuTools.addAction(self.actTasklist)
        mnuTools.addAction(self.actReadingList)
        mnuStatistics = mnuTools.addMenu(tr("&Statistics"))
        mnuStatistics.addAction(self.actStatistics)
        mnuStatistics.addAction(self.actElementData)
        mnuStatistics.addAction(self.actAnalysis)
        mnuStatistics.addAction(self.actSimulation)
        mnuStatistics.addAction(self.actReport)
        mnuRandomize = mnuTools.addMenu(tr("&Randomize"))
        mnuRandomize.addAction(self.actRandomizeDrill)
        mnuRandomize.addAction(self.actRandomizePending)
        mnuRandom = mnuTools.addMenu(tr("R&andom test"))
        mnuRandom.addAction(self.actRandomTest)
        mnuRandom.addSeparator()
        mnuRandom.addAction(self.actRandomAll)
        mnuRandom.addAction(self.actRandomPending)
        mnuRandom.addAction(self.actRandomMemorized)
        mnuRandom.addAction(self.actRandomDismissed)
        mnuRandom.addSeparator()
        mnuRandom.addAction(self.actRandomTopics)
        mnuRandom.addAction(self.actRandomItems)
        mnuRandom.addSeparator()
        mnuRandom.addAction(self.actRandomFilter)
        mnuRandom.addAction(self.actRandomLeeches)
        mnuRandom.addSeparator()
        mnuRandom.addAction(self.actRandomSubset)
        mnuRandom.addSeparator()
        mnuRandom.addAction(self.actRandomBranch)
        mnuTools.addSeparator()
        mnuTools.addAction(self.actOptions)

        # Window menu
        mnuWindow = self.menuBar().addMenu(tr("&Window"))
        mnuWindow.addAction(self.actDock)
        mnuToolbars = mnuWindow.addMenu(tr("&Toolbars"))
        mnuToolbars.addAction(self.actToolbarRead)
        mnuToolbars.addAction(self.actToolbarCompose)
        mnuToolbars.addAction(self.actToolbarFormat)
        mnuToolbars.addAction(self.actToolbarTime)
        mnuToolbars.addAction(self.actToolbarActions)
        mnuToolbars.addSeparator()
        mnuToolbars.addAction(self.actDockToolbars)
        mnuWindow.addAction(self.actStatusBar)
        mnuWindow.addAction(self.actBackground)
        mnuWindow.addAction(self.actHints)
        mnuSelect = mnuWindow.addMenu(tr("S&elect"))
        mnuSelect.addAction(self.actSelectCategory)
        mnuSelect.addAction(self.actSelectTasklist)
        mnuSelect.addAction(self.actSelectNextWindow)
        mnuLayout = mnuWindow.addMenu(tr("&Layout"))
        mnuLayout.addAction(self.actLayoutManager)
        mnuLayout.addSeparator()
        mnuLayout.addAction(self.actApplyDefaultLayout)
        mnuLayout.addAction(self.actClassLayout)
        mnuLayout.addSeparator()
        mnuLayout.addAction(self.actSaveCustomLayout)
        mnuLayout.addAction(self.actSaveAsDefault)
        mnuLayout.addSeparator()
        mnuLayout.addAction(self.actBackgroundColor)
        mnuWindow.addSeparator()
        mnuWindow.addAction(self.actLayoutLastUsed)
        mnuWindow.addAction(self.actLayoutContents)
        mnuWindow.addAction(self.actLayoutClassic)
        mnuWindow.addAction(self.actLayoutBrowser)


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
        tbFile.setVisible(False)

        # Other toolbar
        tbView = self.addToolBar(tr("View"))
        tbView.addAction(self.actLeeches)
        tbView.addAction(self.actSemiLeeches)
        tbView.addAction(self.actDrill)
        tbView.addAction(self.actRange)
        tbView.addAction(self.actHistory)
        tbView.addAction(self.actBranch)
        tbView.setVisible(False)



    def createStatusBar(self):
        self.statusBar().showMessage(tr("Ready."))




    def _refreshAppState(self):
        """Sets control active or inactive depending on the database state."""
        # active/inactive actions
        # FIXME why are they not disabled/enabled ?
        self.actAddCard.setEnabled(self._cardModel.isActive())
        self.actDeleteCard.setEnabled(self._cardModel.isActive())
        self.actPreviousCard.setEnabled(self._cardModel.isActive())
        self.actNextCard.setEnabled(self._cardModel.isActive())
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


    def _openRecentFile(self):
        if config.get_most_recent_file():
            self._openPackFile(config.get_most_recent_file())
        self._refreshAppState()


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


    def on_actFirstCard_triggered(self):
        pass

    def on_actPreviousCard_triggered(self):
        """Moves current selection up by 1 row. If no selection is made then
        selects last item."""
        # move row up
        currentIndex = self.cardModelIndex()
        prevIndex = self._cardModel.getPreviousIndex(currentIndex)
        self.setCardModelIndex(prevIndex)

    def on_actNextCard_triggered(self):
        """Moves current selection down by 1 row. If no selection is made then
        selects first item."""
        currentIndex = self.cardModelIndex()
        nextIndex = self.cardModel().getNextIndex(currentIndex)
        self.setCardModelIndex(nextIndex)

    def on_actLastCard_triggered(self):
        pass

    def on_actAddCard_triggered(self):
        self.cardModel().addNewCard()
        # TODO what if it's not added at the end?
        newIndex = self.cardModel().index(self.cardModel().rowCount() - 1, 0)
        # go to newly added record
        self.setCardModelIndex(newIndex)


    def on_actInsertCard_triggered(self):
        pass

    def on_actDeleteCard_triggered(self):
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
        # TODO must this have disabled if not database is open
        # TODO Option if want to clear existing or append
        fname = QFileDialog.getOpenFileName(self, \
            tr("Import Q&A file"), ".", tr("Q&A files (*.*)"))
        if fname:
            self.cardModel().importQAFile(str(fname))
            self.setCardModelIndex(self.cardModel().index(0, 0))
            self._refreshAppState()

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


    def on_actOptions_triggered(self):
        pass

    def on_actRecentFiles_triggered(self):
        self._openPackFile(self.sender().text())

    def on_actFinalDrill_triggered(self):
        dialog = DrillWindow(self)

        # FIXME
        # load cards from model
        # should it work that way?
        # should model be more general (and have other operations?) or be
        # dedicated to browsing list only ?
        # maybe all operations should be done on the database level
        # and models only for browsing lists
        cards = []
        for row in range(self.cardModel().rowCount()):
            idx = self.cardModel().index(row, 0)
            card = self.cardModel().data(idx, Qt.UserRole)
            cards.append(card)

        dialog.loadCards(cards)

        dialog.exec_()

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





def main():
    app = QApplication(sys.argv)
    # app.setStyle('cde')

    w = MainWindow()
    w.resize(700, 600)
    lazyshow(w)
    app.exec_()

if __name__ == "__main__":
    main()
