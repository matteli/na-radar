from FlightRadar24.api import FlightRadar24API
import datetime
from time import sleep
import sqlite3
import argparse
import logging
from __init__ import __version__

na_airport = "47.3,47,-1.7,-1.5"
delay_dead = 600  # time in second without information for untrack plane
start_curfew = datetime.time(0, 0)
end_curfew = datetime.time(6, 0)
middle_curfew = datetime.time(3, 0)
fr_api = FlightRadar24API()
logging.basicConfig(filename="flights.log", encoding="utf-8", level=logging.INFO)
connection = sqlite3.connect("naflight.db")
cursor = connection.cursor()


class NAFlight:
    def __init__(
        self,
        registration,
        airline,
        origin_airport,
        destination_airport,
        status,
        time,
    ):
        self.registration = registration
        self.last_status = status  # 0 : inflight, 1 : onground
        self.time = time
        self.airline = airline
        self.origin_airport = origin_airport
        self.destination_airport = destination_airport

    def is_curfew_is_start(self, epoch_time):
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

    def check(self, status, time):
        if status != 0 and status != 1:
            return False

        if time - self.time > delay_dead:
            return False

        if status != self.last_status:
            curfew, start_curfew = self.is_curfew_is_start(time)
            self.last_status = status
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

            curfew, start_curfew = self.is_curfew_is_start(self.time)

            if curfew:
                sql = f'INSERT INTO flights VALUES ("{self.registration}", "{self.airline}", {self.operation}, "{self.origin_airport}", "{self.destination_airport}", {self.time}, {self.time_on_ground}, {self.time_in_flight}, 1);'
                cursor.execute(sql)
                connection.commit()
                logging.info(
                    # print(
                    f"L'avion {self.registration} de la compagnie {self.airline} qui a {'décollé' if self.operation==0 else 'atteri'} à {datetime.datetime.fromtimestamp(self.time).strftime('%H:%M:%S')} est hors délai."
                )
            else:
                sql = f'INSERT INTO flights VALUES ("{self.registration}", "{self.airline}", {self.operation}, "{self.origin_airport}", "{self.destination_airport}", {self.time}, {self.time_on_ground}, {self.time_in_flight}, 0);'
                cursor.execute(sql)
                connection.commit()
                logging.info(
                    # print(
                    f"L'avion {self.registration} de la compagnie {self.airline} qui a {'décollé' if self.operation==0 else 'atteri'} à {datetime.datetime.fromtimestamp(self.time).strftime('%H:%M:%S')} est ok."
                )
            return False

        self.time = time
        return True


def main():
    sql = "CREATE TABLE IF NOT EXISTS flights (registration TEXT, airline TEXT, operation INTEGER, origin_airport TEXT, destination_airport TEXT, time INTEGER, time_on_ground INTEGER, time_in_flight INTEGER, curfew INTEGER);"
    cursor.execute(sql)
    connection.commit()

    na_flights = {}
    while True:
        try:
            flights = fr_api.get_flights(None, na_airport)
        except:
            flights = []

        for flight in flights:
            if flight.id in list(na_flights.keys()):
                tracking = na_flights[flight.id].check(flight.on_ground, flight.time)
                if not tracking:
                    na_flights.pop(flight.id)
            else:
                try:
                    flight_detail = fr_api.get_flight_details(flight.id)
                except:
                    logging.warning(
                        "Avion ignoré par manque d'informations obligatoires"
                    )
                else:
                    if flight_detail:
                        try:
                            on_ground = flight.on_ground
                            time = flight.time
                            registration = flight_detail["aircraft"]["registration"]
                        except:
                            logging.warning(
                                "Avion ignoré par manque d'informations obligatoires"
                            )
                        else:
                            try:
                                airline_name = flight_detail["airline"]["name"]
                            except:
                                airline_name = "N/A"
                            try:
                                airport_origin = flight_detail["airport"]["origin"][
                                    "name"
                                ]
                            except:
                                airport_origin = "N/A"
                            try:
                                airport_destination = flight_detail["airport"][
                                    "destination"
                                ]["name"]
                            except:
                                airport_destination = "N/A"

                            na_flights[flight.id] = NAFlight(
                                registration,
                                airline_name,
                                airport_origin,
                                airport_destination,
                                on_ground,
                                time,
                            )

        sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="na-radar", description="Detect planes at NA airport"
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    args = parser.parse_args()
    main()
