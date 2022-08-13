from xml.dom import registerDOMImplementation
from FlightRadar24.api import FlightRadar24API
import datetime
from time import sleep
import sqlite3
import argparse
import logging
from collections import defaultdict
from __init__ import __version__

na_airport = "47.3,47,-1.7,-1.5"
delay_dead = 600  # time in second without information for untrack plane
start_curfew = datetime.time(15, 5)
end_curfew = datetime.time(6, 0)
middle_curfew = datetime.time(22, 0)
fr_api = FlightRadar24API()
logging.basicConfig(filename="flights.log", encoding="utf-8", level=logging.INFO)
connection = sqlite3.connect("naflight.db")
cursor = connection.cursor()

airlines_iata = {}


def is_curfew_is_start(epoch_time):
    time = datetime.datetime.fromtimestamp(epoch_time).time()
    if start_curfew < end_curfew:  # start curfew is after 00:00
        if time > start_curfew and time < end_curfew:
            if time < middle_curfew:
                return True, True
            return True, False
    else:  # start curfew is before 00:00
        if time > start_curfew or time < end_curfew:
            if time < middle_curfew or (
                middle_curfew > datetime.time(0, 0) and time > start_curfew
            ):
                return True, True
            return True, False
    return False, False


class NAFlight:
    def __init__(
        self,
        registration,
        airline_iata,
        origin_airport_iata,
        destination_airport_iata,
        status,
        time,
    ):
        self.registration = registration
        self.last_status = status  # 0 : inflight, 1 : onground
        self.time = time
        self.outlaw = False
        self.tracked = True
        self.airline_iata = airline_iata
        self.origin_airport_iata = origin_airport_iata
        self.destination_airport_iata = destination_airport_iata

    def check(self, status, time):
        if status != 0 and status != 1:
            self.tracked = False
            return False

        if time - self.time > delay_dead:
            self.tracked = False
            return False

        if status != self.last_status:
            curfew, start_curfew = is_curfew_is_start(time)
            self.last_status = status
            self.tracked = False
            if status == 0:  # plane take off from NA
                self.operation = 0
                self.time_on_ground = self.time
                self.time_in_flight = time
                if not start_curfew or not curfew:
                    self.time = time

            else:  # plane land at NA
                self.operation = 1
                self.time_in_flight = self.time
                self.time_on_ground = time
                if start_curfew or not curfew:
                    self.time = time

            curfew, start_curfew = is_curfew_is_start(self.time)

            try:
                airline = airlines_iata[self.airline_iata]
            except KeyError:
                if "airlines_fr" not in locals():
                    airlines_fr = fr_api.get_airlines()
                airline = "inconnue"
                for airline_fr in airlines_fr:
                    if airline_fr["Code"] == self.airline_iata:
                        airlines_iata[self.airline_iata] = airline_fr["Name"]
                        airline = airline_fr["Name"]
                        break

            if curfew:
                sql = f"INSERT INTO flights VALUES ('{self.registration}', '{self.airline_iata}', {self.operation}, '{self.origin_airport_iata}', '{self.destination_airport_iata}', {self.time},{self.time_on_ground}, {self.time_in_flight}, 1);"
                cursor.execute(sql)
                connection.commit()
                logging.info(
                    # print(
                    f"L'avion {self.registration} de la compagnie {airline} qui a {'décollé' if self.operation==0 else 'atteri'} à {datetime.datetime.fromtimestamp(self.time).strftime('%H:%M:%S')} est hors délai."
                )
            else:
                sql = f"INSERT INTO flights VALUES ('{self.registration}', '{self.airline_iata}', {self.operation}, '{self.origin_airport_iata}', '{self.destination_airport_iata}', {self.time},{self.time_on_ground}, {self.time_in_flight}, 0);"
                cursor.execute(sql)
                connection.commit()
                logging.info(
                    # print(
                    f"L'avion {self.registration} de la compagnie {airline} qui a {'décollé' if self.operation==0 else 'atteri'} à {datetime.datetime.fromtimestamp(self.time).strftime('%H:%M:%S')} est ok."
                )

        else:
            self.time = time
        return


def main(what):
    if what == "detect":
        sql = "CREATE TABLE IF NOT EXISTS flights (registration TEXT, airline_iata TEXT, operation INTEGER, origin_airport_iata TEXT, destination_airport_iata TEXT, time INTEGER, time_on_ground INTEGER, time_in_flight INTEGER, curfew INTEGER);"
        cursor.execute(sql)
        connection.commit()

        na_flights = {}
        while True:
            flights = fr_api.get_flights(None, na_airport)
            for flight in flights:
                if flight.id in list(na_flights.keys()):
                    if na_flights[flight.id].tracked:
                        na_flights[flight.id].check(
                            flight.on_ground,
                            flight.time,
                        )
                else:
                    na_flights[flight.id] = NAFlight(
                        flight.registration,
                        flight.airline_iata,
                        flight.origin_airport_iata,
                        flight.destination_airport_iata,
                        flight.on_ground,
                        flight.time,
                    )

            sleep(10)
    elif what == "get":
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="na-radar", description="Count and detecte planes at na airport"
    )
    parser.add_argument("what", choices=["detect", "get"], help="detect or get")
    parser.add_argument("-v", "--version", action="version", version=__version__)

    args = parser.parse_args()
    main(what=args.what)
