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


class CodeIATA:
    def __init__(self):
        self.codes_iata_fr = []
        self.codes_iata = {}
        self.get_codes_iata_fr()

    def get_codes_iata_fr(self):
        try:
            self.codes_iata_fr += fr_api.get_airlines()
            self.codes_iata_fr += fr_api.get_airports()
            return True
        except:
            return False

    def iata_2_name(self, code_iata):
        try:
            name = self.codes_iata[code_iata]
        except KeyError:
            if not self.codes_iata_fr:
                self.get_codes_iata_fr()
            name = code_iata
            for code_iata_fr in self.codes_iata_fr:
                try:
                    if code_iata_fr["Code"] == code_iata:
                        self.codes_iata[code_iata] = code_iata_fr["Name"]
                        name = code_iata_fr["Name"]
                        break
                except KeyError:
                    if code_iata_fr["iata"] == code_iata:
                        self.codes_iata[code_iata] = code_iata_fr["name"]
                        name = code_iata_fr["name"]
                        break
        return name


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

    def check(self, status, time, code_iata):
        if status != 0 and status != 1:
            self.tracked = False
            return False

        if time - self.time > delay_dead:
            self.tracked = False
            return False

        if status != self.last_status:
            curfew, start_curfew = self.is_curfew_is_start(time)
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

            curfew, start_curfew = self.is_curfew_is_start(self.time)

            airline = code_iata.iata_2_name(self.airline_iata)
            origin_airport = code_iata.iata_2_name(self.origin_airport_iata)
            destination_airport = code_iata.iata_2_name(self.destination_airport_iata)

            if curfew:
                sql = f'INSERT INTO flights VALUES ("{self.registration}", "{airline}", {self.operation}, "{origin_airport}", "{destination_airport}", {self.time}, {self.time_on_ground}, {self.time_in_flight}, 1);'
                cursor.execute(sql)
                connection.commit()
                # logging.info(
                print(
                    f"L'avion {self.registration} de la compagnie {airline} qui a {'décollé' if self.operation==0 else 'atteri'} à {datetime.datetime.fromtimestamp(self.time).strftime('%H:%M:%S')} est hors délai."
                )
            else:
                sql = f'INSERT INTO flights VALUES ("{self.registration}", "{airline}", {self.operation}, "{origin_airport}", "{destination_airport}", {self.time}, {self.time_on_ground}, {self.time_in_flight}, 0);'
                cursor.execute(sql)
                connection.commit()
                # logging.info(
                print(
                    f"L'avion {self.registration} de la compagnie {airline} qui a {'décollé' if self.operation==0 else 'atteri'} à {datetime.datetime.fromtimestamp(self.time).strftime('%H:%M:%S')} est ok."
                )

        else:
            self.time = time
        return


def main():
    sql = "CREATE TABLE IF NOT EXISTS flights (registration TEXT, airline TEXT, operation INTEGER, origin_airport_iata TEXT, destination_airport_iata TEXT, time INTEGER, time_on_ground INTEGER, time_in_flight INTEGER, curfew INTEGER);"
    cursor.execute(sql)
    connection.commit()
    code_iata = CodeIATA()

    na_flights = {}
    while True:
        try:
            flights = fr_api.get_flights(None, na_airport)
        except:
            flights = []

        for flight in flights:
            if flight.id in list(na_flights.keys()):
                if na_flights[flight.id].tracked:
                    na_flights[flight.id].check(
                        flight.on_ground, flight.time, code_iata
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="na-radar", description="Count and detecte planes at na airport"
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    args = parser.parse_args()
    main()
