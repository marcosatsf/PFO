import sys
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import (QMainWindow, QApplication, QTableView, QPushButton, QDialogButtonBox,
                             QHeaderView, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QSize
import polars as pl
from polars import DataFrame
import plotly.graph_objects as go
from chart_lib.generate_chart import generate_test_data, create_plot_bar, create_scatterplot
from dialogs import AddNewRegistry
from models.finance import FinanceModel
# import qdarktheme
from qt_material import apply_stylesheet


extra = {

    # Button colors
    'danger': '#dc3545',
    'warning': '#ffc107',
    'success': '#17a2b8',
}

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PFO - Personal Finance Organizer")
        self.model = FinanceModel('extrato_clean.csv')

        # ------- Add 'Analises' TAB
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setDocumentMode(True)
        tabs.setMovable(False)

        # JUST TEST CHARTS!!!!
        self.browser = QWebEngineView(self)
        self.update_charts()
        self.model.layoutChanged.connect(self.update_charts)
        tabs.addTab(self.browser, 'Analises')

        # ------- Add 'Extrato' TAB
        vlayout = QVBoxLayout()
        self.table = QTableView()

        # self.table.setFixedWidth(800)
        # To resize table header given its contents
        # stretched_size = self.table.horizontalHeader().sectionSize(0)
        # print(stretched_size)
        # size = max(self.table.sizeHintForColumn(0), stretched_size)
        # print(size)
        # self.table.horizontalHeader().resizeSection(0, size+300)
        # TODO: Adjust the column size correctly!!!
        self.table.setModel(self.model)
        # print(self.model.data())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode(3))
        vlayout.addWidget(self.table)

        hlayout = QHBoxLayout()
        self.button_add = QPushButton('Add registry', self)
        self.button_add.clicked.connect(self.add)
        self.button_remove = QPushButton('Remove registry', self)
        self.button_remove.clicked.connect(self.remove)
        # self.table.selectionModel().selectionChanged.connect(self.remove)
        hlayout.addWidget(self.button_add)
        hlayout.addWidget(self.button_remove)
        vlayout.addLayout(hlayout)
        widget = QWidget()
        widget.setLayout(vlayout)
        tabs.addTab(widget, 'Extrato')

        # QMainWindow configs
        self.setFixedSize(QSize(1600, 900))
        self.setCentralWidget(tabs)


    def update_charts(self):
        value = self.model.get_pix_data()
        # print(value)
        fig = go.Figure()
        fig = create_plot_bar(fig, value['Data'], value['Valor'], value['Categoria'])

        value = self.model.get_total_amount_by_day()
        # print(value)
        fig = create_scatterplot(fig, value['Data'], value['saldo final do dia'])
        # fig = generate_test_data()
        self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))


    def add(self, s):
        print('click', s)
        dlg = AddNewRegistry()
        print(self.model.get_pix_data())
        if dlg.exec():
            self.model.add_registry(dlg.get_filled_data())

    def remove(self, indexes):
        for e in self.table.selectionModel().selectedRows():
            self.model.removeRow(e)
            print(e.row(), e.column())
        print(indexes)


app=QApplication(sys.argv)
# qdarktheme.setup_theme("auto")
window=MainWindow()
# setup stylesheet
apply_stylesheet(app, theme='dark_red.xml', extra=extra)
window.show()
app.exec()