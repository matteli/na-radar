from flask import Flask, render_template, request
import sqlite3
import datetime
import json
import re

START_DATE = "2022-08-19"

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    start_date = START_DATE
    end_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    type_graph = "H"
    airlines, amounts, total_amount, colors, order = get_data(
        start_date, end_date, type_graph
    )

    return render_template(
        "dash.html",
        airlines=json.dumps(airlines),
        amounts=json.dumps(amounts),
        total_amount=json.dumps(total_amount),
        colors=json.dumps(colors),
        order=json.dumps(order),
        start_date=start_date,
        end_date=end_date,
        type_graph=type_graph,
    )


@app.route("/help", methods=["GET"])
def help():
    return render_template("help.html")


@app.route("/graph", methods=["POST"])
def update_graph():
    if request.is_json:
        start_date = request.json.get("start_date")
        end_date = request.json.get("end_date")
        type_graph = request.json.get("type_graph")

    r_date = re.compile("^(\d\d\d\d-\d\d-\d\d)$")
    if r_date.match(start_date) is None:
        return "Mauvais format de date", 400
    if r_date.match(end_date) is None:
        return "Mauvais format de date", 400

    r_type_graph = re.compile("^(H|Z|MH|ZH)$")
    if r_type_graph.match(type_graph) is None:
        return "Type de graphique inconnu", 400

    airlines, amounts, total_amount, colors, order = get_data(
        start_date, end_date, type_graph
    )
    return {
        "airlines": airlines,
        "amounts": amounts,
        "total_amount": total_amount,
        "colors": colors,
        "order": order,
    }


def get_data(start_date, end_date, type_graph):
    try:
        start_time = int(datetime.datetime.fromisoformat(start_date).timestamp())
    except ValueError:
        start_time = int(datetime.datetime.fromisoformat(START_DATE).timestamp())

    try:
        end_time = int(datetime.datetime.fromisoformat(end_date).timestamp())
    except ValueError:
        end_time = int(
            datetime.datetime.fromisoformat(
                (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
            ).timestamp()
        )

    connection = sqlite3.connect("flights.db")
    cursor = connection.cursor()

    if type_graph == "H":
        sql = f"SELECT airline, \
            SUM(NOT curfew) AS not_curfew, \
            SUM(curfew) AS curfew \
            FROM flights WHERE time>{start_time} AND time<{end_time} \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        nb_bars = 2
        colors = {"Jour": "DarkGreen", "Couvre-feu": "DarkRed"}
        order = [
            "Jour",
            "Couvre-feu",
        ]

    elif type_graph == "Z":
        sql = f"SELECT airline, \
            SUM(NOT north_fly) AS south_fly, \
            SUM(north_fly) AS north_fly \
            FROM flights \
            WHERE time>{start_time} AND time<{end_time} AND north_fly>=0 \
            GROUP BY airline ORDER BY COUNT(airline) DESC LIMIT 10;"

        nb_bars = 2
        colors = {"Sud": "DarkRed", "Nord": "DarkOrange"}
        order = [
            "Sud",
            "Nord",
        ]

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
        colors = {
            "Décollage jour": "DarkGreen",
            "Atterrissage jour": "DarkBlue",
            "Décollage couvre-feu": "DarkRed",
            "Atterrissage couvre-feu": "DarkOrange",
        }
        order = [
            "Décollage jour",
            "Atterrissage jour",
            "Décollage couvre-feu",
            "Atterrissage couvre-feu",
        ]

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
        colors = {
            "Sud jour": "DarkGreen",
            "Nord jour": "DarkBlue",
            "Sud couvre-feu": "DarkRed",
            "Nord couvre-feu": "DarkOrange",
        }
        order = [
            "Sud jour",
            "Nord jour",
            "Sud couvre-feu",
            "Nord couvre-feu",
        ]

    cursor.execute(sql)
    rows = cursor.fetchall()
    connection.close()
    airlines = []
    amounts = {}
    total_amount = [0, 0, 0, 0]

    for o in order:
        amounts[o] = []

    for row in rows:
        airlines.append(row[0])
        amounts[order[0]].append(row[1])
        amounts[order[1]].append(row[2])
        total_amount[0] += row[1]
        total_amount[1] += row[2]
        if nb_bars == 4:
            amounts[order[2]].append(row[3])
            amounts[order[3]].append(row[4])
            total_amount[2] += row[3]
            total_amount[3] += row[4]

    return airlines, amounts, total_amount, colors, order


if __name__ == "__main__":
    app.run_server(debug=True)
