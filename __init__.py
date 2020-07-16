from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
import requests
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

            if query is not None:
                ozone = query[0]["Category"]["Name"]
                particulates = query[1]["Category"]["Name"]
                self.speak_dialog("particulates are {0} and ozone is {1}".format(particulates, ozone))
            else:
                self.speak_dialog("something went wrong")

    def get_air_quality(self):
        PARAMS = {"latitude": self.lat,
                  "longitude": self.lon,
                  "date": datetime.datetime.today().strftime('%Y-%m-%d'),  # Today
                  "distance": 25,
                  "API_KEY": self.api_key}

        response = requests.get(url=URL, params=PARAMS, timeout=3)

        try:
            response.raise_for_status()
            return response.json()
        except Exception as error:
            self.log.debut(error)
            return None

def create_skill():
    return AirQualityIndex()
