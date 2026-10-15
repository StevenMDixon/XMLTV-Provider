from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import requests

from channels.cneast import EASTERN
from utils import tvpassportparser
from utils.showDTO import ShowDTO

class ASEastChannel:
    def __init__(self, xml_generator = None, tvg_api_key = None):
        self.generator = xml_generator
        self.tvg_api_key = tvg_api_key
        self.today = datetime.now().date()
        self.STATION_ID = 607
        self.STATION_SLUG = "adult-swim-east"
        self.base_url = f"https://www.tvpassport.com/tv-listings/stations/"
        self.OUTPUT_XML = "as-east.xml"      # Output XMLTV file
        self.CHANNEL_ID = "as-east"
        self.CHANNEL_NAME = "Adult Swim East"
        self.CHANNEL_LOGO = "https://www.adultswim.com/img/as-logo.svg"


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
            today_shows = self.get_shows(self.today)
            tomorrow = self.today + timedelta(days=1)
            tomorrow_shows = self.get_shows(tomorrow)

            shows = today_shows + tomorrow_shows
            if not shows:
                print("No shows to convert.")
                return
            
            self.convert(shows)

    def get_off_air_entries(self, days_ahead):
        off_air_items = [];

        startDateTime = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0)
        endDateTime = datetime.now(timezone.utc).replace(hour=21, minute=0, second=0) 
        
        for day in range(days_ahead + 1):
            off_air_show = ShowDTO(
                name="Off Air",
                startDate=startDateTime.strftime("%Y%m%d%H%M%S %z"),
                endDate=endDateTime.strftime("%Y%m%d%H%M%S %z"),
                description="We'll be back at 5pm.",
                onScreen="",
                episodeNumber=None,
                subtitle="We'll be back at 5pm."
            )
            off_air_items.append(off_air_show)

            startDateTime += timedelta(days=1)
            endDateTime += timedelta(days=1)

        return off_air_items


    def convert(self, shows):
        print(f"Converting {len(shows)} shows for channel: {self.CHANNEL_ID}")
        converted_shows = []

        for show in shows:
            # Need to extract Times and convert them to a usable format for XMLTV
            start_time = show["start"]

            if start_time.time() >= time(10, 0) and start_time.time() < time(21, 0):
                continue

            end_time = show["stop"]
            episode_num = show["episode_number"]

            converted_show = ShowDTO(
                name=show["title"],
                startDate=start_time.strftime("%Y%m%d%H%M%S %z"),
                endDate=end_time.strftime("%Y%m%d%H%M%S %z"),
                description=show["description"],
                onScreen=episode_num,
                episodeNumber=episode_num,
                subtitle=show["subtitle"]
            )

            converted_shows.append(converted_show)

        off_air_entries = self.get_off_air_entries(1)
        converted_shows.extend(off_air_entries)
        converted_shows.sort(key=lambda show: show.startDate)
        self.generator.convert_to_xml(self, converted_shows, self.CHANNEL_LOGO)