from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime
import random

def generate_test_data():
    v2_cost = [
        3.48,
        2.61, 
        3.19, 
        2.32,
        2.90, #2024-07-04
        2.90,
        2.90,
        2.61,
        2.61,
        2.61
    ]

    v1_cost = [
        9.57,
        9.86,
        9.86, 
        10.44,
        9.28, #2024-07-04
        10.44,
        8.41,
        8.41,
        10.15,
        10.44
    ]
    fig = make_subplots(rows=1, cols=2, subplot_titles=[
        '<b>Cost estimation between versions</b>',
        '<b>Cost estimation (Avg)</b>'
    ])
    v1_color_marker = {
        'color':'#FF0000'
    }
    v2_color_marker = {
        'color':'#0011FF'
    }
    color_marker_diff_bar = {
        'color':'#00DD34'
    }
    BASE_DATE = '2024-06-30'
    BASE_DATETIME = datetime.date.fromisoformat(BASE_DATE)
    DATE = datetime.date.today() - BASE_DATETIME
    DAY = DATE.days

    def get_data_range(first_date:str, quantity:int) -> list:
        return [datetime.date.fromisoformat(first_date) + datetime.timedelta(days=day_cnt) for day_cnt in range(0, quantity)]
    # by cost
    fig.add_trace(go.Scatter(x=get_data_range(BASE_DATE, DAY), y=[float(e) for e in v2_cost], textposition='top center', text=[float(e) for e in v2_cost], mode='lines+markers+text', name='v2', marker=v2_color_marker, showlegend=False),row=1, col=1)
    fig.add_trace(go.Scatter(x=get_data_range(BASE_DATE, DAY), y=[float(e) for e in v1_cost], textposition='top center', text=[float(e) for e in v1_cost],mode='lines+markers+text', name='v1', marker=v1_color_marker, showlegend=False),row=1, col=1)
    fig.add_trace(go.Bar(
        x=get_data_range(BASE_DATE, DAY), 
        y=[v1-v2 for v1, v2 in zip(v1_cost, v2_cost)], 
        base=v2_cost, 
        texttemplate=[f'-{(v1-v2)/v1:.2%}' for v1, v2 in zip(v1_cost, v2_cost)],
        textposition="inside", 
        name='Cost difference',
        marker=color_marker_diff_bar
    ),row=1, col=1)
    fig.update_xaxes(title_text='Date [MM DD, YYYY]', row=1, col=1)
    fig.update_yaxes(title_text='Cost (monthly) [USD]', row=1, col=1)
    # by cost avg
    v1_avg = [sum(v1_cost)/DAY]
    v2_avg = [sum(v2_cost)/DAY]
    fig.add_trace(go.Scatter(x=[f'{DAY} day(s)'], y=v1_avg, textposition='top center', text=v1_avg,mode='lines+markers+text', name='v1', marker=v1_color_marker, legendrank=1),row=1, col=2)
    fig.add_trace(go.Scatter(x=[f'{DAY} day(s)'], y=v2_avg, textposition='top center', text=v2_avg, mode='lines+markers+text', name='v2', marker=v2_color_marker, legendrank=2),row=1, col=2)
    fig.add_trace(go.Bar(
        x=[f'{DAY} day(s)'], 
        y=[sum([v1-v2 for v1, v2 in zip(v1_cost, v2_cost)])/DAY], 
        base=v2_avg,
        texttemplate=[f'-{(v1-v2)/v1:.2%}' for v1, v2 in zip(v1_avg, v2_avg)],
        textposition="inside", 
        name='Avg. cost difference',
        marker=color_marker_diff_bar
    ),row=1, col=2)
    fig.update_xaxes(title_text='Date [MM DD, YYYY]', row=1, col=2)
    fig.update_yaxes(title_text='Cost (monthly) [USD]', row=1, col=2)
    # fig.update_layout(height=400)
    fig.update_layout(template='plotly_dark')
    return fig


def create_plot_bar_2(fig, X, Y, category, schedule):
    match schedule:
        case 'weekly':
            refresh = 'Semana'
        case 'monthly':
            refresh = 'Mês'
        case 'quarterly':
            refresh = 'Quartil'
        case 'yearly':
            refresh = 'Ano'
        case 'daily' | _:
            refresh = 'Dia'
    # fig = go.Figure()
    random.seed()
    dict_colors = {}
    for idx, cat in enumerate(category):
        if dict_colors.get(cat):
            marker = {'color':dict_colors.get(cat)}
            pick_legend = False
        else:
            dict_colors[cat] = f"rgb({random.randrange(0, 255)}, {random.randrange(0, 255)}, {random.randrange(0, 255)})"
            marker = {'color':dict_colors.get(cat)}
            pick_legend = True
        fig.add_trace(
            go.Bar(
                x=[X[idx]],
                y=[Y[idx]],
                name=cat,
                marker=marker,
                showlegend=pick_legend,
                legendgroup=cat,
                text=f'+ R$ {abs(Y[idx]):.2f}' if Y[idx] >= 0 else f'- R$ {abs(Y[idx]):.2f}',
                textposition='none',
                hoverinfo='name+text'
                )
        )
    # fig.add_trace(
    #         go.Line(x=[X[idx]], y=[sum(Y)], name='Saldo')
    #     )

    # range_dates = [X[0]+datetime.timedelta(days=day) for day in range((X[-1]-X[0]).days)]
    # excluded_dates = list(set(range_dates).difference(X))
    # print(excluded_dates, range_dates)
    fig.update_xaxes(
        title_text=f'Período [{refresh}]',
        griddash='dot',
        # rangebreaks=[{'values':excluded_dates}]
        )
    fig.update_yaxes(title_text='valor')
    fig.update_layout(template='plotly_dark', title='Movimentações / Posição', barmode='relative')
    return fig


