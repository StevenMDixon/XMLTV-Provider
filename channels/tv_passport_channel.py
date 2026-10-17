from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import requests
from utils import tvpassportparser
from utils.showDTO import ShowDTO

EASTERN = ZoneInfo("America/New_York")

class tv_passport_channel:
    def __init__(self, xml_generator = None, file_data=None):
        self.generator = xml_generator
        self.base_url = f"https://www.tvpassport.com/tv-listings/stations/"
        self.STATION_ID = file_data['station_id']
        self.STATION_SLUG = file_data['station_slug']
        self.OUTPUT_XML = f"{file_data['channel_id']}.xml"      # Output XMLTV file
        self.CHANNEL_ID = file_data['channel_id']
        self.CHANNEL_NAME = file_data['channel_id'].replace("-", " ").title()
        self.CHANNEL_LOGO = file_data['channel_logo']  # URL to the channel logo

        off_air_start = file_data['off_air_start'] if 'off_air_start' in file_data else None
        if off_air_start is not None:
            self.off_air_start = datetime.strptime(off_air_start, "%H:%M:%S").time()
        else:
            self.off_air_start = None

        off_air_end = file_data['off_air_end'] if 'off_air_end' in file_data else None
        if off_air_end is not None:
            self.off_air_end = datetime.strptime(off_air_end, "%H:%M:%S").time()
        else:
            self.off_air_end = None

        self.today = datetime.now().date() - timedelta(days=1)

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
        days_ahead = 2

        shows = []

        for i in range(0, days_ahead + 1):
            today = self.today + timedelta(days=i)
            shows += self.get_shows(today)

        if not shows:
            print("No shows to convert.")
            return
        
        self.convert(shows)

    def isChannelOffAir(self, check_time):
        if self.off_air_start is None or self.off_air_end is None:
            return False   

        showsStart = check_time.time()

        if(self.off_air_start < self.off_air_end):
            return showsStart >= self.off_air_start and showsStart < self.off_air_end
        else:
            #  if start_time.time() >= time(21, 0) or start_time.time() < time(10, 0):
            return showsStart >= self.off_air_start or showsStart < self.off_air_end    

    def convert(self, shows):
        print(f"Converting {len(shows)} shows for channel: {self.CHANNEL_ID}")
        converted_shows = []

        for show in shows:
            print(show)
            # Need to extract Times and convert them to a usable format for XMLTV
            start_time = show["start"]
            end_time = show["stop"]

            if self.isChannelOffAir(start_time):
                continue

            episode_num = show["episode_number"]

            converted_show = ShowDTO(
                name=show["title"],
                startDate=start_time.strftime("%Y%m%d%H%M%S %z"),
                endDate=end_time.strftime("%Y%m%d%H%M%S %z"),
                description=show["description"],
                onScreen=episode_num,
                episodeNumber=episode_num if episode_num != None and episode_num.isdigit() else None,
                subtitle=show["subtitle"]
            )

            converted_shows.append(converted_show)

        off_air_entries = self.get_off_air_entries(1)
        converted_shows.extend(off_air_entries)
        converted_shows.sort(key=lambda show: show.startDate)
        self.generator.convert_to_xml(self, converted_shows, self.CHANNEL_LOGO)

    def get_off_air_entries(self, days_ahead):
        off_air_items = []

        if self.off_air_start is None or self.off_air_end is None:
            return off_air_items

        today = datetime.now(timezone.utc).date()

        for day in range(days_ahead + 1):
            current_date = today + timedelta(days=day)

            start_datetime = datetime.combine(
                current_date,
                self.off_air_start,
                tzinfo=timezone.utc
            )

            end_datetime = datetime.combine(
                current_date,
                self.off_air_end,
                tzinfo=timezone.utc
            )

            # End time is on the following day
            if end_datetime <= start_datetime:
                end_datetime += timedelta(days=1)

            off_air_items.append(
                ShowDTO(
                    name="Off Air",
                    startDate=start_datetime.strftime("%Y%m%d%H%M%S %z"),
                    endDate=end_datetime.strftime("%Y%m%d%H%M%S %z"),
                    description="Off Air",
                    onScreen="",
                    episodeNumber=None,
                    subtitle="Off Air"
                )
            )

        return off_air_items