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
    end_date = datetime.date.today().isoformat()
    type_graph = "CM"
    airlines, amounts, total_amount, colors, order, title, anchor_legend = get_data(
        start_date, end_date, type_graph
    )

    return render_template(
        "dash.html",
        airlines=json.dumps(airlines),
        amounts=json.dumps(amounts),
        total_amount=json.dumps(total_amount),
        colors=json.dumps(colors),
        order=json.dumps(order),
        title=title,
        start_date=start_date,
        end_date=end_date,
        type_graph=type_graph,
        anchor_legend=anchor_legend,
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
    if start_date != "" and r_date.match(start_date) is None:
        return "Mauvais format de date", 400
    if end_date != "" and r_date.match(end_date) is None:
        return "Mauvais format de date", 400

    r_type_graph = re.compile("^(CM|H|Z|MH|MZ)$")
    if r_type_graph.match(type_graph) is None:
        return "Type de graphique inconnu", 400

    airlines, amounts, total_amount, colors, order, title, anchor_legend = get_data(
        start_date, end_date, type_graph
    )
    return {
        "airlines": airlines,
        "amounts": amounts,
        "total_amount": total_amount,
        "colors": colors,
        "order": order,
        "title": title,
        "anchor_legend": anchor_legend,
    }


def get_data(start_date, end_date, type_graph):
    try:
        start_time = int(datetime.datetime.fromisoformat(start_date).timestamp())
    except ValueError:
        start_time = int(datetime.datetime.fromisoformat(START_DATE).timestamp())

    try:
        end_time = int(datetime.datetime.fromisoformat(end_date).timestamp()) + 86400
    except ValueError:
        end_time = int(
            datetime.datetime.fromisoformat(
                (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
            ).timestamp()
        )

    connection = sqlite3.connect("flights.db")
    cursor = connection.cursor()

    if type_graph == "CM":
        sql = f"SELECT airline, \
            sum(NOT landing AND curfew) AS takeoff_curfew, \
            sum(landing AND curfew) AS landing_curfew \
            FROM flights \
            WHERE retained_time>{start_time} AND retained_time<{end_time} \
            GROUP BY airline \
            ORDER BY (takeoff_curfew + landing_curfew) DESC, count(airline) DESC LIMIT 10;"

        nb_bars = 2
        colors = {
            "Décollage pendant le couvre-feu": "DarkRed",
            "Atterrissage pendant le couvre-feu": "DarkOrange",
        }
        order = [
            "Décollage pendant le couvre-feu",
            "Atterrissage pendant le couvre-feu",
        ]
        title = "Nombre d'avions par compagnie décollant ou atterrissant pendant le couvre-feu (de 0h à 6h)"
        anchor_legend = "right"

    elif type_graph == "H":
        sql = f"SELECT airline, \
            sum(NOT curfew) AS not_curfew, \
            sum(curfew) AS curfew \
            FROM flights \
            WHERE retained_time>{start_time} AND retained_time<{end_time} \
            GROUP BY airline \
            ORDER BY count(airline) DESC LIMIT 10;"

        nb_bars = 2
        colors = {"Jour": "DarkGreen", "Couvre-feu": "DarkRed"}
        order = [
            "Jour",
            "Couvre-feu",
        ]
        title = "Nombre de mouvements d'avions par compagnie pendant le couvre-feu (de 0h à 6h) ou le reste de la journée"
        anchor_legend = "right"

    elif type_graph == "MH":
        sql = f"SELECT airline, \
            sum(NOT(landing OR curfew)) AS takeoff, \
            sum(landing AND NOT curfew) AS landing, \
            sum(NOT landing AND curfew) AS takeoff_curfew, \
            sum(landing AND curfew) AS landing_curfew \
            FROM flights \
            WHERE retained_time>{start_time} AND retained_time<{end_time} \
            GROUP BY airline \
            ORDER BY count(airline) DESC LIMIT 10;"

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
        title = "Nombre d'avions par compagnie décollant ou atterrissant pendant le couvre-feu (de 0h à 6h) ou le reste de la journée"
        anchor_legend = "right"

    elif type_graph == "Z":
        sql = f"SELECT substr(time(retained_time, 'unixepoch', 'localtime'), 1,2) || ':00' AS hour, \
	        sum(NOT(north_fly)) AS south_fly \
	        sum(north_fly) AS north_fly, \
	        FROM flights \
            WHERE retained_time>{start_time} AND retained_time<{end_time} AND north_fly>=0 \
	        GROUP BY hour \
            ORDER BY hour;"

        nb_bars = 2
        colors = {"Sud": "DarkRed", "Nord": "DarkOrange"}
        order = [
            "Sud",
            "Nord",
        ]
        title = "Nombre de mouvements d'avions par heure par le sud ou par le nord"
        anchor_legend = "left"

    elif type_graph == "MZ":
        sql = f"SELECT substr(time(retained_time, 'unixepoch', 'localtime'), 1,2) || ':00' AS hour, \
            sum(NOT(north_fly OR landing)) AS south_takeoff, \
            sum(NOT north_fly AND landing) AS south_landing, \
            sum(north_fly AND NOT landing) AS north_takeoff, \
            sum(north_fly AND landing) AS north_landing \
            FROM flights \
            WHERE retained_time>{start_time} AND retained_time<{end_time} AND north_fly>=0 \
            GROUP BY hour \
            ORDER BY hour;"

        nb_bars = 4
        colors = {
            "Décollage sud": "DarkRed",
            "Atterrissage sud": "DarkOrange",
            "Décollage nord": "DarkGreen",
            "Atterrissage nord": "DarkBlue",
        }
        order = [
            "Décollage sud",
            "Atterrissage sud",
            "Décollage nord",
            "Atterrissage nord",
        ]
        title = "Nombre d'avions par heure décollant ou atterrissant par le sud ou par le nord"
        anchor_legend = "left"

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
        total_amount[0] += row[1]
        if nb_bars >= 2:
            amounts[order[1]].append(row[2])
            total_amount[1] += row[2]
        if nb_bars >= 4:
            amounts[order[2]].append(row[3])
            amounts[order[3]].append(row[4])
            total_amount[2] += row[3]
            total_amount[3] += row[4]

    return airlines, amounts, total_amount, colors, order, title, anchor_legend


if __name__ == "__main__":
    app.run_server(debug=True)
