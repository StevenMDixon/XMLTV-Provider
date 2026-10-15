from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import requests

from utils import tvpassportparser
from utils.showDTO import ShowDTO

EASTERN = ZoneInfo("America/New_York")

class CNEastChannel:
    def __init__(self, xml_generator = None, tvg_api_key = None):
        self.generator = xml_generator
        self.STATION_ID = 6917
        self.STATION_SLUG = "cartoon-network-usa-hd-eastern"
        self.base_url = f"https://www.tvpassport.com/tv-listings/stations/"
        self.OUTPUT_XML = "cn-east.xml"      # Output XMLTV file
        self.CHANNEL_ID = "cn-east"
        self.CHANNEL_NAME = "Cartoon Network East"
        self.CHANNEL_LOGO = "https://static.wikia.nocookie.net/youtube/images/3/3e/Cartoon_Network.jpeg/revision/latest/scale-to-width-down/268?cb=20250222103744"  # URL to the channel logo

        self.today = datetime.now().date()

    def get_shows(self,date):
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
    
            startDateTime = datetime.now().replace(hour=10, minute=0, second=0)
            endDateTime = datetime.now().replace(hour=21, minute=0, second=0) 
            
            for day in range(days_ahead + 1):
                off_air_show = ShowDTO(
                    name="Off Air",
                    startDate=startDateTime.strftime("%Y%m%d%H%M%S %z"),
                    endDate=endDateTime.strftime("%Y%m%d%H%M%S %z"),
                    description="See you tomorrow at 6am.",
                    onScreen="",
                    episodeNumber=None,
                    subtitle="See you tomorrow at 6am."
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
            end_time = show["stop"]

            if start_time.time() >= time(21, 0) or start_time.time() < time(10, 0):
                continue

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
