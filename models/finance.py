import polars as pl
import datetime
from polars import DataFrame
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QSize, QModelIndex
from schema.finance import FinanceSchema
from preprocess_lib.csv import pre_process_csv


class FinanceModel(QtCore.QAbstractTableModel):
    def __init__(self, path: str, default_bank: str):
        """
        Initialize finance model.

        Args:
            path (str): path to a file, to load initial data.
        """
        super(FinanceModel, self).__init__()

        pl.Config(
            tbl_cell_numeric_alignment="RIGHT",
            thousands_separator=".",
            decimal_separator=",",
            float_precision=2
        )

        self.column_name_icons = {
            'Data': "📅",
            'Descrição': "📝",
            'Valor': "💲",
            'Saldo': "💲",
            'Categoria': "🚩",
            'Banco/Corretora': "🏦"
        }

        self.schema = FinanceSchema()
        self.separator_defined = ';'
        self._data = pre_process_csv(path, bank=default_bank)
        self.default_bank = default_bank


    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> str:
        """
        Retrieve data to View

        Args:
            index (QModelIndex): At which index
            role (Qt.ItemDataRole): Current active role

        Returns:
            str: value in str format
        """
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.item(row=index.row(), column=index.column())
            if isinstance(value, float):
                return f'{value:.2f}'
            else:
                return str(value)
        # if role == Qt.ItemDataRole.InitialSortOrderRole:
        #     value = self._data.sort(pl.col(index))
        #     return str(value)
        #     return QSize(len(str(self._data.item(row=index.row(), column=index.column()))), 20)

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        """
        Change model data

        Args:
            index (QModelIndex): At which index
            value (str): value to be set
            role (int, optional): Role used to set data. Defaults to Qt.ItemDataRole.EditRole.

        Returns:
            bool: True if it was successful, or False if not.
        """
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if not value:
                return False
            try:
                # In case of Float
                if self._data.dtypes[index.column()].is_float():
                    self._data[index.row(), index.column()] = float(value)
                # In case of Date
                elif str(self._data.dtypes[index.column()].base_type()) == 'Date':
                    self._data[index.row(), index.column()] = datetime.date.fromisoformat(value)
                # In case of String
                elif str(self._data.dtypes[index.column()].base_type()) == 'String':
                    self._data[index.row(), index.column()] = value
            except ValueError as e:
                print(e)
                return False
            # self._data[index.row(), index.column()] = value
            self.recalculate_data()
            self.layoutChanged.emit()
        return True


    def flags(self, index) -> Qt.ItemFlag:
        """
        Flags to be used by roles

        Args:
            index (QModelIndex): Selected item

        Returns:
            Qt.ItemFlag: flag set
        """
        if self._data.columns[index.column()] == 'Saldo':
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        else:
            return super().flags(index) | Qt.ItemFlag.ItemIsEditable


    def rowCount(self, index=QModelIndex()) -> int:
        """
        Gives the total count of rows

        Args:
            index (QModelIndex, optional): Not used. Defaults to QModelIndex().

        Returns:
            int: Total rows
        """
        return self._data.shape[0]


    def columnCount(self, index=QModelIndex()) -> int:
        """
        Gives the total count of columns

        Args:
            index (QModelIndex, optional): Not used. Defaults to QModelIndex().

        Returns:
            int: Total columns
        """
        return self._data.shape[1]


    def remove_registry(self, index=QModelIndex()) -> bool:
        """
        Removes a registry from the data

        Args:
            index (QModelIndex, optional): Row index to be removed. Defaults to QModelIndex().

        Returns:
            bool: True when success
        """
        self.beginRemoveRows(QModelIndex(), self.rowCount(), self.rowCount()-1)
        self._data = self._data.with_row_index()\
                        .filter(pl.col('index') != index.row())\
                        .drop('index')
        self.recalculate_data()
        self.endRemoveRows()
        self.layoutChanged.emit()
        return True

    def headerData(self, section, orientation, role) -> str:
        """
        Retrieves header information (vertically or horizontally)

        Args:
            section (int): Which section
            orientation (Qt.Orientation): Horizonally or Vertically
            role (Qt.ItemDataRole): Role to access data

        Returns:
            str: header value
        """
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(f"{self.column_name_icons[self._data.columns[section]]} {self._data.columns[section]}")

            if orientation == Qt.Orientation.Vertical:
                return str(section)

    def add_registry(self, dict_row) -> bool:
        """
        Adds a registry to the data

        Args:
            dict_row (dict): A dictionary filled with:
                date, description, operation and amount

        Returns:
            bool: True when success
        """
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        print(dict_row)
        data_to_be_added = {
            'Data': [dict_row['date']],
            'Descrição': [dict_row['desc']],
            'Valor': [dict_row['amount']] if dict_row['operation'] == 'Entrada' else [-dict_row['amount']],
            'Saldo': [0.0],
            'Categoria': ['Manually added!'],
            'Banco/Corretora': self.default_bank
        }
        df_dict_row = pl.DataFrame(data_to_be_added, schema=self.schema)
        self._data = pl.concat([self._data, df_dict_row], rechunk=True)
        self.recalculate_data()
        # self._data = self._data.with_columns(pl.col('Valor').cum_sum().alias('Saldo'))
        self.endInsertRows()
        self.layoutChanged.emit()
        return True


    def add_rows(self, new_df) -> bool:
        """
        Adds a registry to the data

        Args:
            dict_row (dict): A dictionary filled with:
                date, description, operation and amount

        Returns:
            bool: True when success
        """
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount()+new_df.shape[0]-1)
        self._data = pl.concat([self._data, new_df], rechunk=True)
        self.recalculate_data()
        # self._data = self._data.with_columns(pl.col('Valor').cum_sum().alias('Saldo'))
        self.endInsertRows()
        self.layoutChanged.emit()
        return True


    def recalculate_data(self):
        """
        Recalculates the cumulative sum.
        """
        self._data = self._data.sort(*self._data.columns)\
                .with_columns(pl.col('Valor').cum_sum().alias('Saldo'))


    def save_to_file(self, file) -> bool:
        self._data.write_csv(file, separator=self.separator_defined,float_precision=2)
        return True

