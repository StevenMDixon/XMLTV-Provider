from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

from channels.cneast import EASTERN
from utils import tvpassportparser
from utils.showDTO import ShowDTO

class NickToonsEastChannel:
    def __init__(self, xml_generator = None, tvg_api_key = None):
        self.generator = xml_generator
        self.STATION_ID = 11445
        self.STATION_SLUG = "nicktoons-hd-east"
        self.base_url = f"https://www.tvpassport.com/tv-listings/stations/"
        self.OUTPUT_XML = "nicktoons-east.xml"      # Output XMLTV file
        self.CHANNEL_ID = "nicktoons-east"
        self.CHANNEL_NAME = "Nicktoons East"
        self.CHANNEL_LOGO = "https://static.wikia.nocookie.net/dreamlogos/images/b/bb/Nicktoons_UK_2014.png/revision/latest/scale-to-width-down/279?cb=20221230233702"  # URL to the channel logo

        self.today = datetime.now().date()

    def get_shows(self, date):
            url = (
                f"https://www.tvpassport.com/tv-listings/stations/"
                f"{self.STATION_SLUG}/{self.STATION_ID}/{date}"
            )

            response = requests.get(
                url,
                headers={"User-Agent": "HiveMind-EPG/1.0"},
                timeout=30
            )

            return tvpassportparser.parse_schedule(response.text, EASTERN)


    def handle_conversion(self):
        shows = self.get_shows(self.today)
        tomorrow = self.today + timedelta(days=1)
        shows += self.get_shows(tomorrow)

        if not shows:
            print("No shows to convert.")
            return
        
        self.convert(shows)

    def convert(self, shows):
        print(f"Converting {len(shows)} shows for channel: {self.CHANNEL_ID}")
        converted_shows = []

        for show in shows:
            # Need to extract Times and convert them to a usable format for XMLTV
            start_time = show["start"].strftime("%Y%m%d%H%M%S %z")
            end_time = show["stop"].strftime("%Y%m%d%H%M%S %z")
            episode_num = show["episode_number"]

            converted_show = ShowDTO(
                name=show["title"],
                startDate=start_time,
                endDate=end_time,
                description=show["description"],
                onScreen=episode_num,
                episodeNumber=episode_num,
                subtitle=show["subtitle"]
            )

            converted_shows.append(converted_show)

        self.generator.convert_to_xml(self, converted_shows, self.CHANNEL_LOGO)