# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

from four_letter_blocks.focused_plain_text_edit import FocusedPlainTextEdit


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.new_action = QAction(MainWindow)
        self.new_action.setObjectName(u"new_action")
        self.open_action = QAction(MainWindow)
        self.open_action.setObjectName(u"open_action")
        self.save_action = QAction(MainWindow)
        self.save_action.setObjectName(u"save_action")
        self.save_as_action = QAction(MainWindow)
        self.save_as_action.setObjectName(u"save_as_action")
        self.about_action = QAction(MainWindow)
        self.about_action.setObjectName(u"about_action")
        self.export_action = QAction(MainWindow)
        self.export_action.setObjectName(u"export_action")
        self.exit_action = QAction(MainWindow)
        self.exit_action.setObjectName(u"exit_action")
        self.shuffle_action = QAction(MainWindow)
        self.shuffle_action.setObjectName(u"shuffle_action")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.title_label = QLabel(self.centralwidget)
        self.title_label.setObjectName(u"title_label")

        self.verticalLayout.addWidget(self.title_label)

        self.title_text = QLineEdit(self.centralwidget)
        self.title_text.setObjectName(u"title_text")

        self.verticalLayout.addWidget(self.title_text)

        self.grid_label = QLabel(self.centralwidget)
        self.grid_label.setObjectName(u"grid_label")

        self.verticalLayout.addWidget(self.grid_label)

        self.grid_text = FocusedPlainTextEdit(self.centralwidget)
        self.grid_text.setObjectName(u"grid_text")
        self.grid_text.setTabChangesFocus(True)

        self.verticalLayout.addWidget(self.grid_text)

        self.clues_label = QLabel(self.centralwidget)
        self.clues_label.setObjectName(u"clues_label")

        self.verticalLayout.addWidget(self.clues_label)

        self.clues_text = QPlainTextEdit(self.centralwidget)
        self.clues_text.setObjectName(u"clues_text")
        self.clues_text.setTabChangesFocus(True)

        self.verticalLayout.addWidget(self.clues_text)

        self.blocks_label = QLabel(self.centralwidget)
        self.blocks_label.setObjectName(u"blocks_label")

        self.verticalLayout.addWidget(self.blocks_label)

        self.blocks_text = FocusedPlainTextEdit(self.centralwidget)
        self.blocks_text.setObjectName(u"blocks_text")
        self.blocks_text.setTabChangesFocus(True)

        self.verticalLayout.addWidget(self.blocks_text)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        self.file_menu = QMenu(self.menubar)
        self.file_menu.setObjectName(u"file_menu")
        self.help_menu = QMenu(self.menubar)
        self.help_menu.setObjectName(u"help_menu")
        self.edit_menu = QMenu(self.menubar)
        self.edit_menu.setObjectName(u"edit_menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.file_menu.menuAction())
        self.menubar.addAction(self.edit_menu.menuAction())
        self.menubar.addAction(self.help_menu.menuAction())
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.export_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        self.help_menu.addAction(self.about_action)
        self.edit_menu.addAction(self.shuffle_action)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Four-Letter Blocks", None))
        self.new_action.setText(QCoreApplication.translate("MainWindow", u"&New", None))
#if QT_CONFIG(statustip)
        self.new_action.setStatusTip(QCoreApplication.translate("MainWindow", u"Start a new puzzle", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(shortcut)
        self.new_action.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
        self.open_action.setText(QCoreApplication.translate("MainWindow", u"&Open...", None))
#if QT_CONFIG(statustip)
        self.open_action.setStatusTip(QCoreApplication.translate("MainWindow", u"Open a puzzle from a text file", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(shortcut)
        self.open_action.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.save_action.setText(QCoreApplication.translate("MainWindow", u"&Save...", None))
#if QT_CONFIG(statustip)
        self.save_action.setStatusTip(QCoreApplication.translate("MainWindow", u"Save the puzzle to a text file", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(shortcut)
        self.save_action.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.save_as_action.setText(QCoreApplication.translate("MainWindow", u"Save &As...", None))
#if QT_CONFIG(statustip)
        self.save_as_action.setStatusTip(QCoreApplication.translate("MainWindow", u"Save the puzzle to a new text file", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(shortcut)
        self.save_as_action.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Shift+S", None))
#endif // QT_CONFIG(shortcut)
        self.about_action.setText(QCoreApplication.translate("MainWindow", u"&About...", None))
        self.export_action.setText(QCoreApplication.translate("MainWindow", u"&Export...", None))
#if QT_CONFIG(shortcut)
        self.export_action.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+X", None))
#endif // QT_CONFIG(shortcut)
        self.exit_action.setText(QCoreApplication.translate("MainWindow", u"E&xit", None))
        self.shuffle_action.setText(QCoreApplication.translate("MainWindow", u"&Shuffle", None))
#if QT_CONFIG(shortcut)
        self.shuffle_action.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+F", None))
#endif // QT_CONFIG(shortcut)
        self.title_label.setText(QCoreApplication.translate("MainWindow", u"Title", None))
        self.grid_label.setText(QCoreApplication.translate("MainWindow", u"Grid", None))
        self.grid_text.setPlainText("")
        self.clues_label.setText(QCoreApplication.translate("MainWindow", u"Clues", None))
        self.blocks_label.setText(QCoreApplication.translate("MainWindow", u"Blocks", None))
        self.file_menu.setTitle(QCoreApplication.translate("MainWindow", u"&File", None))
        self.help_menu.setTitle(QCoreApplication.translate("MainWindow", u"&Help", None))
        self.edit_menu.setTitle(QCoreApplication.translate("MainWindow", u"&Edit", None))
    # retranslateUi

