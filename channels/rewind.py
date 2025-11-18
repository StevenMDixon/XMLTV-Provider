import requests
import re
import json5
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET


class RewindChannel:
    def __init__(self):
        pass

    def handle_conversion(self):
        # -----------------------------
        # Config
        # -----------------------------
        CHANNEL_ID = "swimrewind"
        DAYS_TO_GENERATE = 3
        SOURCE_URL = "https://swimrewind.com/customjavascript"

        # -----------------------------
        # Fetch JS schedule
        # -----------------------------
        resp = requests.get(SOURCE_URL, verify=False)
        resp.raise_for_status()
        js = resp.text

        match = re.search(r"const\s+schedule\s*=\s*(\{[\s\S]*?\});", js)
        if not match:
            raise RuntimeError("Could not find schedule object in JS")

        schedule_text = match.group(1)

        # Remove JS comments
        schedule_text = re.sub(r"//.*", "", schedule_text)

        # Parse as JSON5 (handles unquoted keys, trailing commas, single quotes)
        schedule = json5.loads(schedule_text)

        # -----------------------------
        # XMLTV Root
        # -----------------------------
        tv = ET.Element("tv")
        channel = ET.SubElement(tv, "channel", id=CHANNEL_ID)
        ET.SubElement(channel, "display-name").text = "Swim Rewind"

        # -----------------------------
        # Helper: build XMLTV datetime
        # -----------------------------
        def xmltv_dt(dt: datetime):
            return dt.astimezone(ZoneInfo("UTC")).strftime("%Y%m%d%H%M%S +0000")

        # -----------------------------
        # Determine correct weekday order
        # -----------------------------
        def weekday_name(dt):
            return dt.strftime("%A")  # Monday, Tuesday, etc.

        # -----------------------------
        # Generate EPG
        # -----------------------------
        SOURCE_TZ = ZoneInfo("America/Chicago")
        tz = ZoneInfo("America/New_York")
        now = datetime.now(tz)

        for day_offset in range(DAYS_TO_GENERATE):
            day = now + timedelta(days=day_offset)
            day_name = weekday_name(day)

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
                    stop_dt = day.replace(hour=next_t.hour, minute=next_t.minute, second=0, microsecond=0)
                    if stop_dt <= start_dt:
                        stop_dt += timedelta(days=1)  # wraps past midnight
                else:
                    stop_dt = start_dt + timedelta(minutes=30)  # fallback duration

                # Add programme entry
                programme = ET.SubElement(tv, "programme", {
                    "start": xmltv_dt(start_dt),
                    "stop": xmltv_dt(stop_dt),
                    "channel": CHANNEL_ID
                })
                ET.SubElement(programme, "title").text = show_title

        # -----------------------------
        # Output to XML file
        # -----------------------------
        tree = ET.ElementTree(tv)
        output_filename = "./xml_schedules/rewind.xml"
        tree.write(output_filename, encoding="utf-8", xml_declaration=True)

        print(f"EPG XML generated: {output_filename}")