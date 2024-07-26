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


    def refresh_plots(self, bar_values, rank_categories, rank_bank, scatter_values):
        self.create_plots(
            bar_values['Data'],
            bar_values['Valor'],
            bar_values['Categoria'],
            bar_values['Descrição'],
            rank_categories,
            rank_bank)
        self.create_scatterplot(
            *scatter_values.values())


    def create_plots(self, X, Y, category, description, rank_cat, rank_bank):
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


        p_obj(obj_grid)
        # Define subplots
        title_list = [j.pop('title') for i in grid_specs for j in i if j and j.get('title')]
        p_obj(title_list)
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

        invest = []
        invest_type = []
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
                    text=f'+ R$ {abs(Y[idx]):.2f}' if Y[idx] >= 0 else f'- R$ {abs(Y[idx]):.2f}',
                    textposition='none',
                    hoverinfo='name+text',
                    legendrank=rank_cat['Categoria'].index(cat)+2
                    ),
                    row=obj_grid['transactions'][0],
                    col=obj_grid['transactions'][1]
            )
            if cat == 'Aplicacao':
                invest.append(abs(Y[idx]))
                invest_type.append(description[idx])
        # Pie
        self.fig.add_trace(
                go.Pie(
                    labels=invest_type,
                    values=invest,
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
        scatter_obj = go.Scatter(
                x=X,
                y=Y,
                text=[f'R$ {value:.2f}' for value in Y],
                textposition='top center',
                mode='lines+markers+text',
                name=f'Saldo {self.refresh_schedule_tuple[1]}',
                marker=self.marker_scatter,
                legendrank=1,
                hoverinfo='name+text',
                line={'shape':'spline'}
                )
        self.fig.add_trace(scatter_obj)


        # range_dates = [X[0]+datetime.timedelta(days=day) for day in range((X[-1]-X[0]).days)]
        # excluded_dates = list(set(range_dates).difference(X))
        # print(excluded_dates, range_dates)

# def create_plot_bar_2(fig, X, Y, category, schedule):
#     match schedule:
#         case 'weekly':
#             refresh = 'Semana'
#         case 'monthly':
#             refresh = 'Mês'
#         case 'quarterly':
#             refresh = 'Quartil'
#         case 'yearly':
#             refresh = 'Ano'
#         case 'daily' | _:
#             refresh = 'Dia'
#     # fig = go.Figure()
#     random.seed()
#     dict_colors = {}
#     for idx, cat in enumerate(category):
#         if dict_colors.get(cat):
#             marker = {'color':dict_colors.get(cat)}
#             pick_legend = False
#         else:
#             dict_colors[cat] = f"rgb({random.randrange(0, 255)}, {random.randrange(0, 255)}, {random.randrange(0, 255)})"
#             marker = {'color':dict_colors.get(cat)}
#             pick_legend = True
#         fig.add_trace(
#             go.Bar(
#                 x=[X[idx]],
#                 y=[Y[idx]],
#                 name=cat,
#                 marker=marker,
#                 showlegend=pick_legend,
#                 legendgroup=cat,
#                 text=f'+ R$ {abs(Y[idx]):.2f}' if Y[idx] >= 0 else f'- R$ {abs(Y[idx]):.2f}',
#                 textposition='none',
#                 hoverinfo='name+text'
#                 )
#         )
#     # fig.add_trace(
#     #         go.Line(x=[X[idx]], y=[sum(Y)], name='Saldo')
#     #     )

#     # range_dates = [X[0]+datetime.timedelta(days=day) for day in range((X[-1]-X[0]).days)]
#     # excluded_dates = list(set(range_dates).difference(X))
#     # print(excluded_dates, range_dates)
#     fig.update_xaxes(
#         title_text=f'Período [{refresh}]',
#         griddash='dot',
#         # rangebreaks=[{'values':excluded_dates}]
#         )
#     fig.update_yaxes(title_text='valor')
#     fig.update_layout(template='plotly_dark', title='Movimentações / Posição', barmode='relative')
#     return fig


# def generate_test_data():
#     v2_cost = [
#         3.48,
#         2.61, 
#         3.19, 
#         2.32,
#         2.90, #2024-07-04
#         2.90,
#         2.90,
#         2.61,
#         2.61,
#         2.61
#     ]

#     v1_cost = [
#         9.57,
#         9.86,
#         9.86, 
#         10.44,
#         9.28, #2024-07-04
#         10.44,
#         8.41,
#         8.41,
#         10.15,
#         10.44
#     ]
#     fig = make_subplots(rows=1, cols=2, subplot_titles=[
#         '<b>Cost estimation between versions</b>',
#         '<b>Cost estimation (Avg)</b>'
#     ])
#     v1_color_marker = {
#         'color':'#FF0000'
#     }
#     v2_color_marker = {
#         'color':'#0011FF'
#     }
#     color_marker_diff_bar = {
#         'color':'#00DD34'
#     }
#     BASE_DATE = '2024-06-30'
#     BASE_DATETIME = datetime.date.fromisoformat(BASE_DATE)
#     DATE = datetime.date.today() - BASE_DATETIME
#     DAY = DATE.days

#     def get_data_range(first_date:str, quantity:int) -> list:
#         return [datetime.date.fromisoformat(first_date) + datetime.timedelta(days=day_cnt) for day_cnt in range(0, quantity)]
#     # by cost
#     fig.add_trace(go.Scatter(x=get_data_range(BASE_DATE, DAY), y=[float(e) for e in v2_cost], textposition='top center', text=[float(e) for e in v2_cost], mode='lines+markers+text', name='v2', marker=v2_color_marker, showlegend=False),row=1, col=1)
#     fig.add_trace(go.Scatter(x=get_data_range(BASE_DATE, DAY), y=[float(e) for e in v1_cost], textposition='top center', text=[float(e) for e in v1_cost],mode='lines+markers+text', name='v1', marker=v1_color_marker, showlegend=False),row=1, col=1)
#     fig.add_trace(go.Bar(
#         x=get_data_range(BASE_DATE, DAY), 
#         y=[v1-v2 for v1, v2 in zip(v1_cost, v2_cost)], 
#         base=v2_cost, 
#         texttemplate=[f'-{(v1-v2)/v1:.2%}' for v1, v2 in zip(v1_cost, v2_cost)],
#         textposition="inside", 
#         name='Cost difference',
#         marker=color_marker_diff_bar
#     ),row=1, col=1)
#     fig.update_xaxes(title_text='Date [MM DD, YYYY]', row=1, col=1)
#     fig.update_yaxes(title_text='Cost (monthly) [USD]', row=1, col=1)
#     # by cost avg
#     v1_avg = [sum(v1_cost)/DAY]
#     v2_avg = [sum(v2_cost)/DAY]
#     fig.add_trace(go.Scatter(x=[f'{DAY} day(s)'], y=v1_avg, textposition='top center', text=v1_avg,mode='lines+markers+text', name='v1', marker=v1_color_marker, legendrank=1),row=1, col=2)
#     fig.add_trace(go.Scatter(x=[f'{DAY} day(s)'], y=v2_avg, textposition='top center', text=v2_avg, mode='lines+markers+text', name='v2', marker=v2_color_marker, legendrank=2),row=1, col=2)
#     fig.add_trace(go.Bar(
#         x=[f'{DAY} day(s)'], 
#         y=[sum([v1-v2 for v1, v2 in zip(v1_cost, v2_cost)])/DAY], 
#         base=v2_avg,
#         texttemplate=[f'-{(v1-v2)/v1:.2%}' for v1, v2 in zip(v1_avg, v2_avg)],
#         textposition="inside", 
#         name='Avg. cost difference',
#         marker=color_marker_diff_bar
#     ),row=1, col=2)
#     fig.update_xaxes(title_text='Date [MM DD, YYYY]', row=1, col=2)
#     fig.update_yaxes(title_text='Cost (monthly) [USD]', row=1, col=2)
#     # fig.update_layout(height=400)
#     fig.update_layout(template='plotly_dark')
#     return fig
