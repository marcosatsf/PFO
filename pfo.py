import os
import sys
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QMainWindow, QApplication, QTableView,
                             QPushButton, QFileDialog, QHeaderView, QTabWidget,
                             QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
                             QSizePolicy, QLabel)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QSize
import polars as pl
import plotly.graph_objects as go
from chart_lib.functions import p_obj
from chart_lib.generate_chart import ChartBuilder
import datetime
from dialogs.addnewregistry import AddNewRegistry
from dotenv import load_dotenv
from models.finance import FinanceModel
from models.preprocess import pre_process_csv
from qt_material import apply_stylesheet

load_dotenv()
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
        self.load_set_envs()
        self.model = FinanceModel(self.initial_load_filename)

        menu = self.menuBar()
        file_menu = menu.addMenu("Arquivo")

        # Save menu
        save_file = QAction(QIcon("assets\icons\in.png"), "Salvar dados", self)
        save_file.triggered.connect(self.save_file)
        save_file.setCheckable(True)
        # Carregar menu
        load_file = QAction(QIcon("assets\icons\in.png"), "Carregar+ arquivo", self)
        load_file.triggered.connect(self.loadplus_file)
        load_file.setCheckable(True)
        # Restaurar menu
        restore_file = QAction(QIcon("assets\icons\in.png"), "Restaurar dados", self)
        restore_file.triggered.connect(self.restore_file)
        restore_file.setCheckable(True)

        file_menu.addAction(save_file)
        file_menu.addAction(load_file)
        file_menu.addAction(restore_file)

        self.current_refresh = 'daily'
        # ------- Add 'Analises' TAB
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setDocumentMode(True)
        tabs.setMovable(False)

        hlayout_analysis = QHBoxLayout()
        #--------------------------
        #menu|---------chart-------
        #--------------------------
        # Menu
        # self.chart_opt = QLabel('Wow')
        menu_vlayout = QVBoxLayout()
        self.chart_menu = QWidget()
        # self.chart_opt.setTabPosition(QTabWidget.TabPosition.West)
        qsize_chartopt = QSizePolicy()
        qsize_chartopt.setHorizontalStretch(1)
        self.chart_menu.setSizePolicy(qsize_chartopt)

        # Daily group
        daily_b = QPushButton(QIcon("assets\icons\in.png"), "Daily", self)
        daily_b.setEnabled(True)

        # Carregar menu
        weekly_b = QPushButton(QIcon("assets\icons\out.png"), "Weekly", self)
        weekly_b.setEnabled(True)

        menu_vlayout.addWidget(daily_b)
        menu_vlayout.addWidget(weekly_b)
        self.chart_menu.setLayout(menu_vlayout)
        hlayout_analysis.addWidget(self.chart_menu)

        # Chart
        self.browser = QWebEngineView(self)
        # qsize_browser = QSizePolicy()
        # qsize_browser.setHorizontalStretch(4)
        # self.browser.setSizePolicy(qsize_browser)
        hlayout_analysis.addWidget(self.browser)

        self.chart_model = ChartBuilder(
            grid=(3,4),
            refresh=self.current_refresh
        )
        self.browser.setHtml(self.chart_model.get_figure().to_html(include_plotlyjs='cdn'))
        self.update_charts()
        self.model.layoutChanged.connect(self.update_charts)

        analysis = QWidget()
        analysis.setLayout(hlayout_analysis)
        tabs.addTab(analysis, 'Analises')

        # ------- Add 'Extrato' TAB
        vlayout = QVBoxLayout()
        #--------------------------
        #----------table-----------
        #--add-------|-----remove--
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
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode(3))
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
        statement = QWidget()
        statement.setLayout(vlayout)
        tabs.addTab(statement, 'Extrato')

        daily_b.clicked.connect(self.update_refresh('daily'))
        weekly_b.clicked.connect(self.update_refresh('weekly'))
        # QMainWindow configs
        self.setFixedSize(QSize(1600, 900))
        self.setCentralWidget(tabs)


    def load_set_envs(self):
        self.initial_load_filename = os.getenv('INITIAL_LOAD_PATH')
        print(self.initial_load_filename)
        if not self.initial_load_filename:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Tem algo errado 😅 !")
            dlg.setText("Por favor, selecione um arquivo a ser carregado inicialmente!")
            dlg.exec()
            self.initial_load_filename, _ = QFileDialog.getOpenFileName(self, 'Open first CSV', '', filter='Arquivos CSV (*.csv)')
            self.set_initial_path_env(self.initial_load_filename)


    def update_refresh(self, refresh):
        def set_refresh():
            self.current_refresh = refresh
            self.update_charts()
        return set_refresh


    def set_initial_path_env(self, path):
        with open('.env', 'w') as f:
                f.write(f'INITIAL_LOAD_PATH="{path}"')


    def save_file(self):
        filename = f'csv_files/checkpoint_{datetime.datetime.now().strftime("%d%m%Y%H%M%S")}.csv'
        self.model.save_to_file(filename)
        self.set_initial_path_env(filename)



    def loadplus_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open CSV', '', filter='Arquivos CSV (*.csv)')
        if filename:
            self.model.add_rows(pre_process_csv(filename))
            print(self.model._data)


    def restore_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open CSV', '', filter='Arquivos CSV (*.csv)')
        if filename:
            self.model = FinanceModel(filename)
            print(self.model._data)


    def update_charts(self):
        bar_values = self.model.get_transactions_by(refresh_schedule=self.current_refresh)
        rank_values = self.model.get_top_significant_expenses_by_category()
        scatter_values = self.model.get_total_amount_by(refresh_schedule=self.current_refresh)
        # p_obj(bar_values)
        # p_obj(rank_values)
        # p_obj(scatter_values)
        self.chart_model.refresh_plots(
            bar_values=bar_values,
            rank_values=rank_values,
            scatter_values=scatter_values
        )
        self.browser.setHtml(self.chart_model.get_figure().to_html(include_plotlyjs='cdn'))


    def add(self, s):
        dlg = AddNewRegistry()
        print(self.model.get_transactions_by(refresh_schedule=self.current_refresh))
        if dlg.exec():
            self.model.add_registry(dlg.get_filled_data())

    def remove(self):
        for qitem in self.table.selectionModel().selectedRows():
            self.model.remove_registry(qitem)


app=QApplication(sys.argv)
window=MainWindow()
# setup stylesheet
apply_stylesheet(app, theme='dark_red.xml', extra=extra)
window.show()
app.exec()