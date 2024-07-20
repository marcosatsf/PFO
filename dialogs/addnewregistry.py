import sys
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import (QDialogButtonBox, QLabel, QDateEdit, QLineEdit, QButtonGroup, QGridLayout,
                             QDoubleSpinBox, QRadioButton, QDialog, QWidget, QVBoxLayout)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QSize

class AddNewRegistry(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add New Registry")

        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        insert_message = QLabel("Inserir novo registro:")
        self.layout.addWidget(insert_message)

        # Date
        self.date_input = QDateEdit()
        self.date_input.setDisplayFormat('dd/MM/yyyy')

        # Desc
        self.desc_input = QLineEdit()
        self.desc_input.setMaxLength(50)
        self.desc_input.setPlaceholderText("Descrição para o seu item")

        # Operacao
        radio_button_in = QRadioButton('Entrada')
        radio_button_in.setIcon(QtGui.QIcon('assets\icons\in.png'))
        radio_button_in.setChecked(True)
        radio_button_out = QRadioButton('Saída')
        radio_button_out.setIcon(QtGui.QIcon('assets\icons\out.png'))
        layout_radio_bttn = QVBoxLayout()
        layout_radio_bttn.addWidget(radio_button_in)
        layout_radio_bttn.addWidget(radio_button_out)
        self.op_input = QButtonGroup()
        self.op_input.addButton(radio_button_in)
        self.op_input.addButton(radio_button_out)

        op_input_widget = QWidget()
        op_input_widget.setLayout(layout_radio_bttn)

        # Valor
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setDecimals(2)
        self.amount_input.setMaximum(1e6)
        self.amount_input.setValue(0.00)

        self.layout.addWidget(
            self.add_into_layout(
                [QLabel("Dia:"), QLabel("Descrição:"), QLabel("Operação:"), QLabel("Valor:")],
                [self.date_input, self.desc_input, op_input_widget, self.amount_input]
            ))

        self.setFixedSize(600,400)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


    def add_into_layout(self, list_labels, list_inputs):
        layout = QGridLayout()
        for idx, tuple_widgets in enumerate(zip(list_labels, list_inputs)):
            layout.addWidget(tuple_widgets[0], idx, 0)
            layout.addWidget(tuple_widgets[1], idx, 1)
        final_widget = QWidget()
        final_widget.setLayout(layout)
        return final_widget


    def get_filled_data(self):
        return {
            'date':self.date_input.date().toPyDate(),
            'desc':self.desc_input.text(),
            'operation':self.op_input.checkedButton().text(),
            'amount':float(self.amount_input.text())
        }
