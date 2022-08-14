from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import sqlite3
import datetime

START_DATE = datetime.date(2022, 8, 10)

app = Dash(__name__, title="NA-Radar")
application = app.server

app.layout = html.Div(
    children=[
        html.H1(children="NA-Radar"),
        html.Section(
            children=f"""
        Suivi des mouvements d'avions sur l'aéroport de Nantes-Atlantique.
    """
        ),
        dcc.DatePickerRange(
            id="date-pick",
            min_date_allowed=START_DATE,
            max_date_allowed=datetime.datetime.today(),
            start_date=START_DATE,
            end_date=datetime.datetime.today(),
            display_format="DD/MM/YY",
            start_date_placeholder_text="DD/MM/YY",
        ),
        dcc.Graph(id="graph"),
        dcc.Interval(
            id="interval-component",
            interval=60 * 1000,  # in milliseconds
            n_intervals=0,
        ),
    ]
)


@app.callback(
    Output("graph", "figure"),
    Input("interval-component", "n_intervals"),
    Input("date-pick", "start_date"),
    Input("date-pick", "end_date"),
)
def update_graph(n, start_date, end_date):
    start_time = int(datetime.datetime.fromisoformat(start_date).timestamp())
    end_time = int(datetime.datetime.fromisoformat(end_date).timestamp())
    connection = sqlite3.connect("naflight.db")
    cursor = connection.cursor()
    sql = f"SELECT * FROM flights WHERE time>{start_time} AND time<{end_time}"
    cursor.execute(sql)
    rows = cursor.fetchall()
    connection.close()

    airlines = []
    amount = []
    total = 0
    opes = []

    for row in rows:
        airline = row[1]
        ope = row[2]
        curfew = row[8]
        if not airline in airlines:
            airlines.append(airline)
            airlines.append(airline)
            airlines.append(airline)
            airlines.append(airline)
            opes.append("Décollage")
            opes.append("Atterrissage")
            opes.append("Décollage couvre-feu")
            opes.append("Atterrissage couvre-feu")
            amount.append(0)
            amount.append(0)
            amount.append(0)
            amount.append(0)
        i = airlines.index(airline)
        if curfew == 0:
            if ope == 1:  # landing
                i = airlines.index(row[1], i + 1)
        elif curfew == 1:
            i = airlines.index(row[1], i + 1)
            i = airlines.index(row[1], i + 1)
            if ope == 1:  # landing
                i = airlines.index(row[1], i + 1)
        amount[i] += 1
        total += 1

    df = pd.DataFrame({"Compagnies": airlines, "Nombre": amount, "Mouvement": opes})

    fig = px.bar(
        df, x="Compagnies", y="Nombre", color="Mouvement", text_auto=True, height=600
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
