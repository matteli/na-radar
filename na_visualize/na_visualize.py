from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
import pandas as pd
import sqlite3
import datetime

START_DATE = datetime.date(2022, 8, 18)

app = Dash(__name__, title="NA-Radar")
application = app.server

app.layout = html.Div(
    children=[
        html.H1(children="NA-Radar"),
        html.H3(
            children=f"""
        Suivi des mouvements d'avions sur l'aéroport de Nantes-Atlantique.
    """
        ),
        html.Br(),
        html.Div(
            children=[
                html.Div(
                    children=[
                        dcc.DatePickerRange(
                            id="date-pick",
                            min_date_allowed=START_DATE,
                            start_date=START_DATE,
                            display_format="DD/MM/YY",
                            start_date_placeholder_text="DD/MM/YY",
                            style={
                                "display": "flex",
                                "justify-content": "center",
                            },
                        ),
                    ],
                    style={"padding": 10, "flex": 2},
                ),
                html.Div(
                    children=[
                        dcc.Dropdown(
                            options=[
                                {
                                    "label": html.Div(
                                        ["Plage horaire des mouvements"],
                                        style={"font-size": 19},
                                    ),
                                    "value": "CF",
                                },
                                {
                                    "label": html.Div(
                                        ["Zone des mouvements"], style={"font-size": 19}
                                    ),
                                    "value": "ZM",
                                },
                                {
                                    "label": html.Div(
                                        ["Type des mouvements avec plage horaire"],
                                        style={"font-size": 19},
                                    ),
                                    "value": "CFTM",
                                },
                                {
                                    "label": html.Div(
                                        ["Zone des mouvements avec plage horaire"],
                                        style={"font-size": 19},
                                    ),
                                    "value": "CFZM",
                                },
                            ],
                            value="CF",
                            clearable=False,
                            searchable=False,
                            id="type-pick",
                            style={"height": 48, "border-radius": "0px"},
                        ),
                    ],
                    style={"padding": 10, "flex": 3},
                ),
                html.Div(
                    children=[
                        html.Button(
                            "Ok",
                            id="ok-button",
                            n_clicks=0,
                            style={"height": "100%", "width": "100%", "font-size": 19},
                        ),
                    ],
                    style={"padding": 10, "flex": 1},
                ),
            ],
            style={
                "display": "flex",
                "justify-content": "space-around",
                "align-items": "stretch",
                "flex-direction": "row",
            },
        ),
        html.Div(
            children=[
                html.Span(
                    "Total : ",
                    style={
                        "text-align": "center",
                        "padding": "10px",
                        "margin-top": "5px",
                    },
                ),
                html.Span(id="span1", className="badge"),
                html.Span(id="span2", className="badge"),
                html.Span(id="span3", className="badge"),
                html.Span(id="span4", className="badge"),
            ],
            style={
                "display": "flex",
                "align-items": "stretch",
                "flex-direction": "row",
            },
        ),
        dcc.Graph(id="graph"),
        dcc.Interval(
            id="interval-component",
            interval=60 * 1000,  # in milliseconds
            n_intervals=0,
        ),
    ],
)


