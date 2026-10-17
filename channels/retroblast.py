from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET
import csv
import io
import urllib.request
from datetime import date
from dateutil import parser

from utils.showDTO import ShowDTO

class RetroblastChannel:
    def __init__(self, xml_generator = None):
        self.OUTPUT_XML = "retroblast.xml"      # Output XMLTV file
        self.CHANNEL_ID = "retroblast"
        self.CHANNEL_NAME = "Retroblast"
        self.CHANNEL_LOGO = "https://retroblast.tv/logo"

        self.SOURCE_URL = "https://docs.google.com/spreadsheets/d/1JzGvY5st6Z8x0w5vh7L6vuzh34bZKjMl0zMi328xOT8/edit?gid=0#gid=0"

        self.generator = xml_generator
        self.today = datetime.now().date() - timedelta(days=1)

    def get_schedule(self):
        sheet_id = "1JzGvY5st6Z8x0w5vh7L6vuzh34bZKjMl0zMi328xOT8"
        gid = "0"

        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

        mySchedule = {
            'Monday': [],
            'Tuesday': [],
            'Wednesday': [],
            'Thursday': [],
            'Friday': [],
            'Saturday': [],
            'Sunday': []
        }

        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        previous_time = None

        for row in rows:
            ct = row['Time in EST']
            print(ct, self.is_unknown_time_format(ct))
            if self.is_unknown_time_format(ct) or ct == '':
                continue

            current_time = self.parse_time(row['Time in EST'], previous_time)
            previous_time = current_time

            for day in mySchedule:
                if day not in row or not row[day]:
                    continue
                
                mySchedule[day].append((current_time, row[day]))

                print(mySchedule['Friday'])

        return mySchedule

    def is_unknown_time_format(self, time_str):
        try:
            parser.parse(time_str)
            return False
        except (ValueError, OverflowError):
            return True

    def parse_time(self, value: str, previous_time=None):
        value = value.strip().upper()

        for fmt in ("%I:%M:%S %p", "%I:%M %p"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                pass

        # No AM/PM specified
        parsed = datetime.strptime(value, "%I:%M").time()

        hour = parsed.hour

        if previous_time is not None:
            # Infer AM/PM from chronological order
            candidates = [
                parsed.replace(hour=hour % 12),
                parsed.replace(hour=(hour % 12) + 12)
            ]

            valid = [t for t in candidates if t > previous_time]

            if valid:
                return min(valid)

        return parsed

    def get_shows(self):
        schedule = self.get_schedule()
        days_ahead = 2
        shows = [];

        
        for i in range(0, days_ahead + 1):
            today = self.today + timedelta(days=i)
            day_name = today.strftime("%A")
            current_day_schedule = schedule.get(day_name, [])
            for index, (time, title) in enumerate(current_day_schedule):

                start_utc = datetime.combine(today, time).astimezone(ZoneInfo("UTC"))
                end_utc = datetime.combine(today + timedelta(days=1), time.min).astimezone(ZoneInfo("UTC")) if index == len(current_day_schedule) - 1 else datetime.combine(today, current_day_schedule[index + 1][0]).astimezone(ZoneInfo("UTC"))
                
                shows.append({
                    "title": title,
                    "subtitle": "",
                    "episode_number": "",
                    "description": None,
                    "rating": None,
                    "category": None,
                    "listing_id": None,
                    "start": start_utc,
                    "stop": end_utc,
                }   )

        return shows
        
    def handle_conversion(self):
        shows = self.get_shows()
        print(f"Converting {len(shows)} shows for channel: {self.CHANNEL_ID}")
        converted_shows = []

        for show in shows:
            print(show)
            # Need to extract Times and convert them to a usable format for XMLTV
            start_time = show["start"]
            end_time = show["stop"]

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

        converted_shows.sort(key=lambda show: show.startDate)
        self.generator.convert_to_xml(self, converted_shows, self.CHANNEL_LOGO)