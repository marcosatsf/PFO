import polars as pl
import datetime
from polars import DataFrame
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QSize, QModelIndex

class FinanceModel(QtCore.QAbstractTableModel):

    def __init__(self, path: str):
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
        }

        self.schema = pl.Schema({
            'Data': pl.Date(),
            'Descrição': pl.String(),
            'Valor': pl.Float64(),
            'Saldo': pl.Float64(),
            'Categoria': pl.String()
            })

        df = pl.read_csv(path, separator=';', schema=self.schema, decimal_comma=True)
        df = df.with_columns(
            pl.col('Descrição')\
            .map_elements(lambda val: val.split(':')[0] , return_dtype=pl.String)\
            .alias('Categoria')
            )#.sort(self.column_name_maps['dia'], descending=True)
        self._data = df

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
            'Categoria': ['Manually added!']
        }
        df_dict_row = pl.DataFrame(data_to_be_added, schema=self.schema)
        self._data = pl.concat([self._data, df_dict_row], rechunk=True).sort('Data')
        self.recalculate_data()
        # self._data = self._data.with_columns(pl.col('Valor').cum_sum().alias('Saldo'))
        self.endInsertRows()
        self.layoutChanged.emit()
        return True


    def recalculate_data(self):
        """
        Recalculates the cumulative sum.
        """
        self._data = self._data.sort('Data')\
                .with_columns(pl.col('Valor').cum_sum().alias('Saldo'))

#------------------------ QUERIES TO BE ADDED
    def get_pix_data(self):
        return self._data\
            .group_by('Data', 'Categoria')\
            .agg(pl.col('Valor').sum())\
            .sort('Data').to_dict()
            # .filter(pl.col(self.column_name_maps['cat']).str.contains('Pix'))\
            #.dt.truncate('1mo')

    def get_total_amount_by_day(self):
        return self._data\
            .select(
                'Data',
                pl.col('Saldo').last().over('Data').alias('saldo final do dia')
                ).unique().sort('Data').to_dict()