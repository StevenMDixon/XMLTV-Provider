from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

from utils.showDTO import ShowDTO

class NickEastChannel:
    def __init__(self, xml_generator = None, tvg_api_key = None):
        self.generator = xml_generator
        self.tvg_api_key = tvg_api_key
        self.tvg_id = "ch_7wb0p3ak"
        self.base_url = f"https://api.tvguideapi.com/v1/channels/{self.tvg_id}/schedule?date"
        self.OUTPUT_XML = "nick-east.xml"      # Output XMLTV file
        self.CHANNEL_ID = "nick-east"
        self.CHANNEL_NAME = "Nickelodeon East"
        self.CHANNEL_LOGO = "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/c82dd5b3-b0d8-44e8-b11d-a50e55b7b9de/dfarp8m-d179a77e-c1f3-4564-bb8f-332374472311.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiIvZi9jODJkZDViMy1iMGQ4LTQ0ZTgtYjExZC1hNTBlNTViN2I5ZGUvZGZhcnA4bS1kMTc5YTc3ZS1jMWYzLTQ1NjQtYmI4Zi0zMzIzNzQ0NzIzMTEucG5nIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.E3sERHPPdmhQcRhmoNhyM3upJWp0NTaNThoS3yDcmtM"  # URL to the channel logo

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

        SOURCE_TZ = ZoneInfo("America/New_York")
        tz = ZoneInfo("America/New_York")

        for show in shows:
            # Need to extract Times and convert them to a usable format for XMLTV
            start_time = show.get("start")
            end_time = show.get("stop")
            print(f"Raw show data: {show}")

            start_time_utc = datetime.fromisoformat(start_time) if start_time else None
            end_time_utc = datetime.fromisoformat(end_time) if end_time else None

            if start_time_utc:
                start_time = start_time_utc.astimezone(tz).isoformat()
            if end_time_utc:
                end_time = end_time_utc.astimezone(tz).isoformat()

            converted_show = ShowDTO(
                name=show.get("title"),
                startDate=start_time,
                endDate=end_time,
                description=show.get("description"),
                episodeNumber=show.get("episode_num"),
                iconUrl='',
                subtitle=show.get("sub_title")
            )
            converted_shows.append(converted_show)

        self.generator.convert_to_xml(self, converted_shows, self.CHANNEL_LOGO)
