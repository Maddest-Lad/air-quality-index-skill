from mycroft import MycroftSkill, intent_file_handler


class AirQualityIndex(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('index.quality.air.intent')
    def handle_index_quality_air(self, message):
        self.speak_dialog('index.quality.air')


def create_skill():
    return AirQualityIndex()

