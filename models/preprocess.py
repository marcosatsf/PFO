# This script should exist in order to pre-process data
import polars as pl
from schema.finance import FinanceSchema
from schema.fatura import FaturaSchema

def pre_process_csv(path: str) -> pl.DataFrame:
    df = load_csv_df(path)
    if 'Tipo' in df.columns:
        print('transform!')
        return df.drop('Tipo')\
            .rename({'Lançamento':'Descrição'})\
            .with_columns(pl.col('Valor').str.extract(r'([0-9]+,[0-9]+)', 1).str.replace(',', '.').cast(pl.Float64).mul(-1))\
            .with_columns(Saldo=pl.lit(0.0).cast(pl.Float64))\
            .select('Data', 'Descrição', 'Valor', 'Saldo', 'Categoria')
            # pass
            # return df.with_columns(
            #     pl.col('Descrição')\
            #     .map_elements(lambda val: val.split(':')[0] , return_dtype=pl.String)\
            #     .alias('Categoria')
            #     )


def load_csv_df(path, separator = ',', schema:pl.Schema = None) -> pl.DataFrame:
    if schema:
        return pl.read_csv(path,
                    separator=separator,
                    schema=schema,
                    decimal_comma=True
                    )
    try:
        return pl.read_csv(path,
                    separator=separator,
                    schema=FinanceSchema()
                    )
    except pl.exceptions.ComputeError as e:
        return pl.read_csv(path,
                        separator=separator,
                        schema=FaturaSchema()
                        )


