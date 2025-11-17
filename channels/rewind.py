#!/usr/bin/env python3
"""
generate_epg.py

Fetches a published Google Sheets CSV (weekly grid), maps today's weekday
(and next 2 days) to the schedule columns, converts times from sheet timezone
(America/Chicago) to Eastern (America/New_York), and writes an XMLTV file
called rewind.xml.

Requirements: Python 3.9+ (for zoneinfo)
No third-party packages required.

Usage:
    python generate_epg.py
"""

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import csv
import io
import requests
import sys
import re
import xml.etree.ElementTree as ET

# ==== CONFIG ====
CSV_URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vTyuFJJk4PhKqIy6n8hiEVwpGGk6tKLdXIZ_jkamqgcTrXnRMPavZcHmH-Lbm_BjsyamV9fjEqLFWDN"
           "/pub?gid=0&single=true&output=csv")
SHEET_TZ = ZoneInfo("America/Chicago")   # sheet times shown as "ALL TIMES IN CST" -> use America/Chicago for DST handling
OUTPUT_TZ = ZoneInfo("America/New_York")
CHANNEL_ID = "rewind"
CHANNEL_NAME = "Rewind"
EPG_DAYS = 3   # today + next 2 days
OUTPUT_FILE = "rewind.xml"
# =================

WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

