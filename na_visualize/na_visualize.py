from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import sqlite3
import datetime

START_DATE = datetime.date(2022, 8, 16)

app = Dash(__name__, title="NA-Radar")
application = app.server
colors = ["DarkGreen", "DarkBlue", "DarkRed", "DarkOrange"]

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
            start_date=START_DATE,
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
    if end_date:
        end_time = int(datetime.datetime.fromisoformat(end_date).timestamp())
    else:
        end_time = int(datetime.datetime.today().timestamp()) + 100000

    connection = sqlite3.connect("naflight.db")
    cursor = connection.cursor()
    sql = f"SELECT airline, COUNT(airline) AS airline_count, \
        SUM(CASE WHEN (operation = 0 AND curfew = 0) THEN 1 ELSE 0 END) AS takeoff, \
        SUM(CASE WHEN (operation = 1 AND curfew = 0) THEN 1 ELSE 0 END) AS landing, \
        SUM(CASE WHEN (operation = 0 AND curfew = 1) THEN 1 ELSE 0 END) AS takeoff_curfew, \
        SUM(CASE WHEN (operation = 1 AND curfew = 1) THEN 1 ELSE 0 END) AS landing_curfew \
        FROM flights WHERE time>{start_time} AND time<{end_time} \
        GROUP BY airline ORDER BY airline_count DESC;"

    cursor.execute(sql)
    rows = cursor.fetchall()
    connection.close()

    airlines = []
    amount = []
    opes = []
    airlines_index = {}

    for row in rows:
        airlines.append(row[0])
        airlines.append(row[0])
        airlines.append(row[0])
        airlines.append(row[0])
        opes.append("Décollage")
        opes.append("Atterrissage")
        opes.append("Décollage couvre-feu")
        opes.append("Atterrissage couvre-feu")
        amount.append(row[2])
        amount.append(row[3])
        amount.append(row[4])
        amount.append(row[5])

    df = pd.DataFrame({"Compagnies": airlines, "Nombre": amount, "Mouvement": opes})

    fig = px.bar(
        df,
        x="Compagnies",
        y="Nombre",
        color="Mouvement",
        text_auto=True,
        height=600,
        color_discrete_sequence=colors,
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
