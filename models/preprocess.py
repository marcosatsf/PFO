# This script should exist in order to pre-process data
import re
import os
import polars as pl
import pandas as pd
import datetime
from typing import Union
from schema.finance import FinanceSchema
from schema.fatura import FaturaSchema


def pre_process_csv(path: str, separation_char:str=';') -> pl.DataFrame:
    """
    Pre-process CSV files

    Args:
        path (str): CSV Path do pre-process data;
        separation (str): Separation char to be used on CSV

    Returns:
        pl.DataFrame: DataFrame loaded.
    """
    #Read and try to handle data
    with open(path, 'r') as f:
        data = f.read()

    file_name_to_exclude = ''
    if 'Extrato Conta Corrente' in data:
        _, data = data.split('\n\n')
        file_name_to_exclude, separation_char = check_integrity_with_finance(data)
    try:
        df = pl.read_csv(path,
                    separator=separation_char,
                    schema=FinanceSchema(),
                    decimal_comma=True
                    )
    except pl.exceptions.ComputeError:
        try:
            df = load_csv_df(path,
                        separator=separation_char,
                        schema=FaturaSchema(),
                        decimal_comma=False)
            if 'Tipo' in  df.columns:
                df = df.drop('Tipo')\
                    .rename({'Lançamento':'Descrição'})\
                    .with_columns(pl.col('Valor').str.extract(r'([0-9]+,[0-9]+)', 1).str.replace(',', '.').cast(pl.Float64).mul(-1))\
                    .with_columns(Saldo=pl.lit(0.0).cast(pl.Float64))\
                    .select('Data', 'Descrição', 'Valor', 'Saldo', 'Categoria')
        except pl.exceptions.ComputeError:
            path, separation_char = check_integrity_with_finance(data)
            df = load_csv_df(path,
                        separator=separation_char,
                        schema=FaturaSchema(),
                        decimal_comma=True)

    if file_name_to_exclude:
        os.remove(file_name_to_exclude)
    return df


def check_integrity_with_finance(data: str) -> Union[str, str]:
    """
    Checks integrity of the file and tries to refactor and set columns according
    to the current FinanceSchema()

    Args:
        data (str): Data previouly loaded;

    Raises:
        Exception: Not enough columns to parse
        Exception: Important columns does not exist

    Returns:
        Union[str, str]: filename and separator char
    """

    exception_cols = {
        'Data': 'Deve conter dias no formato YYYY-MM-DD, e.g.: 2000-10-20',
        'Descrição': 'Deve conter uma descrição da transação',
        'Valor': 'Deve conter o valor da transação, com 2 casas decimais e sinal de negativo caso seja saída'
    }

    header, data = data.split('\n', maxsplit=1)
    # separation step
    sep_string = ',;'
    current_sep = ''
    for sep in sep_string:
        col_list = header.split(sep)
        if len(col_list) > 1:
            current_sep = sep
            break
    if not current_sep:
        raise Exception('CSV não parseado! Por favor utilize pelo menos "," como separação!')
    # Start to work on data!
    filename = handle_tmp_file(data)
    df = pd.read_csv(filename, sep=current_sep, try_parse_dates=True)
    for col_name, col_type in FinanceSchema().items():
        try:
            # Add needed columns!
            if col_name in df.columns:
                if col_name == 'Saldo':
                    df['Saldo'] = 0.0
                if col_name == 'Categoria':
                    if 'Histórico' in df.columns:
                        df['Categoria'] = df['Histórico']
                    else:
                        df['Categoria'] = df.apply(lambda x:x['Descrição'].split(':')[0], axis=1)
                continue
            # Check Data type and adapt it!
            if not df.columns[col_name].dtype.name == col_type.lower():
                if col_type == 'Date':
                    df.columns[col_name].astype('date64[pyarrow]')
                else:
                    df.columns[col_name].astype(col_type.lower())
        except KeyError:
            raise Exception(f'Não há coluna {col_name}'\
                            f', por favor verifique e adicione a coluna {col_name}'\
                            f'com a seguinte lógica: {exception_cols[col_name]}!')
    # reorder data
    df = df[FinanceSchema().keys()]
    df.to_csv(filename, sep=current_sep, index=False)
    return filename, current_sep


def handle_tmp_file(data: str) -> pl.DataFrame:
    """
    Handles "Extrato" pattern file.

    Args:
        data (str): Data in str form;

    Returns:
        pl.DataFrame: DataFrame loaded
    """

    file_name = f'csv_files/tmp_{datetime.datetime.now().strftime("%d%m%Y%H%M%S")}.csv'
    with open(file_name, 'w') as f:
        f.write(re.sub(r'(?<=[0-9])\.(?=[0-9]{3})', '', data))
    return file_name


def load_csv_df(path,
                separator = ',',
                schema:pl.Schema = None,
                decimal_comma:bool = False) -> pl.DataFrame:
    """
    Loads CSV based on some parameters.

    Args:
        path (str): Path to load the CSV file
        separator (str, optional): CSV separator character. Defaults to ','.
        schema (pl.Schema, optional): Data schema. Defaults to None.
        decimal_comma (bool, optional): Parse floats using a comma as
        the decimal separator instead of a period. Defaults to False.

    Returns:
        pl.DataFrame: DataFrame loaded
    """

    if schema:
        return pl.read_csv(path,
                    separator=separator,
                    schema=schema,
                    decimal_comma=decimal_comma
                    )
    else:
        return pl.read_csv(path,
                    separator=separator,
                    schema=FinanceSchema(),
                    decimal_comma=decimal_comma
                    )