#------------------------ QUERIES TO BE ADDED
    def get_transactions_by(self, refresh_schedule: str):
        match refresh_schedule:
            case 'weekly':
                trunc_str = '1w'
            case 'monthly':
                trunc_str = '1mo'
            case 'quarterly':
                trunc_str = '1q'
            case 'yearly':
                trunc_str = '1y'
            case 'daily' | _:
                trunc_str = '1d'
        return self._data\
            .group_by(pl.col('Data').dt.truncate(trunc_str), 'Descrição', 'Categoria')\
            .agg(pl.col('Valor').sum())\
            .sort('Data')\
            .to_dict()
            # .filter(pl.col(self.column_name_maps['cat']).str.contains('Pix'))\
            #.dt.truncate('1mo')


    def get_top_significant_expenses_by_category(self):
        return self._data\
            .group_by('Categoria')\
            .agg(pl.col('Valor').abs().sum())\
            .sort(by=pl.col('Valor'),descending=True)\
            .select('Categoria', 'Valor')\
            .to_dict(as_series=False)


    def get_distribution_by_bank(self):
        # return self._data\
        #     .group_by('Banco/Corretora')\
        #     .agg(pl.col('Valor').abs().sum())\
        #     .sort(by=pl.col('Valor'),descending=True)\
        #     .select('Banco/Corretora', 'Valor')\
        #     .to_dict(as_series=False)
        invest = self._data.filter(Categoria='Aplicacao')\
                            .select('Banco/Corretora', 'Valor')\
                            .group_by('Banco/Corretora')\
                            .sum()\
                            .select('Banco/Corretora', pl.col('Valor').abs())
        current = self._data.group_by('Banco/Corretora')\
                            .agg(pl.col('Saldo').last())\
                            .select('Banco/Corretora', pl.col('Saldo').abs().alias('Valor'))
        return pl.concat([current, invest], how='vertical')\
            .group_by('Banco/Corretora').sum()\
            .sort(by=pl.col('Valor'),descending=True)\
            .to_dict(as_series=False)


    def get_total_amount_by(self, refresh_schedule: str ):
        match refresh_schedule:
            case 'weekly':
                trunc_str = '1w'
            case 'monthly':
                trunc_str = '1mo'
            case 'quarterly':
                trunc_str = '1q'
            case 'yearly':
                trunc_str = '1y'
            case 'daily' | _:
                trunc_str = '1d'
        return self._data\
            .select(
                pl.col('Data').dt.truncate(trunc_str),
                pl.col('Saldo').last().over(pl.col('Data').dt.truncate(trunc_str)).alias('Saldo período')
                ).sort('Data').to_dict()

    # def get_current_amount(self):
    #     return self._data.select('Data', 'Saldo').to_dict()