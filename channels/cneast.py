from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

from utils.showDTO import ShowDTO

class CNEastChannel:
    def __init__(self, xml_generator = None, tvg_api_key = None):
        self.generator = xml_generator
        self.tvg_api_key = tvg_api_key
        self.tvg_id = "ch_9msqd0yx"
        self.base_url = f"https://api.tvguideapi.com/v1/channels/{self.tvg_id}/schedule?date"
        self.OUTPUT_XML = "cn-east.xml"      # Output XMLTV file
        self.CHANNEL_ID = "cn-east"
        self.CHANNEL_NAME = "Cartoon Network East"
        self.CHANNEL_LOGO = "https://static.wikia.nocookie.net/youtube/images/3/3e/Cartoon_Network.jpeg/revision/latest/scale-to-width-down/268?cb=20250222103744"  # URL to the channel logo

        self.today = datetime.now().date()

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

        for show in shows:
            # Need to extract Times and convert them to a usable format for XMLTV
            start_time = show.get("start")
            end_time = show.get("stop")

            print(f"Raw show data: {show}")

            start_time_utc = datetime.fromisoformat(start_time)
            end_time_utc = datetime.fromisoformat(end_time)

            if start_time_utc:
                start_time_utc = (start_time_utc - timedelta(hours=3))
            if end_time_utc:
                end_time_utc = (end_time_utc - timedelta(hours=3))

            print(start_time_utc, end_time_utc)

            episode_number = show.get("episode_num")

            if episode_number:
                episode_number = episode_number.replace("onscreen:", "")

            converted_show = ShowDTO(
                name=show.get("title"),
                startDate=self.generator.iso_to_xmltv(start_time_utc.isoformat()),
                endDate=self.generator.iso_to_xmltv(end_time_utc.isoformat()),
                description=show.get("description"),
                episodeNumber=None,
                onScreen=episode_number,
                subtitle=show.get("sub_title")
            )
            converted_shows.append(converted_show)

        self.generator.convert_to_xml(self, converted_shows, self.CHANNEL_LOGO)
