from flask import Flask, render_template
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import mysql.connector
from datetime import datetime
import plotly.graph_objects as go
import numpy as np

db_config = {
    'host': ' roundhouse.proxy.rlwy.net',         
    'port': '14710',
    'user': 'root',        
    'password': 'ZvulfgacDrHrzwoGqOIEcoossaCHrxCF', 
    'database': 'railway'
}

def get_temperature_data(table_name, start_date, end_date):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    query = f"SELECT fecha, ROUND(temperaturaaire, 1) FROM {table_name} WHERE fecha BETWEEN '{start_date}' AND '{end_date}'"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    if data:
        dates, temperatures = zip(*data)
    else:
        dates, temperatures = [], []
    return dates, temperatures

server = Flask(__name__)

app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/')

app.layout = html.Div([
    html.Div(
        [
            html.Div(
                [
                    html.Img(src="/assets/Nova.PNG", style={'width': '200px', 'height': '50px'}),
                    html.H1("Cuartos Fríos", style={
                        'color': 'dimgray',
                        'display': 'inline-block',
                        'vertical-align': 'middle',
                        'margin': '0 20px',
                    }),
                ],
                style={
                    'background-color': 'rgb(0, 141, 34)',
                    'padding': '20px',
                    'border': '3px solid green',
                    'border-radius': '5px',
                    'display': 'flex',
                    'align-items': 'center',
                }
            ),
            html.Br(),
            html.B("Selecciona Cuarto: "), 
            dcc.Dropdown(
                id='room-selection',
                options=[
                    {'label': 'Supervisión', 'value': 'emetereologicas'},
                    {'label': 'Histórico', 'value': 'emetereologicas'},
                    {'label': 'Análisis', 'value': 'emetereologicas'},                 
                ],
                value='emetereologicas',
                clearable=False,
                style={'width': '300px', 'marginBottom': 10, 'fontSize': 16}
            ),
            html.Div(html.B("Seleccione Fecha: "), style={'display': 'inline-block', 'marginRight': '10px'}),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=datetime(2023, 7, 1),
                end_date=datetime(2023, 7, 7),
                display_format='YYYY-MM-DD',
                style={'marginBottom': 10}
            ),
        ],
        style={
            'marginBottom': 30,
            'padding': '10px',
            'border-radius': '5px',
        }
    ),
    html.Div([
        dcc.Graph(id='temperature-graph', style={'width': '50%', 'display': 'inline-block'}),
        dcc.Graph(id='histogram-graph', style={'width': '50%', 'display': 'inline-block'})
    ]),
])

@app.callback(
    [Output('temperature-graph', 'figure'),
     Output('histogram-graph', 'figure')],
    [Input('room-selection', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_graph(selected_room, start_date, end_date):
    dates, temperatures = get_temperature_data(selected_room, start_date, end_date)
    fig_temperature = go.Figure()
    point_colors = ['red' if temp > -12 else 'blue' for temp in temperatures]
    fig_temperature.add_trace(go.Scatter(
        x=dates,
        y=temperatures,
        mode='lines+markers',
        marker=dict(size=8, color=point_colors),
        name='Temperatura'
    ))
    fig_temperature.update_layout(
        title='Gráfico de Temperatura vs Tiempo',
        xaxis=dict(title='Fecha'),
        yaxis=dict(title='Temperatura'),
        hovermode='closest'
    )

    fig_histogram = go.Figure()
    frequencies, bins = np.histogram(temperatures, bins=8)
    bin_ranges = [(round(bin_start, 1), round(bin_end, 1)) for bin_start, bin_end in zip(bins[:-1], bins[1:])]
    x_labels = [f'{bin_start:.1f} - {bin_end:.1f}' for bin_start, bin_end in bin_ranges]
    bar_colors = ['red' if bin_end > -12 else 'blue' for bin_start, bin_end in bin_ranges]

    fig_histogram.add_trace(go.Bar(
        x=x_labels,
        y=frequencies,
        name='Info',
        marker=dict(color=bar_colors, line=dict(color='white', width=0.1)),
        hoverinfo='text',
        hovertext=[f'Rango: {x_label}<br>Frecuencia: {freq}' for x_label, freq in zip(x_labels, frequencies)],
        text=frequencies,
        textposition='outside'
    ))
    fig_histogram.update_layout(
        title='Histograma de Temperatura',
        xaxis=dict(title='Temperatura', showgrid=True, dtick=1),
        yaxis=dict(title='Frecuencia'),
        hovermode='closest'
    )

    return fig_temperature, fig_histogram

@server.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=8080)
