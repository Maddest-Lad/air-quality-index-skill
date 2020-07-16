from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from datetime import datetime, timedelta
import json
import requests
import os
import time

"""
    This skill uses the AirNow (https://docs.airnowapi.org/) 
    Specifically, The Lat/Lon API (https://docs.airnowapi.org/forecastsbylatlon/docs)
"""

URL = "http://www.airnowapi.org/aq/forecast/latLong/?format=application/json"
api_key = "19C1A418-EFC9-4FC5-A58C-9E62C29DBBE9" # REMOVE AFTER TESTING
distance = 25  # How far the from the lat/long airnow will check
last_request = None


class AirQualityIndex(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_handler('index.quality.air.intent')
    def handle_index_quality_air(self, message):
        self.speak_dialog('index.quality.air')

    # Returns dict of data from the AirNow Api
    def get_air_quality(self, lat, long) -> dict:
        # If Most Recent Usage Was Within 30 Minutes, Use That Data
        try:
            minutes = int(time.strftime('%M', time.localtime(os.path.getmtime("data.json"))))
            if minutes < 60:
                with open("data.json") as file:
                    return json.load(file)

        # Perhaps There's No File Yet, Maybe It's Not A Valid Json Either Way, Get New Data
        except:
            pass

        PARAMS = {"latitude": lat,
                  "longitude": long,
                  "distance": distance,
                  "API_KEY": api_key}

        try:
            response = requests.get(url=URL, params=PARAMS, timeout=3).json()
            response.raise_for_status()  # Raises HTTP Error If Something Went Wrong

        except requests.HTTPError as http_err:
            self.log.exception(f"HTTP error occurred: {http_err}")  # Replace With Mycroft LOG

        except Exception as err:
            self.log.exception(f"Other error occurred: {err}")  # Replace With Mycroft LOG

        else:
            try:
                # Try To Save File To Reduce Potential API Calls
                with open("data.json", "w") as file:
                    file.write(json.dumps(response))

            except Exception as err:
                self.log.exception(f"JSON write error occurred: {err}")
                pass

            # Returns The Dictionary
            return json.load(response)

def create_skill():
    return AirQualityIndex()