@app.callback(
    Output("graph", "figure"),
    Output("span1", "children"),
    Output("span1", "style"),
    Output("span2", "children"),
    Output("span2", "style"),
    Output("span3", "children"),
    Output("span3", "style"),
    Output("span4", "children"),
    Output("span4", "style"),
    Input("interval-component", "n_intervals"),
    Input("ok-button", "n_clicks"),
    State("date-pick", "start_date"),
    State("date-pick", "end_date"),
    State("type-pick", "value"),
)
def update_graph(n_intervals, n_clicks, start_date, end_date, type_graph):
    start_time = int(datetime.datetime.fromisoformat(start_date).timestamp())
    if end_date:
        end_time = int(datetime.datetime.fromisoformat(end_date).timestamp())
    else:
        end_time = int(datetime.datetime.today().timestamp()) + 100000

    connection = sqlite3.connect("flights.db")
    cursor = connection.cursor()

    if type_graph == "CF":
        sql = f"SELECT airline, \
            SUM(NOT curfew) AS not_curfew, \
            SUM(curfew) AS curfew \
            FROM flights WHERE time>{start_time} AND time<{end_time} \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        combo = False
        colors = ["DarkGreen", "DarkRed"]
        opes_title = "Plage horaire"
        opes_label = (
            "Jour",
            "Couvre-feu",
        )

    elif type_graph == "ZM":
        sql = f"SELECT airline, \
            SUM(NOT north_fly) AS south_fly, \
            SUM(north_fly) AS north_fly \
            FROM flights WHERE time>{start_time} AND time<{end_time} \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        combo = False
        colors = ["DarkRed", "DarkOrange"]
        opes_title = "Zone"
        opes_label = (
            "Sud",
            "Nord",
        )

    elif type_graph == "CFTM":
        sql = f"SELECT airline, \
            SUM(NOT(landing OR curfew)) AS takeoff, \
            SUM(landing AND NOT curfew) AS landing, \
            SUM(NOT landing AND curfew) AS takeoff_curfew, \
            SUM(landing AND curfew) AS landing_curfew \
            FROM flights WHERE time>{start_time} AND time<{end_time} \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        combo = True
        colors = ["DarkGreen", "DarkBlue", "DarkRed", "DarkOrange"]
        opes_title = "Mouvement"
        opes_label = (
            "Décollage jour",
            "Atterrissage jour",
            "Décollage couvre-feu",
            "Atterrissage couvre-feu",
        )

    elif type_graph == "CFZM":
        sql = f"SELECT airline, \
            SUM(NOT(north_fly OR curfew)) AS south, \
            SUM(north_fly AND NOT curfew) AS north, \
            SUM(NOT north_fly AND curfew) AS south_curfew, \
            SUM(north_fly AND curfew) AS north_curfew \
            FROM flights WHERE time>{start_time} AND time<{end_time} \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        combo = True
        colors = ["DarkGreen", "DarkBlue", "DarkRed", "DarkOrange"]
        opes_title = "Zone"
        opes_label = (
            "Sud jour",
            "Nord jour",
            "Sud couvre-feu",
            "Nord couvre-feu",
        )

    cursor.execute(sql)
    rows = cursor.fetchall()
    connection.close()
    airlines = []
    opes = []
    amount = []
    total_amout = [0, 0, 0, 0]

    for row in rows:
        airlines.append(row[0])
        airlines.append(row[0])
        opes.append(opes_label[0])
        opes.append(opes_label[1])
        amount.append(row[1])
        amount.append(row[2])
        total_amout[0] += row[1]
        total_amout[1] += row[2]
        if combo:
            airlines.append(row[0])
            airlines.append(row[0])
            opes.append(opes_label[2])
            opes.append(opes_label[3])
            amount.append(row[3])
            amount.append(row[4])
            total_amout[2] += row[3]
            total_amout[3] += row[4]

    df = pd.DataFrame({"Compagnies": airlines, "Nombre": amount, opes_title: opes})

    fig = px.bar(
        df,
        x="Compagnies",
        y="Nombre",
        color=opes_title,
        text_auto=True,
        height=600,
        color_discrete_sequence=colors,
    )
    if not combo:
        return (
            fig,
            total_amout[0],
            {"background-color": colors[0]},
            total_amout[1],
            {"background-color": colors[1]},
            "",
            {"background-color": "white"},
            "",
            {"background-color": "white"},
        )
    else:
        return (
            fig,
            total_amout[0],
            {"background-color": colors[0]},
            total_amout[1],
            {"background-color": colors[1]},
            total_amout[2],
            {"background-color": colors[2]},
            total_amout[3],
            {"background-color": colors[3]},
        )


if __name__ == "__main__":
    app.run_server(debug=True)
