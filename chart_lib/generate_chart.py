from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime
import random
from .functions import populate_grid_specs, generate_grid_specs, p_obj

class ChartBuilder():
    def __init__(self,
                 grid: tuple[int, int],
                 refresh: str = 'daily') -> None:
        random.seed()
        self.dict_colors = {}
        self.dict_bank_colors = {}
        self.dict_markers = {}
        self.marker_scatter = {'color':f"rgb({random.randrange(0, 255)}, {random.randrange(0, 255)}, {random.randrange(0, 255)})"}
        self.current_grid = grid
        self.set_figure()
        self.set_schedule(refresh)


    def add_bank_color(self, bank, color):
        self.dict_bank_colors[bank] = color


    def set_schedule(self, value):
        match value:
            case 'weekly':
                self.refresh_schedule_tuple = ('Semana', 'semanal')
            case 'monthly':
                self.refresh_schedule_tuple = ('Mês', 'mensal')
            case 'quarterly':
                self.refresh_schedule_tuple = ('Quartil', 'quadrimestre')
            case 'yearly':
                self.refresh_schedule_tuple = ('Ano', 'anual')
            case 'daily' | _:
                self.refresh_schedule_tuple = ('Dia', 'diário')


    def set_figure(self):
        self.fig = go.Figure()


    def get_figure(self):
        return self.fig


    def refresh_plots(self, bar_values, investments, rank_categories, rank_bank, scatter_values):
        self.create_plots(
            bar_values['Data'],
            bar_values['Valor'],
            bar_values['Categoria'],
            bar_values['Descrição'],
            investments,
            rank_categories,
            rank_bank)
        self.create_scatterplot(
            *scatter_values.values())


    def create_plots(self, X, Y, category, description, investments, rank_cat, rank_bank):
        charts_struct = [ # coord -> (x1,y1,x2,y2)
                {'type': 'bar', 'name': 'transactions', 'title': '<b>Movimentações / Posição</b>', 'coord': (0,0,2,2)},
                {'type': 'pie', 'name': 'investment', 'title': '<b>Investimentos</b>', 'coord': (0,3,0,3)},
                {'type': 'treemap' , 'name': 'bank', 'title': '<b>Distribuição nos bancos/corretoras</b>', 'coord': (1,3,1,3)},
                {'type': 'treemap', 'name': 'categories', 'title': '<b>Categorias mais usadas</b>', 'coord': (2,3,2,3)}
            ]

        grid_specs, obj_grid = populate_grid_specs(
            generate_grid_specs(self.current_grid),
            charts_struct
            )

        #p_obj(obj_grid)
        # Define subplots
        title_list = [j.pop('title') for i in grid_specs for j in i if j and j.get('title')]
        # p_obj(title_list)
        self.fig = make_subplots(
            rows=self.current_grid[0],
            cols=self.current_grid[1],
            subplot_titles=title_list,
            specs=grid_specs
            )
        # ], specs=[[{}, { 'type': 'domain' }]])
        # [
        #     '<b>Movimentações / Posição</b>',
        #     '<b>Investimentos</b>',
        #     '<b>Categorias mais usadas</b>'
        # ]

        repeated_marker = []
        # invest = []
        # invest_type = []
        for idx, cat in enumerate(category):
            # if not self.dict_markers.get(cat):
            if not self.dict_colors.get(cat):
                self.dict_colors[cat] = f"rgb({random.randrange(0, 255)}, {random.randrange(0, 255)}, {random.randrange(0, 255)})"
            marker = {'color':self.dict_colors.get(cat)}
            if cat in repeated_marker:
                pick_legend = False # needs always
            else:
                repeated_marker.append(cat)
                pick_legend = True # needs always
            self.fig.add_trace(
                go.Bar(
                    x=[X[idx]],
                    y=[Y[idx]],
                    name=cat,
                    marker=marker,
                    showlegend=pick_legend,
                    legendgroup=cat,
                    text=(f'+ R$ {abs(Y[idx]):.2f}' if Y[idx] >= 0 else f'- R$ {abs(Y[idx]):.2f}')
                        + '<br>'
                        + 'Descrição: '
                        + (f'{description[idx][0:50]}' if len(description[idx]) < 50 else f'{description[idx][0:47]}...'),
                    textposition='none',
                    hoverinfo='x+name+text',
                    hoverlabel=dict(
                        namelength=-1
                    ),
                    # hovertemplate="<br>".join([
                    #     "label: %{customdata[0]}",
                    #     "width: %{width}",
                    #     "height: %{y}",
                    #     "area: %{customdata[1]}",
                    # ])
                    legendrank=sorted(rank_cat['Categoria']).index(cat)+2
                    ),
                    row=obj_grid['transactions'][0],
                    col=obj_grid['transactions'][1]
            )
        now_datetime = datetime.datetime.now()
        last_30_days = now_datetime - datetime.timedelta(days=30)
        self.fig.update_layout(
            xaxis=dict(
                rangeslider=dict(
                    visible=True,
                    thickness=0.04,
                ),
                type="date",
                range=(last_30_days, now_datetime.strftime('%Y-%m-%d'))
            ),
            yaxis=dict(
                fixedrange=False,
            )
        )
        # self.fig.update_traces(
        #     hovertemplate="<br>".join(
        #             [
        #                 "%{name}",
        #                 "%{text}",
        #                 "Data: %{x}"
        #             ]
        #         )
        # )
            # if cat == 'Aplicacao':
            #     invest.append(abs(Y[idx]))
            #     invest_type.append(description[idx].split('"')[1])
        # Pie
        self.fig.add_trace(
                go.Pie(
                    labels=investments['Descrição'],
                    values=investments['Valor'],
                    textinfo='percent+value', #'label+percent+value'
                    showlegend=False,
                    hole=.5),
                row=obj_grid['investment'][0],
                col=obj_grid['investment'][1]
            )
        print(self.dict_bank_colors)
        # Treemap bank
        self.fig.add_trace(
                go.Treemap(
                    labels=rank_bank['Banco/Corretora'],
                    values=rank_bank['Valor'],
                    parents=['']*len(rank_bank['Banco/Corretora']),
                    maxdepth=2,
                    root_color="black",
                    textinfo='label+value+percent root',
                    marker_colors=[self.dict_bank_colors[bank] for bank in rank_bank['Banco/Corretora']]),
                row=obj_grid['bank'][0],
                col=obj_grid['bank'][1]
            )
        self.fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

        # Treemap categories
        self.fig.add_trace(
                go.Treemap(
                    labels=rank_cat['Categoria'],
                    values=rank_cat['Valor'],
                    parents=['']*len(rank_cat['Categoria']),
                    maxdepth=5,
                    root_color="black",
                    textinfo='label+value+percent root',
                    marker_colors=[self.dict_colors.get(cat) for cat in rank_cat['Categoria']]),
                row=obj_grid['categories'][0],
                col=obj_grid['categories'][1]
            )
        self.fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

        self.fig.update_xaxes(
            title_text=f'Período [{self.refresh_schedule_tuple[0]}]',
            griddash='dot',
            row=obj_grid['transactions'][0],
            col=obj_grid['transactions'][1]
            # rangebreaks=[{'values':excluded_dates}]
            )
        self.fig.update_yaxes(
            title_text='valor',
            row=obj_grid['transactions'][0],
            col=obj_grid['transactions'][1]
            )
        self.fig.update_layout(template='plotly_dark', barmode='relative')


    def create_scatterplot(self, X, Y):
        partial_by_each = 5
        scatter_obj = go.Scatter(
                x=X,
                y=Y,
                text=[f'R$ {value:.2f}' for value in Y],
                textposition='top center',
                mode='lines+markers',
                name=f'Saldo {self.refresh_schedule_tuple[1]}',
                marker=self.marker_scatter,
                legendrank=1,
                hoverinfo='name+text',
                line={'shape':'spline'},
                )
        for idx, _ in enumerate(X):
            self.fig.add_annotation(
                x=X[idx],
                y=Y[idx],
                text=f'R$ {Y[idx]:.2f}' if idx % partial_by_each == 0 else '',
                textangle=35,
                showarrow=True if idx % partial_by_each == 0 else False,
                # align='center',
                yanchor='bottom',
                xanchor='auto'
            )
        self.fig.add_trace(scatter_obj)

        # range_dates = [X[0]+datetime.timedelta(days=day) for day in range((X[-1]-X[0]).days)]
        # excluded_dates = list(set(range_dates).difference(X))
        # print(excluded_dates, range_dates)