import requests
import re
import json5
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

from utils.showDTO import ShowDTO


class RewindChannel:
    def __init__(self, xml_generator = None):
        self.OUTPUT_XML = "rewind.xml"      # Output XMLTV file
        self.CHANNEL_ID = "swimrewind"
        self.CHANNEL_NAME = "Swim Rewind"

        self.DAYS_TO_GENERATE = 3
        self.SOURCE_URL = "https://swimrewind.com/customjavascript"

        self.generator = xml_generator

    def get_shows(self):
        resp = requests.get(self.SOURCE_URL, verify=False)
        resp.raise_for_status()
        js = resp.text

        match = re.search(r"const\s+schedule\s*=\s*(\{[\s\S]*?\});", js)
        if not match:
            raise RuntimeError("Could not find schedule object in JS")

        schedule_text = match.group(1)

        # Remove JS comments
        schedule_text = re.sub(r"//.*", "", schedule_text)

        # Parse as JSON5 (handles unquoted keys, trailing commas, single quotes)
        return json5.loads(schedule_text)
        
    def handle_conversion(self):
        converted_shows = []
       
        schedule = self.get_shows()

        SOURCE_TZ = ZoneInfo("America/Chicago")
        tz = ZoneInfo("America/New_York")
        now = datetime.now(tz)

        for day_offset in range(self.DAYS_TO_GENERATE):
            day = now + timedelta(days=day_offset)
            day_name = self.generator.weekday_name(day)

            if day_name not in schedule:
                print(f"Warning: No schedule for {day_name}, skipping.")
                continue

            day_shows = schedule[day_name]
            sorted_times = sorted(day_shows.keys(), key=lambda t: datetime.strptime(t, "%H:%M"))

            for i, start_str in enumerate(sorted_times):
                show_title = str(day_shows[start_str]).strip()

                start_time = datetime.strptime(start_str, "%H:%M")

                start_dt_naive = day.replace(
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=0,
                    microsecond=0
                )
                # localize to the source timezone (America/Chicago)
                start_dt = start_dt_naive.replace(tzinfo=SOURCE_TZ)

                # Determine stop time
                if i + 1 < len(sorted_times):
                    next_start_str = sorted_times[i + 1]
                    next_t = datetime.strptime(next_start_str, "%H:%M")
                    
                    stop_dt_naive = day.replace(hour=next_t.hour, minute=next_t.minute, second=0, microsecond=0)
                    stop_dt = stop_dt_naive.replace(tzinfo=SOURCE_TZ)

                    if stop_dt <= start_dt:
                        stop_dt += timedelta(days=1)  # wraps past midnight
                else:
                    stop_dt = start_dt + timedelta(minutes=30)  # fallback duration

                converted_shows.append(
                    ShowDTO(
                        name=show_title,
                        startDate=self.generator.iso_to_xmltv(start_dt.astimezone(tz).isoformat()),
                        endDate=self.generator.iso_to_xmltv(stop_dt.astimezone(tz).isoformat()),
                        description=None,
                        episodeNumber=None,
                        iconUrl=None
                    )
                )

        # -----------------------------
        self.generator.convert_to_xml(self, converted_shows)