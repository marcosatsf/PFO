from typing import Iterable, Mapping
import polars as pl

class FinanceSchema(pl.Schema):
    def __init__(self, schema:
                 Mapping[str, pl.DataType] | Iterable[tuple[str, pl.DataType]] = {
            'Data': pl.Date(),
            'Descrição': pl.String(),
            'Valor': pl.Float64(),
            'Saldo': pl.Float64(),
            'Categoria': pl.String()
            }):
        super().__init__(schema)