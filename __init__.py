from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
import json
import requests
import os
import time
import datetime

"""
    This skill uses the AirNow (https://docs.airnowapi.org/) 
    Specifically, The Lat/Lon API (https://docs.airnowapi.org/forecastsbylatlon/docs)
"""

# Request URL
URL = "http://www.airnowapi.org/aq/forecast/latLong/?format=application/json"


class AirQualityIndex(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.api_key = self.settings.get('api_key')

        loc = self.location

        self.lat = loc['coordinate']['latitude']
        self.lon = loc['coordinate']['longitude']

    @intent_handler('index.quality.air.intent')
    def handle_index_quality_air(self, message):

        if self.api_key is None:
            self.speak_dialog("API Key Not Set")
        else:
            query = self.get_air_quality()
            if query is list:
                ozone = query[0]["Category"]["Name"]
                particulates = query[1]["Category"]["Name"]
                self.speak_dialog("particulates are {0} and ozone is {1}".format(particulates, ozone))
            else:
                self.speak_dialog("data could not be found")

    # Returns dict of data from the AirNow Api
    # Reuses Previous Data If Time Since Last Use Is Less Than 30 Min
    def get_air_quality(self):
        # If Most Recent Usage Was Within 30 Minutes, Use That Data
        try:
            minutes = int(time.strftime('%M', time.localtime(os.path.getmtime("data.json"))))
            if minutes < 60:
                with open("data.json") as file:
                    return json.load(file)

        # Perhaps There's No File Yet, Maybe It's Not A Valid Json Either Way, Get New Data
        except Exception as err:
            self.log.exception(f"Error Occurred: {err}")

        PARAMS = {"latitude": self.lat,
                  "longitude": self.lon,
                  "date": datetime.datetime.today().strftime('%Y-%m-%d'),  # Today
                  "distance": 25,
                  "API_KEY": self.api_key}

        try:
            response = requests.get(url=URL, params=PARAMS, timeout=3)
            response.raise_for_status()  # Raises HTTP Error If Something Went Wrong

        except requests.HTTPError as http_err:
            self.log.exception(f"HTTP error occurred: {http_err}")
            return None

        except Exception as err:
            self.log.exception(f"Other error occurred: {err}")
            return None

        else:
            try:
                # Try To Save File To Reduce Potential API Calls
                with open("data.json", "w") as file:
                    file.write(json.dumps(response.json()))

            except Exception as err:
                self.log.exception(f"JSON write error occurred: {err}")
                pass

            # Returns The Dictionary
            return response.json()

    def stop(self):
        pass


def create_skill():
    return AirQualityIndex()
