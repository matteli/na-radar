from flask import Flask, render_template
import sqlite3
import datetime
import json

START_DATE = datetime.date(2022, 8, 19)

app = Flask(__name__)
# application = app.server


@app.route("/")
def update_graph(start_date="2022-08-15", end_date="", type_graph="H"):
    start_time = int(datetime.datetime.fromisoformat(start_date).timestamp())
    if end_date:
        end_time = int(datetime.datetime.fromisoformat(end_date).timestamp())
    else:
        end_time = int(datetime.datetime.today().timestamp()) + 100000

    connection = sqlite3.connect("flights.db")
    cursor = connection.cursor()

    if type_graph == "H":
        sql = f"SELECT airline, \
            SUM(NOT curfew) AS not_curfew, \
            SUM(curfew) AS curfew \
            FROM flights WHERE time>{start_time} AND time<{end_time} \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        nb_bars = 2
        colors = ["DarkGreen", "DarkRed"]
        opes_title = "Plage horaire"
        opes_label = (
            "Jour",
            "Couvre-feu",
        )

    elif type_graph == "Z":
        sql = f"SELECT airline, \
            SUM(NOT north_fly) AS south_fly, \
            SUM(north_fly) AS north_fly \
            FROM flights \
            WHERE time>{start_time} AND time<{end_time} AND north_fly>=0 \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        nb_bars = 2
        colors = ["DarkRed", "DarkOrange"]
        opes_title = "Zone"
        opes_label = (
            "Sud",
            "Nord",
        )

    elif type_graph == "MH":
        sql = f"SELECT airline, \
            SUM(NOT(landing OR curfew)) AS takeoff, \
            SUM(landing AND NOT curfew) AS landing, \
            SUM(NOT landing AND curfew) AS takeoff_curfew, \
            SUM(landing AND curfew) AS landing_curfew \
            FROM flights \
            WHERE time>{start_time} AND time<{end_time} \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        nb_bars = 4
        colors = ["DarkGreen", "DarkBlue", "DarkRed", "DarkOrange"]
        opes_title = "Mouvement"
        opes_label = (
            "Décollage jour",
            "Atterrissage jour",
            "Décollage couvre-feu",
            "Atterrissage couvre-feu",
        )

    elif type_graph == "ZH":
        sql = f"SELECT airline, \
            SUM(NOT(north_fly OR curfew)) AS south, \
            SUM(north_fly AND NOT curfew) AS north, \
            SUM(NOT north_fly AND curfew) AS south_curfew, \
            SUM(north_fly AND curfew) AS north_curfew \
            FROM flights \
            WHERE time>{start_time} AND time<{end_time} AND north_fly>=0 \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        nb_bars = 4
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
    amounts = {}
    total_amout = [0, 0, 0, 0]

    for o in opes_label:
        amounts[o] = []

    for row in rows:
        airlines.append(row[0])
        amounts[opes_label[0]].append(row[1])
        amounts[opes_label[1]].append(row[2])
        total_amout[0] += row[1]
        total_amout[1] += row[2]
        if nb_bars == 4:
            amounts[opes_label[0]].append(row[3])
            amounts[opes_label[0]].append(row[4])
            total_amout[2] += row[3]
            total_amout[3] += row[4]

    return render_template(
        "dash.html",
        airlines=json.dumps(airlines),
        amounts=json.dumps(amounts),
        total_amout=json.dumps(total_amout),
    )


if __name__ == "__main__":
    app.run_server(debug=True)
