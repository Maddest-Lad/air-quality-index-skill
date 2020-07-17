from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from dateutil.utils import today
from collections import Counter, defaultdict
import requests

"""
    A Skill to return the daily air quality parameters 
    TODO: figure out how to handle x days from now

    This skill uses the data from the World Air Quality Project (https://aqicn.org/api/) 
    Specifically, The Geo-Localized Feed (https://aqicn.org/json-api/doc/#api-Geolocalized_Feed-GetGeolocFeed)
"""

base_url = "https://api.waqi.info/feed/"


class AirQualityIndex(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

        self.api_key = self.settings.get('api_key')

        # Mycroft Location
        loc = self.location
        self.lat = loc['coordinate']['latitude']
        self.lon = loc['coordinate']['longitude']

    # Handle: What's The Air Quality Like [Today]
    @intent_handler(IntentBuilder("").require("Query").one_of("Air", "Air Quality").build())
    def handle_index_quality_air(self, message):
        self.log.debug("Handler: handle_aqi_now")

        data = self.get_air_quality()

        if data is None:
            self.speak_dialog("Something Went Wrong")
        else:
            daily_values = self.forecast(data, 0)
            self.simplify_and_speak(daily_values)

    # Returns A Dictionary From The Api Containing Air Quality Data & A Bunch of Fluff / Attributions
    def get_air_quality(self) -> dict or None:
        try:
            url = base_url + "geo:{0};{1}/?token={2}".format(self.lat, self.lon, self.api_key)

            response = requests.get(url=url, timeout=3)
            response.raise_for_status()  # Raises and exception if anything seems wrong with response
            return response.json()
        except Exception as error:
            self.log.error(f"Data Collection Error: {error}")
            return None

    # Get The Average Value For Each of The Aerial Pollutants <days_from_now> Days From Today
    # ex : today is the 5th and <days_from_now> = 4 will return the forecast for the 9th
    @staticmethod
    def forecast(data: dict, days_from_now: int) -> dict:

        daily_values = {}

        date = today().strftime('%Y-%m-%d')
        date = date[:8] + str(int(date[8:]) + days_from_now)  # Change Lookup Date

        for i in data.items():
            if type(i[0]) == str:
                for j in data[i[0]]:
                    if j['day'] == date:
                        daily_values[i[0]] = j['avg']

        return daily_values

    # Tries to simplify spoken text to minimize repetitions
    # ie if all pollutants are of one category
    def simplify_and_speak(self, daily_values: dict) -> None:

        term_dict = {}
        # Map Each Value To The Correct AQI/UVI Term
        for i in daily_values.keys():
            term_dict[i] = self.air_quality_to_term(value=daily_values[i], pollutant=i)

        # All Values Are The Same
        if len(Counter(term_dict.values())) == 1:
            self.speak_dialog("all air quality parameters are {}".format(term_dict["o3"]))

        else:
            # Invert The Dictionary So That The (Good, Moderate, Unhealthy etc) Map To A List Pollutants
            inverted_dict = dict()
            for key, value in term_dict.items():
                inverted_dict.setdefault(value, list()).append(key)

            for i in inverted_dict.keys():
                linking_verb = "is" if len(inverted_dict[i]) > 1 else "are"
                self.speak_dialog(*inverted_dict[i], linking_verb, i)
                self.log.debug(*inverted_dict[i], linking_verb, i)

    # Returns Level of Concern For A Given Pollutant Value
    @staticmethod
    def air_quality_to_term(value: int, pollutant: str) -> str:
        # Everything but the UV index has a shared scale
        if pollutant != "uvi":
            if value < 50:
                return "Good"
            elif value < 100:
                return "Moderate"
            elif value < 200:
                return "Unhealthy"
            elif value < 300:
                return "Very Unhealthy"
            else:
                return "Hazardous"

        else:  # UVI
            if value < 2:
                return "Good"
            elif value < 5:
                return "Moderate"
            elif value < 7:
                return "Unhealthy"
            elif value < 10:
                return "Very Unhealthy"
            else:
                return "Hazardous"


def create_skill():
    return AirQualityIndex()
