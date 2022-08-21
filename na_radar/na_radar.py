from FlightRadar24.api import FlightRadar24API
import datetime
from time import sleep
import sqlite3
import argparse
import logging
from __init__ import __version__

AIRPORT_ZONE = "47.19,47.11,-1.65,-1.57"
TRACK_ANGLE_LIMITS = (297, 117)
START_CURFEW = datetime.time(0, 0)
END_CURFEW = datetime.time(6, 0)
MIDDLE_CURFEW = datetime.time(3, 0)
MAX_ALTITUDE_TESTING_HEADING = 1000  # in feet
MIN_GROUND_SPEED_TESTING_HEADING = 40  # in knots
DELAY_DEAD = 600  # time in second without information for untrack plane
CONNECTION = sqlite3.connect("flights.db")
CURSOR = CONNECTION.cursor()


class AirportFlight:
    def __init__(
        self,
        registration,
        airline,
        origin_airport,
        destination_airport,
        on_ground,
        heading,
        altitude,
        ground_speed,
        time,
    ):
        self.registration = registration
        self.on_ground = on_ground
        self.heading = heading
        self.altitude = altitude
        self.ground_speed = ground_speed
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

    def get_north_fly(
        self,
        landing,
        heading_0,
        heading_1,
        altitude_0,
        altitude_1,
        ground_speed_0,
        ground_speed_1,
    ):
        def test_heading(heading, landing):
            if heading > TRACK_ANGLE_LIMITS[0] or heading < TRACK_ANGLE_LIMITS[1]:
                if landing:
                    return 0  # south_fly
                else:
                    return 1  # north_fly
            else:
                if landing:
                    return 1  # north_fly
                else:
                    return 0  # south_fly

        north_0 = test_heading(heading_0, landing)
        north_1 = test_heading(heading_1, landing)
        if north_0 == north_1:
            return north_0
        if landing:
            if altitude_0 < MAX_ALTITUDE_TESTING_HEADING:
                return north_0
            elif ground_speed_1 > MIN_GROUND_SPEED_TESTING_HEADING:
                return north_1
            else:
                return -1
        else:
            if altitude_1 < MAX_ALTITUDE_TESTING_HEADING:
                return north_1
            elif ground_speed_0 > MIN_GROUND_SPEED_TESTING_HEADING:
                return north_0
            else:
                return -1

    def check(self, on_ground, time, heading, altitude, ground_speed):
        if on_ground != 0 and on_ground != 1:
            return False

        if time - self.time > DELAY_DEAD:
            return False

        if on_ground != self.on_ground:
            time_curfew, begin_curfew = self.is_curfew_is_begin(time)
            self.on_ground = on_ground

            if on_ground == 0:  # plane take off from NA
                landing = 0
                time_on_ground = self.time
                time_in_flight = time
                if not begin_curfew or not time_curfew:
                    self.time = time

            else:  # plane land at NA
                landing = 1
                time_in_flight = self.time
                time_on_ground = time
                if begin_curfew or not time_curfew:
                    self.time = time

            north_fly = self.get_north_fly(
                landing,
                self.heading,
                heading,
                self.altitude,
                altitude,
                self.ground_speed,
                ground_speed,
            )
            curfew = self.get_curfew(self.time)

            sql = f'INSERT INTO flights VALUES ("{self.registration}", "{self.airline}", {landing}, "{self.origin_airport}", "{self.destination_airport}", {self.time}, {time_on_ground}, {time_in_flight}, {curfew}, {north_fly});'
            CURSOR.execute(sql)
            CONNECTION.commit()
            logging.info(
                f"L'avion {self.registration} de la compagnie {self.airline} a {'atteri' if landing else 'décollé'} {'côté nord' if north_fly==1 else 'côté sud' if north_fly==0 else 'un côté indéterminé'} à {datetime.datetime.fromtimestamp(self.time).strftime('%H:%M:%S')}{' pendant le couvre-feu.' if curfew else '.'}"
            )
            return False

        self.time = time
        self.heading = heading
        self.altitude = altitude
        self.ground_speed = ground_speed
        return True


def main():
    logging.basicConfig(filename="flights.log", encoding="utf-8", level=logging.INFO)

    sql = "CREATE TABLE IF NOT EXISTS flights (registration TEXT, airline TEXT, landing INTEGER, origin_airport TEXT, destination_airport TEXT, time INTEGER, time_on_ground INTEGER, time_in_flight INTEGER, curfew INTEGER, north_fly INTEGER);"
    CURSOR.execute(sql)
    CONNECTION.commit()

    airport_flights = {}
    while True:
        try:
            flights = FlightRadar24API().get_flights(None, AIRPORT_ZONE)
        except:
            flights = []

        for flight in flights:
            try:
                id = flight.id
                on_ground = flight.on_ground
                time = flight.time
                heading = flight.heading
                altitude = flight.altitude
                ground_speed = flight.ground_speed
            except:
                logging.warning(
                    "Position ignorée par manque d'informations obligatoires"
                )

            if id in list(airport_flights.keys()):
                tracking = airport_flights[id].check(
                    on_ground,
                    time,
                    heading,
                    altitude,
                    ground_speed,
                )
                if not tracking:
                    airport_flights.pop(id)
            else:
                try:
                    flight_detail = FlightRadar24API().get_flight_details(id)
                except:
                    logging.warning(
                        "Avion ignoré par manque d'informations obligatoires"
                    )
                else:
                    try:
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
                            airport_origin = flight_detail["airport"]["origin"]["name"]
                        except:
                            airport_origin = "N/A"
                        try:
                            airport_destination = flight_detail["airport"][
                                "destination"
                            ]["name"]
                        except:
                            airport_destination = "N/A"

                        airport_flights[flight.id] = AirportFlight(
                            registration,
                            airline_name,
                            airport_origin,
                            airport_destination,
                            on_ground,
                            heading,
                            altitude,
                            ground_speed,
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
