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

Dictionary:
CHANGE ITEMS to CARDS
SNIPPETS and CARDS

"""

import release
__author__  = '%s <%s>' % \
              ( release.authors['afolmert'][0], release.authors['afolmert'][1])

__license__ = release.license
__version__ = release.version

# WARNING !
# <!--- Run pyrcc4 mentor.qrc to mentor_rc.py file -->

# TODO
# set mainwidget
# tabbar with widgets
# set status bar and toolbar
# set icons
# interface ala Designer -> lit on the left to select -> may be switched off
# the central will be tabbar current snippet
# at the bottom will be source
# on the right palettes
#
#
from PyQt4.QtCore import SIGNAL, SLOT
from PyQt4.QtGui import QWidget, QPushButton, QApplication, QMainWindow, \
     QKeySequence, QAction, QIcon, qApp
from miscqt import msgbox, lazyshow, tr
from misc import log
import sys
import mentor_rc



class MainWindow(QMainWindow):
    """My widget subclass."""

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)

        button = QPushButton("Press me!", self)
        self.connect(button, SIGNAL("clicked(bool)"), self.onClicked)

        self.setWindowTitle("Mentor" )

        button.move(40, 40)

        self.move(50, 50)

        self.setCentralWidget(button)

        self.createActions()
        self.createMenus()
        self.createToolbars()
        self.createStatusBar()

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


    def onClicked(self):
        msgbox("Hello world!")


    def on_actNew_triggered(self):
        msgbox("actNew was pressed!")
        pass


    def on_actAbout_triggered(self):
        log("this is actabout triggered " )
        msgbox(tr("MENTOR Version %s\nA learning tool\n\nDistributed under license: %s\n\nAuthors: \n%s" \
            % (__version__, __license__, str(__author__))))



def main():
    app = QApplication(sys.argv)

    w = MainWindow()
    w.resize(600, 400)
    lazyshow(w)
    app.exec_()

if __name__ == "__main__":
    main()








