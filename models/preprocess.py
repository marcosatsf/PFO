# This script should exist in order to pre-process data
import re
import os
import polars as pl
import datetime
from schema.finance import FinanceSchema
from schema.fatura import FaturaSchema


def pre_process_csv(path: str) -> pl.DataFrame:
    """
    Pre-process CSV files

    Args:
        path (str): CSV Path do pre-process data

    Returns:
        pl.DataFrame: DataFrame loaded.
    """
    #Read and try to manage data
    with open(path, 'r') as f:
        data = f.read()
    # Needs to be pre-processed by "extrato" model
    header_info = data.split('\n')[0]
    file_name_to_exclude = ''
    if 'Extrato Conta Corrente' in data:
        file_name_to_exclude = handle_extrato_full(data)
        path = file_name_to_exclude
    if ';' in header_info:
        if 'checkpoint' in path:
            return load_csv_df(path,
                        separator=';',
                        schema=pl.Schema({
                            "Data": pl.Date(),
                            "Descrição": pl.String(),
                            "Valor": pl.Float64(),
                            "Saldo": pl.Float64(),
                            "Categoria": pl.String()
                            }),
                        decimal_comma=True)
        elif 'Histórico' in header_info:
            df = load_csv_df(path,
                        separator=';',
                        schema=pl.Schema({
                            "Data": pl.Date(),
                            "Histórico": pl.String(),
                            "Descrição": pl.String(),
                            "Valor": pl.Float64()
                            }),
                        decimal_comma=True)
            print(df)
            return df.rename({'Histórico':'Categoria'})\
                    .with_columns(Saldo=pl.lit(0.0).cast(pl.Float64))\
                    .select('Data', 'Descrição', 'Valor', 'Saldo', 'Categoria')
        else:
            df = load_csv_df(path,
                        separator=';',
                        schema=pl.Schema({
                            "Data": pl.Date(),
                            "Descrição": pl.String(),
                            "Valor": pl.Float64(),
                            "Saldo": pl.Float64()
                            }),
                        decimal_comma=True)
            # Removes unused temporary file
            if file_name_to_exclude:
                os.remove(file_name_to_exclude)
            # Returns data with some transformations
            return df.with_columns(
                    pl.col('Descrição')\
                    .map_elements(lambda val: val.split(':')[0] , return_dtype=pl.String)\
                    .alias('Categoria')
                    ).rename({'Data Lançamento':'Data'})
    if ',' in header_info:
        df = load_csv_df(path,
                     separator=',',
                     schema=FaturaSchema(),
                    decimal_comma=False)
        # Returns data with some transformations
        return df.drop('Tipo')\
                .rename({'Lançamento':'Descrição'})\
                .with_columns(pl.col('Valor').str.extract(r'([0-9]+,[0-9]+)', 1).str.replace(',', '.').cast(pl.Float64).mul(-1))\
                .with_columns(Saldo=pl.lit(0.0).cast(pl.Float64))\
                .select('Data', 'Descrição', 'Valor', 'Saldo', 'Categoria')
    else:
        # Just load trying to attach one schema
        return load_csv_df(path)


def handle_extrato_full(data: str) -> pl.DataFrame:
    """
    Handles "Extrato" pattern file.

    Args:
        data (str): Data in str form;

    Returns:
        pl.DataFrame: DataFrame loaded
    """
    _, bank_statement = data.split('\n\n')
    if 'Data Lançamento' == bank_statement.split(';', maxsplit=1)[0]:
        bank_statement = bank_statement.replace('Data Lançamento', 'Data')
    file_name = f'tmp_{datetime.datetime.now().strftime("%d%m%Y%H%M%S")}.csv'
    with open(file_name, 'w') as f:
        f.write(re.sub(r'(?<=[0-9])\.(?=[0-9])', '', bank_statement))
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


