import requests
from dateutil.utils import today

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler

"""
    A Skill to return the daily air quality parameters based on your latitude/longitude
    TODO: Handle x days from now in an Intent Handler (the forecast side is ready for it rn)

    This skill uses the data from the World Air Quality Project (WAQP) (https://aqicn.org/api/) 
    Specifically, The Geo-Localized Feed (https://aqicn.org/json-api/doc/#api-Geolocalized_Feed-GetGeolocFeed)
"""

BASE_URL = "https://api.waqi.info/feed/"


class AirQualityIndex(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

        self.api_key = self.settings.get('api_key')

        # Mycroft Location
        loc = self.location
        self.lat = loc['coordinate']['latitude']
        self.lon = loc['coordinate']['longitude']

    # Handle: What's The Air Quality Like
    @intent_handler(IntentBuilder("").require("Query").one_of("Air", "Air Quality").build())
    def handle_index_quality_air(self):
        self.log.debug("Handler: handle_aqi_now")

        data = self.get_air_quality()

        if data is None:
            self.speak_dialog("Something Went Wrong")
        else:
            daily_values = self.forecast(data, 0)
            self.simplify_and_speak(daily_values)

    def get_air_quality(self) -> dict or None:
        """
            Makes a GET request to the WAQP API which should return either a jSON file or a HTTP Error Status Code

            :returns
                Dict : Returns the JSON file as a Dictionary
                None : If A HTTP Error Occurred In the Get Request, It Logs The Error and Returns None
        """

        try:
            url = BASE_URL + "geo:{0};{1}/?token={2}".format(self.lat, self.lon, self.api_key)

            response = requests.get(url=url, timeout=3)
            response.raise_for_status()  # Raises and exception if anything seems wrong with response
            return response.json()
        except (requests.HTTPError, requests.ConnectionError, requests.RequestException) as error:
            self.log.error(f"Data Collection Error: {error}")
            return None

    @staticmethod
    def forecast(data: dict, days_from_now: int) -> dict:
        """
            Get The Average Value For Each of The Aerial Pollutants <days_from_now> Days From Today
            ex : today is the 5th and <days_from_now> = 4 will return the forecast for the 9th

            :param data : The JSON Dictionary From get_air_quality()
            :param days_from_now : Used to increment which day the data is retrieved from

            :returns
                Dict : Returns a dictionary containing each pollutant mapped to it's value
        """

        daily_values = {}

        date = today().strftime('%Y-%m-%d')
        date = date[:8] + str(int(date[8:]) + days_from_now)  # Change Lookup Date

        for i in data.items():
            if isinstance(i[0], str):
                for j in data[i[0]]:
                    if j['day'] == date:
                        daily_values[i[0]] = j['avg']

        return daily_values

    def simplify_and_speak(self, daily_values: dict) -> None:
        """
            Speaks The Values For Each Air Quality Parameter

            :param daily_values: a dict containing each pollutant mapped to it's value - The Output of Self.forecast()

            :return:
                None :  Nothing
        """

        term_dict = {}
        # Map Each Value To The Correct AQI/UVI Term
        for i in daily_values.keys():
            term_dict[i] = self.air_quality_to_term(value=daily_values[i], pollutant=i)

        self.log.debug(term_dict)

        # Invert The Dictionary So That The (Good, Moderate, Unhealthy etc) Map To A List Pollutants
        inverted_dict = dict()
        for key, value in term_dict.items():
            inverted_dict.setdefault(value, list()).append(key)

        self.log.debug(inverted_dict)

        # ex Ozone [and] Fine Particulates Are Good
        for i in inverted_dict.keys():
            linking_verb = "is" if len(inverted_dict[i]) > 1 else "are"
            self.speak_dialog(*inverted_dict[i], linking_verb, i)
            self.log.debug(*inverted_dict[i], linking_verb, i)

    @staticmethod
    def air_quality_to_term(value: int, pollutant: str) -> str:
        """
            Returns The Level of Concern For A Given Pollutant Value
            Note, Ozone, PM25 and PM10 all Use The First Scale, While The UV Index Uses It's Own

            :param pollutant: a string containing
            :param value: an int representing the Air Quality Index Value for <pollutant>

            :return:
                None :  Nothing
        """

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