def generate_grid_specs(grid: tuple) -> list[list[dict]]:
    """
    Creates a grid of dicts. e.g:
    2x3:
    [
    [{},{},{}],
    [{},{},{}]
    ]

    Args:
        grid (tuple): _description_

    Returns:
        list[list[dict]]: _description_
    """
    return [[None for _ in range(grid[1])] for _ in range(grid[0])]


def populate_grid_specs(grid_specs: list[list[dict]], list_objs: list[dict]) -> dict:
    obj_grid = {}
    for obj in list_objs:
        name = obj['name']
        x1, y1, x2, y2 = obj['coord']
        if x2 > x1:
            if y2 > y1:
                grid_specs[x1][y1] = {'rowspan': x2-x1+1, 'colspan': y2-y1+1}
            else: #means only equal (y2 = y1), never less
                grid_specs[x1][y1] = {'rowspan': x2-x1+1}
        else: #means only equal (x2 = x1), never less
            if y2 > y1:
                grid_specs[x1][y1] = {'colspan': y2-y1+1}
            else: #means only equal (y2 = y1), never less
                grid_specs[x1][y1] = {}
        if name == 'pie':
            grid_specs[x1][y1]['type'] = 'domain'
        if name == 'treemap':
            grid_specs[x1][y1]['type'] = 'treemap'
        obj_grid[name] = (x1+1,y1+1)
    return grid_specs, obj_grid


def create_plot_bar(fig, X, Y, category, description, rankdf, schedule):
    grid = (3,4)
    grid_spec = generate_grid_specs(grid)
    grid_specs, obj_grid = populate_grid_specs(
        grid_spec,
        [
            {'name':'bar', 'coord': (0,0,0,0)},
            {'name':'pie', 'coord': (1,0,1,0)},
            {'name':'treemap', 'coord': (0,1,2,3)},
        ])
    # [
    #         {'name':'bar', 'coord': (0,0,2,2)},
    #         {'name':'pie', 'coord': (0,3,0,3)},
    #         {'name':'treemap', 'coord': (1,3,2,3)},
    #     ])
    for e in grid_specs:
        print(e)

    print(obj_grid)

    fig = make_subplots(rows=grid[0], cols=grid[1], subplot_titles=[
        '<b>Movimentações / Posição</b>',
        '<b>Investimentos</b>',
        '<b>Categorias mais usadas</b>'
    ], specs=grid_specs)
    # ], specs=[[{}, { 'type': 'domain' }]])

    match schedule:
        case 'weekly':
            refresh = 'Semana'
        case 'monthly':
            refresh = 'Mês'
        case 'quarterly':
            refresh = 'Quartil'
        case 'yearly':
            refresh = 'Ano'
        case 'daily' | _:
            refresh = 'Dia'
    # fig = go.Figure()
    random.seed()
    dict_colors = {}
    invest = []
    invest_type = []
    for idx, cat in enumerate(category):
        if dict_colors.get(cat):
            marker = {'color':dict_colors.get(cat)}
            pick_legend = False
        else:
            dict_colors[cat] = f"rgb({random.randrange(0, 255)}, {random.randrange(0, 255)}, {random.randrange(0, 255)})"
            marker = {'color':dict_colors.get(cat)}
            pick_legend = True
        fig.add_trace(
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
                legendrank=rankdf['Categoria'].index(cat)+2
                ),
                row=obj_grid['bar'][0],
                col=obj_grid['bar'][1]
        )
        if cat == 'Aplicacao':
            invest.append(abs(Y[idx]))
            invest_type.append(description[idx])

    fig.add_trace(
            go.Pie(
                labels=invest_type,
                values=invest,
                textinfo='percent+value',
                showlegend=False),
            row=obj_grid['pie'][0],
            col=obj_grid['pie'][1]
        )
    print(rankdf)
    fig.add_trace(
            go.Treemap(
                labels=rankdf['Categoria'],
                values=rankdf['Valor'],
                maxdepth=2,
                root_color="white",
                textinfo='label+value+percent parent+percent entry'),
            row=obj_grid['treemap'][0],
            col=obj_grid['treemap'][1]
        )
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

    # range_dates = [X[0]+datetime.timedelta(days=day) for day in range((X[-1]-X[0]).days)]
    # excluded_dates = list(set(range_dates).difference(X))
    # print(excluded_dates, range_dates)
    fig.update_xaxes(
        title_text=f'Período [{refresh}]',
        griddash='dot',
        row=obj_grid['bar'][0],
        col=obj_grid['bar'][1]
        # rangebreaks=[{'values':excluded_dates}]
        )
    fig.update_yaxes(
        title_text='valor',
        row=obj_grid['bar'][0],
        col=obj_grid['bar'][1]
        )
    fig.update_layout(template='plotly_dark', barmode='relative')
    return fig


def create_scatterplot(fig, X, Y, schedule):
    random.seed()
    marker = {'color':f"rgb({random.randrange(0, 255)}, {random.randrange(0, 255)}, {random.randrange(0, 255)})"}

    match schedule:
        case 'weekly':
            refresh = 'semanal'
        case 'monthly':
            refresh = 'mensal'
        case 'quarterly':
            refresh = 'quadrimestre'
        case 'yearly':
            refresh = 'anual'
        case 'daily' | _:
            refresh = 'diário'
    scatter_obj = go.Scatter(
            x=X,
            y=Y,
            text=[f'R$ {value:.2f}' for value in Y],
            textposition='top center',
            mode='lines+markers+text',
            name=f'Saldo {refresh}',
            marker=marker,
            legendrank=1,
            hoverinfo='name+text',
            line={'shape':'spline'}
            )
    fig.add_trace(scatter_obj)
    return fig