class RewindChannel:
    def __init__(self):
        self.TIME_RANGE_RE = re.compile(r'^\s*(?P<start>[^-]+?)\s*-\s*(?P<end>.+?)\s*$')

    def handle_conversion(self):
        self.main()

    def fetch_csv(self, url):
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.text

    def csv_to_rows(self, csv_text):
        f = io.StringIO(csv_text)
        reader = csv.reader(f)
        return [row for row in reader]

    def find_header_and_columns(self, rows):
        for i, row in enumerate(rows[:20]):  # search first 20 rows for header
            if not row:
                continue
            # normalize cells
            norm = [ (cell.strip().lower() if cell else "") for cell in row ]
            # check if at least 3 weekday names appear
            weekday_matches = [wd.lower() for wd in WEEKDAYS if wd.lower() in norm]
            if len(weekday_matches) >= 3:
                # build mapping
                mapping = {}
                for wd in WEEKDAYS:
                    if wd.lower() in norm:
                        mapping[wd] = norm.index(wd.lower())
                # find time-range column as the first non-weekday column to left (usually index 0)
                # we'll choose the leftmost column that is not a weekday index
                weekday_indices = set(mapping.values())
                time_col = 0
                for idx in range(len(row)):
                    if idx not in weekday_indices:
                        # Heuristic: first column is typically the time range
                        time_col = idx
                        break
                return i, mapping, time_col
        raise RuntimeError("Could not find header row with weekday names. Check CSV layout.")

        

    def parse_time_str(self, t_str):
        """
        Parse a time like:
        "12:00 AM", "3:50PM", "12AM", "4 PM", "1:00:30PM"
        into a time object.
        """
        t_str = t_str.strip().upper()

        # Normalize missing space before AM/PM:
        # e.g., "3:50PM" -> "3:50 PM", "12AM" -> "12 AM"
        t_str = re.sub(r'(?<=\d)(AM|PM)$', r' \1', t_str)

        # Try common formats:
        fmts = [
            "%I:%M %p",
            "%I %p",
            "%I:%M:%S %p",
        ]

        for fmt in fmts:
            try:
                return datetime.strptime(t_str, fmt).time()
            except ValueError:
                continue

        raise ValueError(f"Unrecognized time format: '{t_str}'")


    def build_programmes_for_date(self, rows, header_idx, mapping, time_col, target_date):
        """
        For a single date (a datetime.date), return list of programme dicts:
        { 'start_dt_central': datetime, 'end_dt_central': datetime, 'title': str }
        start_dt_central and end_dt_central are timezone-aware in SHEET_TZ
        """
        weekday_name = target_date.strftime("%A")
        if weekday_name not in mapping:
            # No column for this weekday
            return []

        col_idx = mapping[weekday_name]
        programmes = []

        # iterate rows after header
        for row in rows[header_idx+1:]:
            if len(row) <= time_col:
                continue
            time_cell = row[time_col].strip() if row[time_col] else ""
            if not time_cell:
                continue
            m = self.TIME_RANGE_RE.match(time_cell)
            if not m:
                # skip rows that are not time ranges
                continue
            start_str = m.group('start').strip()
            end_str = m.group('end').strip()

            # get title at col_idx if present
            title = ""
            if len(row) > col_idx:
                title = row[col_idx].strip()
            if not title:
                continue  # empty cell means no program scheduled here

            try:
                start_time = self.parse_time_str(start_str)
                end_time = self.parse_time_str(end_str)
            except ValueError as ex:
                print(f"Warning: skipping row with unparseable time '{time_cell}': {ex}", file=sys.stderr)
                continue

            # combine with target_date in sheet tz
            start_dt = datetime.combine(target_date, start_time)
            end_dt = datetime.combine(target_date, end_time)

            # if end <= start, it likely crosses midnight -> add one day to end
            if end_dt <= start_dt:
                end_dt = end_dt + timedelta(days=1)

            # attach tzinfo (sheet tz)
            start_dt = start_dt.replace(tzinfo=SHEET_TZ)
            end_dt = end_dt.replace(tzinfo=SHEET_TZ)

            programmes.append({
                "title": title,
                "start_central": start_dt,
                "end_central": end_dt
            })
        return programmes

    def to_xmltv_datetime(self, dt):
        """
        Convert a timezone-aware datetime to XMLTV format: YYYYMMDDHHMMSS +/-ZZZZ
        dt must be timezone-aware
        """
        return dt.strftime("%Y%m%d%H%M%S %z")

    def generate_xml(self, programme_entries, output_file):
        """
        programme_entries: list of dicts containing:
        - start_eastern (tz-aware)
        - end_eastern (tz-aware)
        - title
        """
        tv = ET.Element("tv")
        # channel block
        ch = ET.SubElement(tv, "channel", id=CHANNEL_ID)
        dn = ET.SubElement(ch, "display-name")
        dn.text = CHANNEL_NAME

        for p in programme_entries:
            start_attr = self.to_xmltv_datetime(p["start_eastern"])
            stop_attr = self.to_xmltv_datetime(p["end_eastern"])
            prog = ET.SubElement(tv, "programme", start=start_attr, stop=stop_attr, channel=CHANNEL_ID)
            t = ET.SubElement(prog, "title")
            t.text = p["title"]
            d = ET.SubElement(prog, "desc")
            d.text = ""  # blank as requested

        # produce pretty XML string (with declaration)
        xml_bytes = ET.tostring(tv, encoding="utf-8")
        # ET.tostring doesn't pretty-print. We'll write a simple header + bytes.
        header = b'<?xml version="1.0" encoding="utf-8"?>\n'
        with open(output_file, "wb") as f:
            f.write(header)
            f.write(xml_bytes)

    def main(self):
        print("Fetching CSV...")
        csv_text = self.fetch_csv(CSV_URL)
        rows = self.csv_to_rows(csv_text)
        if not rows:
            print("Empty CSV. Exiting.", file=sys.stderr)
            return

        try:
            header_idx, mapping, time_col = self.find_header_and_columns(rows)
        except Exception as e:
            print("Error locating header/weekday columns:", e, file=sys.stderr)
            return

        # Build target dates: today + next 2 days
        today_local = datetime.now(tz=OUTPUT_TZ).date()
        target_dates = [ today_local + timedelta(days=i) for i in range(EPG_DAYS) ]
        print("Target dates:", ", ".join(d.isoformat() for d in target_dates))

        all_programmes = []
        for d in target_dates:
            progs = self.build_programmes_for_date(rows, header_idx, mapping, time_col, d)
            # Convert each programme from sheet tz -> output tz
            for p in progs:
                start_eastern = p["start_central"].astimezone(OUTPUT_TZ)
                end_eastern = p["end_central"].astimezone(OUTPUT_TZ)
                all_programmes.append({
                    "title": p["title"],
                    "start_eastern": start_eastern,
                    "end_eastern": end_eastern
                })

        # Sort by start time
        all_programmes.sort(key=lambda x: x["start_eastern"])

        print(f"Generating {len(all_programmes)} programmes into {OUTPUT_FILE} ...")
        self.generate_xml(all_programmes, f'xml_schedules/{OUTPUT_FILE}')
        print("Done.")

