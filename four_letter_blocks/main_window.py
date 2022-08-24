# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.3.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMenu,
    QMenuBar, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QStatusBar, QTabWidget, QVBoxLayout,
    QWidget)

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
        self.options_action = QAction(MainWindow)
        self.options_action.setObjectName(u"options_action")
        self.export_set_action = QAction(MainWindow)
        self.export_set_action.setObjectName(u"export_set_action")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.main_tabs = QTabWidget(self.centralwidget)
        self.main_tabs.setObjectName(u"main_tabs")
        self.single_tab = QWidget()
        self.single_tab.setObjectName(u"single_tab")
        self.verticalLayout_2 = QVBoxLayout(self.single_tab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.title_label = QLabel(self.single_tab)
        self.title_label.setObjectName(u"title_label")

        self.verticalLayout_2.addWidget(self.title_label)

        self.title_text = QLineEdit(self.single_tab)
        self.title_text.setObjectName(u"title_text")

        self.verticalLayout_2.addWidget(self.title_text)

        self.grid_label = QLabel(self.single_tab)
        self.grid_label.setObjectName(u"grid_label")

        self.verticalLayout_2.addWidget(self.grid_label)

        self.grid_text = FocusedPlainTextEdit(self.single_tab)
        self.grid_text.setObjectName(u"grid_text")
        self.grid_text.setTabChangesFocus(True)

        self.verticalLayout_2.addWidget(self.grid_text)

        self.clues_label = QLabel(self.single_tab)
        self.clues_label.setObjectName(u"clues_label")

        self.verticalLayout_2.addWidget(self.clues_label)

        self.clues_text = QPlainTextEdit(self.single_tab)
        self.clues_text.setObjectName(u"clues_text")
        self.clues_text.setTabChangesFocus(True)

        self.verticalLayout_2.addWidget(self.clues_text)

        self.blocks_label = QLabel(self.single_tab)
        self.blocks_label.setObjectName(u"blocks_label")

        self.verticalLayout_2.addWidget(self.blocks_label)

        self.blocks_text = FocusedPlainTextEdit(self.single_tab)
        self.blocks_text.setObjectName(u"blocks_text")
        self.blocks_text.setTabChangesFocus(True)

        self.verticalLayout_2.addWidget(self.blocks_text)

        self.warnings_label = QLabel(self.single_tab)
        self.warnings_label.setObjectName(u"warnings_label")

        self.verticalLayout_2.addWidget(self.warnings_label)

        self.main_tabs.addTab(self.single_tab, "")
        self.set_tab = QWidget()
        self.set_tab.setObjectName(u"set_tab")
        self.gridLayout = QGridLayout(self.set_tab)
        self.gridLayout.setObjectName(u"gridLayout")
        self.crossword_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.crossword_spacer, 2, 0, 1, 1)

        self.crossword_files = QListWidget(self.set_tab)
        self.crossword_files.setObjectName(u"crossword_files")

        self.gridLayout.addWidget(self.crossword_files, 1, 0, 1, 3)

        self.remove_button = QPushButton(self.set_tab)
        self.remove_button.setObjectName(u"remove_button")

        self.gridLayout.addWidget(self.remove_button, 2, 2, 1, 1)

        self.add_button = QPushButton(self.set_tab)
        self.add_button.setObjectName(u"add_button")

        self.gridLayout.addWidget(self.add_button, 2, 1, 1, 1)

        self.crossword_label = QLabel(self.set_tab)
        self.crossword_label.setObjectName(u"crossword_label")

        self.gridLayout.addWidget(self.crossword_label, 0, 0, 1, 3)

        self.main_tabs.addTab(self.set_tab, "")

        self.verticalLayout.addWidget(self.main_tabs)

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
        self.tools_menu = QMenu(self.menubar)
        self.tools_menu.setObjectName(u"tools_menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        QWidget.setTabOrder(self.main_tabs, self.title_text)
        QWidget.setTabOrder(self.title_text, self.grid_text)
        QWidget.setTabOrder(self.grid_text, self.clues_text)
        QWidget.setTabOrder(self.clues_text, self.blocks_text)
        QWidget.setTabOrder(self.blocks_text, self.crossword_files)
        QWidget.setTabOrder(self.crossword_files, self.add_button)
        QWidget.setTabOrder(self.add_button, self.remove_button)

        self.menubar.addAction(self.file_menu.menuAction())
        self.menubar.addAction(self.edit_menu.menuAction())
        self.menubar.addAction(self.tools_menu.menuAction())
        self.menubar.addAction(self.help_menu.menuAction())
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.export_action)
        self.file_menu.addAction(self.export_set_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        self.help_menu.addAction(self.about_action)
        self.edit_menu.addAction(self.shuffle_action)
        self.tools_menu.addAction(self.options_action)

        self.retranslateUi(MainWindow)

        self.main_tabs.setCurrentIndex(0)


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
        self.export_action.setText(QCoreApplication.translate("MainWindow", u"&Export Single...", None))
#if QT_CONFIG(shortcut)
        self.export_action.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+X", None))
#endif // QT_CONFIG(shortcut)
        self.exit_action.setText(QCoreApplication.translate("MainWindow", u"E&xit", None))
        self.shuffle_action.setText(QCoreApplication.translate("MainWindow", u"&Shuffle", None))
#if QT_CONFIG(shortcut)
        self.shuffle_action.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+F", None))
#endif // QT_CONFIG(shortcut)
        self.options_action.setText(QCoreApplication.translate("MainWindow", u"&Options...", None))
        self.export_set_action.setText(QCoreApplication.translate("MainWindow", u"Export Se&t...", None))
#if QT_CONFIG(shortcut)
        self.export_set_action.setShortcut(QCoreApplication.translate("MainWindow", u"Alt+X", None))
#endif // QT_CONFIG(shortcut)
        self.title_label.setText(QCoreApplication.translate("MainWindow", u"Title", None))
        self.grid_label.setText(QCoreApplication.translate("MainWindow", u"Grid", None))
        self.grid_text.setPlainText("")
        self.clues_label.setText(QCoreApplication.translate("MainWindow", u"Clues", None))
        self.blocks_label.setText(QCoreApplication.translate("MainWindow", u"Blocks", None))
        self.warnings_label.setText(QCoreApplication.translate("MainWindow", u"Warnings", None))
        self.main_tabs.setTabText(self.main_tabs.indexOf(self.single_tab), QCoreApplication.translate("MainWindow", u"Single", None))
        self.remove_button.setText(QCoreApplication.translate("MainWindow", u"Remove", None))
        self.add_button.setText(QCoreApplication.translate("MainWindow", u"Add...", None))
        self.crossword_label.setText(QCoreApplication.translate("MainWindow", u"Crossword Files", None))
        self.main_tabs.setTabText(self.main_tabs.indexOf(self.set_tab), QCoreApplication.translate("MainWindow", u"Set", None))
        self.file_menu.setTitle(QCoreApplication.translate("MainWindow", u"&File", None))
        self.help_menu.setTitle(QCoreApplication.translate("MainWindow", u"&Help", None))
        self.edit_menu.setTitle(QCoreApplication.translate("MainWindow", u"&Edit", None))
        self.tools_menu.setTitle(QCoreApplication.translate("MainWindow", u"&Tools", None))
    # retranslateUi

