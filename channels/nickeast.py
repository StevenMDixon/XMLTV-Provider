from datetime import datetime, timedelta, timezone
from pydoc import html
import re
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

from utils import tvpassportparser
from utils.showDTO import ShowDTO

EASTERN = ZoneInfo("America/New_York")

class NickEastChannel:
    def __init__(self, xml_generator = None, tvg_api_key = None):
        self.generator = xml_generator
        self.tvg_api_key = tvg_api_key
        self.STATION_ID = 658
        self.STATION_SLUG = "nickelodeon-usa-east-feed"
        self.base_url = f"https://www.tvpassport.com/tv-listings/stations/"

        self.OUTPUT_XML = "nick-east.xml"      # Output XMLTV file
        self.CHANNEL_ID = "nick-east"
        self.CHANNEL_NAME = "Nickelodeon East"
        self.CHANNEL_LOGO = "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/c82dd5b3-b0d8-44e8-b11d-a50e55b7b9de/dfarp8m-d179a77e-c1f3-4564-bb8f-332374472311.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiIvZi9jODJkZDViMy1iMGQ4LTQ0ZTgtYjExZC1hNTBlNTViN2I5ZGUvZGZhcnA4bS1kMTc5YTc3ZS1jMWYzLTQ1NjQtYmI4Zi0zMzIzNzQ0NzIzMTEucG5nIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.E3sERHPPdmhQcRhmoNhyM3upJWp0NTaNThoS3yDcmtM"  # URL to the channel logo

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