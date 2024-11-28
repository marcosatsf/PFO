# This script should exist in order to pre-process data
import re
import os
import polars as pl
import pandas as pd
import datetime
from typing import Union
from schema.finance import FinanceSchema
from preprocess_lib.transformations_map import ColumnMap


def pre_process_csv(path: str, separation_char:str=';', bank:str='') -> pl.DataFrame:
    """
    Pre-process CSV files

    Args:
        path (str): CSV Path do pre-process data;
        separation (str): Separation char to be used on CSV;
        bank (str): Bank name

    Returns:
        pl.DataFrame: DataFrame loaded.
    """
    #Read and try to handle data
    with open(path, 'r',encoding='utf-8') as f:
        data = f.read()

    file_name_to_exclude = ''
    # Remove unused info.
    if 'Extrato Conta Corrente' in data:
        _, data = data.split('\n\n')
        file_name_to_exclude, separation_char = check_integrity_with_finance(data, bank)
    # Try to load with various formats
    try:
        df = pl.read_csv(path,
                    separator=separation_char,
                    schema=FinanceSchema(),
                    decimal_comma=False
                    )
    except pl.exceptions.ComputeError:
        try:
            df = load_csv_df(path,
                        separator=separation_char,
                        schema=FinanceSchema(),
                        decimal_comma=False)
            if 'Tipo' in  df.columns:
                df = df.drop('Tipo')\
                    .rename({'Lançamento':'Descrição'})\
                    .with_columns(pl.col('Valor').str.extract(r'([0-9]+,[0-9]+)', 1).str.replace(',', '.').cast(pl.Float64).mul(-1))\
                    .with_columns(Saldo=pl.lit(0.0).cast(pl.Float64))\
                    .select('Data', 'Descrição', 'Valor', 'Saldo', 'Categoria')
        except pl.exceptions.ComputeError:
            # Path when we are uploading an invoice!
            path, separation_char = check_integrity_with_finance(data, bank, data_type='invoice')
            df = load_csv_df(path,
                        separator=separation_char,
                        schema=FinanceSchema(),
                        decimal_comma=False)
            file_name_to_exclude = path
    # Delete temporary file, if needed
    if file_name_to_exclude:
        os.remove(file_name_to_exclude)
    # Filter out data which is not important right now!
    df = df.with_columns(pl.col('Banco/Corretora').fill_null(bank))
    # Deal with some especial cases
    return df_transformations(df)


def df_transformations(df:pl.DataFrame) -> pl.DataFrame:
    """
    Transformed dataframe based on utility.
    1. Remove credit card invoice;
    2. Map "Pagamento" to correct description;

    Args:
        df (pl.DataFrame): Dataframe to be filtered/transformed

    Returns:
        pl.DataFrame: Dataframe filtered/transformed
    """
    def cascade_when_then_structure(df:pl.DataFrame, map_column: list[dict], column_name:str):
        for map_dict in map_column:
            df = df.with_columns(
                    pl.when(map_dict['predicate'])
                    .then(map_dict['result'])
                    .otherwise(pl.col(column_name))
                    .alias(column_name)
                )
        return df

    # Step 1 - according to docstring
    df = df.filter(~pl.col('Descrição').str.contains_any(
        [
        'Pagamento efetuado: "Debito Automatico Fatura Cartao Inter"',
        'Pagamento efetuado: "Pagamento fatura cartao Inter"',
        'Pagamento Online De Fatura',
        'Pagto Debito Automat'
        ]))
    # Step 2 - according to docstring
    list_columns_2_transform = ['Descrição', 'Categoria']
    for column_name in list_columns_2_transform:
        cm = ColumnMap(curr_col=column_name)
        df = cascade_when_then_structure(
            df = df,
            map_column = cm.get_column_mappings(),
            column_name = column_name
        )
    # Return dataframe
    return df


def check_integrity_with_finance(data: str, bank: str, data_type: str = '') -> Union[str, str]:
    """
    Checks integrity of the file and tries to refactor and set columns according
    to the current FinanceSchema()

    Args:
        data (str): Data previouly loaded;
        bank (str): Bank name to be added;
        date_type (str, optional): type of data being loaded. Defaults to empty string.

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
    header = header.replace("Data Lançamento", "Data")
    data = f'{header}\n{data}'
    print(data)
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
    df = pd.read_csv(filename, sep=current_sep, parse_dates=True, date_format='%Y-%m-%d', encoding='utf-8')
    for col_name, col_type in FinanceSchema().items():
        col_type = str(col_type)
        try:
            # Add needed columns!
            if not col_name in df.columns:
                if col_name == 'Saldo':
                    df['Saldo'] = 0.0
                elif col_name == 'Categoria':
                    if 'Histórico' in df.columns:
                        df['Categoria'] = df['Histórico']
                    else:
                        df['Categoria'] = df.apply(lambda x:x['Descrição'].split(':')[0], axis=1)
                elif col_name == 'Banco/Corretora':
                    df['Banco/Corretora'] = bank
                continue
            # Transform any incorrect type under "Valor"
            if col_name == 'Valor':
                df[col_name] = df.apply(lambda x:re.sub(r'[^0-9-.]*', '', x[col_name].replace(',', '.')), axis=1)
            # Check Data type and adapt it!
            print('PRINTING DEBUG!!!', col_name, df[col_name].dtype.name, col_type.lower())
            if not df[col_name].dtype.name == col_type.lower():
                if col_type == 'Date':
                    df[col_name] = pd.to_datetime(arg=df[col_name], yearfirst=True, format='%Y-%m-%d')
                else:
                    df[col_name] = df[col_name].astype(col_type.lower())
                    if col_name == 'Valor' and data_type == 'invoice':
                        df[col_name] = df[col_name] * -1
        except KeyError:
            print(df)
            raise Exception(f'Não há coluna {col_name}'\
                            f', por favor verifique e adicione a coluna {col_name}'\
                            f'com a seguinte lógica: {exception_cols[col_name]}!')
    # Rename needed columns
    if 'Lançamento' in df.columns:
        df['Descrição'] = df['Lançamento']
    # reorder data
    print(FinanceSchema().keys())
    print(df.keys())
    df = df[FinanceSchema().keys()]
    df.to_csv(filename, sep=current_sep, index=False, header=True)
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
    # remove '.' from hundreds
    data = re.sub(r'(?<=[0-9])\.(?=[0-9]{3})', '', data)
    # change float to '.' from hundreds
    data = re.sub(r'(?<=[0-9])\,(?=[0-9]{2})', '.', data)
    # replace '/' from dates
    data = re.sub(r'([0-9]{2})/([0-9]{2})/([0-9]{4})', r'\g<3>-\g<2>-\g<1>', data)
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(data)
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


