from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

from utils.showDTO import ShowDTO

class ASEastChannel:
    def __init__(self, xml_generator = None, tvg_api_key = None):
        self.generator = xml_generator
        self.tvg_api_key = tvg_api_key
        self.today = datetime.now().date()
        self.tvg_id = "ch_cm0rh88z"
        self.base_url = f"https://api.tvguideapi.com/v1/channels/{self.tvg_id}/schedule?date"
        self.OUTPUT_XML = "as-east.xml"      # Output XMLTV file
        self.CHANNEL_ID = "as-east"
        self.CHANNEL_NAME = "Adult Swim East"
        self.CHANNEL_LOGO = "https://www.adultswim.com/img/as-logo.svg"


    def get_shows(self, channel_id):
            print(f"Fetching shows for channel: {channel_id} with API key: {self.tvg_api_key}")
            response = requests.get(
                self.base_url + f"={self.today}" + "&tz=America%2FNew_York",
                headers={
                    "Authorization": f"Bearer {self.tvg_api_key}"
                },
                timeout=30
            ).json()
    
            return response.get("data", [])
    
    def handle_conversion(self):
        shows = self.get_shows(self.CHANNEL_ID)
        if not shows:
            print("No shows to convert.")
            return
        
        self.convert(shows)

    def convert(self, shows):
        print(f"Converting {len(shows)} shows for channel: {self.CHANNEL_ID}")
        converted_shows = []

        SOURCE_TZ = ZoneInfo("UTC")
        tz = ZoneInfo("America/New_York")

        for show in shows:
            # Need to extract Times and convert them to a usable format for XMLTV
            start_time = show.get("start")
            end_time = show.get("stop")

            if start_time:
                start_time = datetime.fromisoformat(start_time).replace(tzinfo=SOURCE_TZ).isoformat()
            if end_time:
                end_time = datetime.fromisoformat(end_time).replace(tzinfo=SOURCE_TZ).isoformat()

            print(f"Processing show: {show.get('title')}")
            converted_show = ShowDTO(
                name=show.get("title"),
                startDate=self.generator.iso_to_xmltv(start_time),
                endDate=self.generator.iso_to_xmltv(end_time),
                description=show.get("description"),
                episodeNumber=None,
                onScreen=show.get("episode_num").replace("onscreen:", ""),
                subtitle=show.get("sub_title")
            )
            converted_shows.append(converted_show)

        self.generator.convert_to_xml(self, converted_shows, self.CHANNEL_LOGO)
        