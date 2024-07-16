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

def create_plot_bar_2(fig, X, Y, category):
    # fig = go.Figure()
    random.seed()
    dict_colors = {}
    cum_sum = 0
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
                base=cum_sum if idx > 0 or X[idx] == X[idx-1] else 0,
                marker=marker, 
                showlegend=pick_legend,
                legendgroup=cat,
                text=f'R$ {Y[idx]}'
                )
        )
        cum_sum += Y[idx]
    # fig.add_trace(
    #         go.Line(x=[X[idx]], y=[sum(Y)], name='Saldo')
    #     )
    fig.update_xaxes(title_text='Date [MM DD, YYYY]')
    fig.update_yaxes(title_text='valor')
    fig.update_layout(template='plotly_dark', title='Test Pix')
    return fig


def create_plot_bar(fig, X, Y, category):
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
                text=f'+ R$ {abs(Y[idx])}' if Y[idx] >= 0 else f'- R$ {abs(Y[idx])}',
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
        title_text='Date [MM DD, YYYY]',
        griddash='dot',
        # rangebreaks=[{'values':excluded_dates}]
        )
    fig.update_yaxes(title_text='valor')
    fig.update_layout(template='plotly_dark', title='Test Pix', barmode='relative')
    return fig


def create_scatterplot(fig, X, Y):
    random.seed()
    marker = {'color':f"rgb({random.randrange(0, 255)}, {random.randrange(0, 255)}, {random.randrange(0, 255)})"}

    fig.add_trace(
        go.Scatter(
            x=X,
            y=Y,
            text=[f'R$ {value}' for value in Y],
            textposition='top center',
            mode='lines+markers+text',
            name='Saldo do dia',
            marker=marker,
            legendrank=1,
            hoverinfo='name+text',
            line={'shape':'spline'}
            ))
    # fig.add_trace(
    #         go.Line(x=[X[idx]], y=[sum(Y)], name='Saldo')
    #     )
    # fig.update_xaxes(title_text='Date [MM DD, YYYY]')
    # fig.update_yaxes(title_text='valor')
    # fig.update_layout(template='plotly_dark', title='Test Pix')
    return fig