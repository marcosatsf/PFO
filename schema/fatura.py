from typing import Iterable, Mapping
import polars as pl

class FaturaSchema(pl.Schema):
    def __init__(self, schema:
                 Mapping[str, pl.DataType] | Iterable[tuple[str, pl.DataType]] = {
            'Data': pl.Date(),
            'Lançamento': pl.String(), #Descrição
            'Categoria': pl.String(),
            'Tipo': pl.String(),
            'Valor': pl.String(),
            }):
        super().__init__(schema)