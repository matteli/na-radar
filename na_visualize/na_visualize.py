from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import sqlite3
import datetime

START_DATE = datetime.date(2022, 8, 15)

app = Dash(__name__, title="NA-Radar")
application = app.server
colors = ["DarkGreen", "DarkBlue", "DarkOrange", "DarkRed"]

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
    sql = f"SELECT airline, operation, curfew, count(airline) as airline_count \
        FROM flights WHERE time>{start_time} AND time<{end_time} \
        GROUP BY airline, operation, curfew ORDER BY airline_count DESC;"
    cursor.execute(sql)
    rows = cursor.fetchall()
    connection.close()

    airlines = []
    amount = []
    opes = []
    airlines_index = {}

    for row in rows:
        if not row[0] in airlines:
            airlines.append(row[0])
            airlines.append(row[0])
            airlines.append(row[0])
            airlines.append(row[0])
            opes.append("Décollage")
            opes.append("Atterrissage")
            opes.append("Décollage couvre-feu")
            opes.append("Atterrissage couvre-feu")
            amount.append(0)
            amount.append(0)
            amount.append(0)
            amount.append(0)
            airlines_index[row[0]] = len(airlines) - 4
        if row[2] == 0:
            if row[1] == 0:
                # take off no curfew
                amount[airlines_index[row[0]]] = row[3]
            else:
                # landing no curfew
                amount[airlines_index[row[0]] + 1] = row[3]
        else:
            if row[1] == 0:
                # take off curfew
                amount[airlines_index[row[0]] + 2] = row[3]
            else:
                # landing curfew
                amount[airlines_index[row[0]] + 3] = row[3]

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
