from FlightRadar24.api import FlightRadar24API
import datetime
from time import sleep
import sqlite3
import argparse
import logging
from __init__ import __version__

NA_AIRPORT_ZONE = "47.3,47,-1.7,-1.5"
TRACK_ANGLE_LIMITS = (197, 117)
DELAY_DEAD = 600  # time in second without information for untrack plane
START_CURFEW = datetime.time(0, 0)
END_CURFEW = datetime.time(6, 0)
MIDDLE_CURFEW = datetime.time(3, 0)
CONNECTION = sqlite3.connect("naflights.db")
CURSOR = CONNECTION.cursor()


class NAFlight:
    def __init__(
        self,
        registration,
        airline,
        origin_airport,
        destination_airport,
        on_ground,
        heading,
        time,
    ):
        self.registration = registration
        self.on_ground = on_ground
        self.heading = heading
        self.time = time
        self.airline = airline
        self.origin_airport = origin_airport
        self.destination_airport = destination_airport

    def is_curfew_is_begin(self, epoch_time):
        time = datetime.datetime.fromtimestamp(epoch_time).time()
        if START_CURFEW < END_CURFEW:  # start curfew is after 00:00
            if time > START_CURFEW and time < END_CURFEW:
                if time < MIDDLE_CURFEW:
                    return True, True
                return True, False
        else:  # start curfew is before 00:00
            if time > START_CURFEW or time < END_CURFEW:
                if time < MIDDLE_CURFEW or (
                    MIDDLE_CURFEW > datetime.time(0, 0) and time > START_CURFEW
                ):
                    return True, True
                return True, False
        return False, False

    def get_curfew(self, epoch_time):
        time = datetime.datetime.fromtimestamp(epoch_time).time()
        if START_CURFEW < END_CURFEW:  # start curfew is after 00:00
            if time > START_CURFEW and time < END_CURFEW:
                return 1
        else:
            if time > START_CURFEW or time < END_CURFEW:
                return 1
        return 0

    def get_north_fly(self, heading, landing):
        if heading > TRACK_ANGLE_LIMITS[0] or heading < TRACK_ANGLE_LIMITS[1]:
            if landing:
                return 0
            else:
                return 1
        else:
            if landing:
                return 1
            else:
                return 0

    def check(self, on_ground, time, heading):
        if on_ground != 0 and on_ground != 1:
            return False

        if time - self.time > DELAY_DEAD:
            return False

        if on_ground != self.on_ground:
            time_curfew, begin_curfew = self.is_curfew_is_begin(time)
            self.on_ground = on_ground
            if on_ground == 0:  # plane take off from NA
                landing = 0
                north_fly = self.get_north_fly(self.heading, landing)
                time_on_ground = self.time
                time_in_flight = time
                if not begin_curfew or not time_curfew:
                    self.time = time

            else:  # plane land at NA
                landing = 1
                north_fly = self.get_north_fly(heading, landing)
                time_in_flight = self.time
                time_on_ground = time
                if begin_curfew or not time_curfew:
                    self.time = time

            curfew = self.get_curfew(self.time)

            sql = f'INSERT INTO flights VALUES ("{self.registration}", "{self.airline}", {landing}, "{self.origin_airport}", "{self.destination_airport}", {self.time}, {time_on_ground}, {time_in_flight}, {curfew}, {north_fly});'
            CURSOR.execute(sql)
            CONNECTION.commit()
            logging.info(
                # print(
                f"L'avion {self.registration} de la compagnie {self.airline} a {'atteri' if landing else 'décollé'} côté {'nord' if north_fly else 'sud'} à {datetime.datetime.fromtimestamp(self.time).strftime('%H:%M:%S')}{' pendant le couvre-feu.' if curfew else '.'}"
            )

            return False

        self.time = time
        self.heading = heading
        return True


def main():
    logging.basicConfig(filename="flights.log", encoding="utf-8", level=logging.INFO)

    sql = "CREATE TABLE IF NOT EXISTS flights (registration TEXT, airline TEXT, landing INTEGER, origin_airport TEXT, destination_airport TEXT, time INTEGER, time_on_ground INTEGER, time_in_flight INTEGER, curfew INTEGER, north_fly INTEGER);"
    CURSOR.execute(sql)
    CONNECTION.commit()

    na_flights = {}
    while True:
        try:
            flights = FlightRadar24API().get_flights(None, NA_AIRPORT_ZONE)
        except:
            flights = []

        for flight in flights:
            if flight.id in list(na_flights.keys()):
                tracking = na_flights[flight.id].check(
                    flight.on_ground, flight.time, flight.heading
                )
                if not tracking:
                    na_flights.pop(flight.id)
            else:
                try:
                    flight_detail = FlightRadar24API().get_flight_details(flight.id)
                except:
                    logging.warning(
                        "Avion ignoré par manque d'informations obligatoires"
                    )
                else:
                    if flight_detail:
                        try:
                            on_ground = flight.on_ground
                            time = flight.time
                            heading = flight.heading
                            registration = flight_detail["aircraft"]["registration"]
                        except:
                            logging.warning(
                                "Avion ignoré par manque d'informations obligatoires"
                            )
                        else:
                            try:
                                airline_name = flight_detail["airline"]["short"]
                            except:
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
                                heading,
                                time,
                            )

        sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="NA-Radar", description="Detect planes at NA airport"
    )
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )

    args = parser.parse_args()
    main()
