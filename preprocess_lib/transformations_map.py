import polars as pl
import dotenv

dotenv_file = dotenv.find_dotenv('env/.env_transformation_map')
dotenv.load_dotenv(dotenv_file)
return_dict = dotenv.dotenv_values(dotenv_file)
PIX_NUBANK_PROV = return_dict.get('PIX_NUBANK_PROV', '')
PIX_RECEBIDO_TRACK = return_dict.get('PIX_RECEBIDO_TRACK', '')
TRACK_BOLETO_1 = return_dict.get('TRACK_BOLETO_1', '')
TRACK_ASS_1 = return_dict.get('TRACK_ASS_1', '')

class ColumnMap():
    def __init__(self, curr_col: str):
        self.column_mappings = [
            {
                'predicate':
                    [
                        pl.col(curr_col) == 'Pagamento',
                        pl.col('Valor') == -1450.00
                    ],
                'result': pl.lit(TRACK_BOLETO_1)
            },
            {
                'predicate':
                    [
                        pl.col(curr_col) == 'Pagamento',
                        pl.col('Valor') == -20.90
                    ],
                'result': pl.lit(TRACK_ASS_1)
            },
            # nubank proventos
            {
                'predicate':
                    [
                        pl.col(curr_col) == PIX_RECEBIDO_TRACK,
                        pl.col('Categoria').str.contains_any(
                            [
                                'Pix recebido',
                                PIX_NUBANK_PROV
                            ])
                    ],
                'result': pl.lit(PIX_NUBANK_PROV)
            },
            {
                'predicate':
                    [
                        pl.col('Descrição').str.contains_any(
                            [
                                PIX_RECEBIDO_TRACK,
                                PIX_NUBANK_PROV
                            ]),
                        pl.col(curr_col) == 'Pix recebido'
                    ],
                'result': pl.lit(PIX_NUBANK_PROV)
            },
            # salario
            {
                'predicate':
                    [
                        pl.col(curr_col) == 'Salario recebido - Portabilidade',
                    ],
                'result': pl.lit('Salario recebido')
            },
        ]


    def get_column_mappings(self):
        return self.column_mappings
