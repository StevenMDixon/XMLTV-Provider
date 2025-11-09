import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
import requests
import json

url = "https://api.toonamiaftermath.com/media?scheduleName=Toonami%20Aftermath%20EST&dateString=2025-11-09T11%3A00%3A00Z&count=40"

response = requests.get(url, verify=False)

# Check the status code (200 indicates success)
print(f"Status Code: {response.status_code}")

# Access the response content
if response.status_code == 200:
    print(f"Content (text): {response.text}")
    # If the response is JSON, you can parse it directly
    print(f"Content (JSON): {response.json()}")
else:
    print("Request failed.")

# --- CONFIG ---
INPUT_JSON = "shows.json"     # Input JSON file
OUTPUT_XML = "xmltv.xml"      # Output XMLTV file
CHANNEL_ID = "toonami"
CHANNEL_NAME = "Toonami"

shows = response.json()

# --- SORT SHOWS BY START TIME ---
shows.sort(key=lambda x: x["startDate"])

# --- CREATE ROOT ELEMENT ---
tv = ET.Element("tv")

# --- DEFINE CHANNEL ---
channel = ET.SubElement(tv, "channel", id=CHANNEL_ID)
ET.SubElement(channel, "display-name").text = CHANNEL_NAME

# --- HELPER FUNCTION ---
def iso_to_xmltv(iso_str):
    """Convert ISO 8601 string to XMLTV timestamp (YYYYMMDDHHMMSS +0000)"""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%Y%m%d%H%M%S +0000")

def escape_text(text):
    """Escape characters invalid in XML"""
    if text:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text

# --- GENERATE PROGRAMMES ---
for i, show in enumerate(shows):
    start = iso_to_xmltv(show["startDate"])
    
    # Stop time = start of next show, or add 12 min for last show
    if i + 1 < len(shows):
        stop = iso_to_xmltv(shows[i + 1]["startDate"])
    else:
        dt_start = datetime.fromisoformat(show["startDate"].replace("Z", "+00:00"))
        dt_stop = dt_start + timedelta(minutes=12)
        stop = dt_stop.strftime("%Y%m%d%H%M%S +0000")

    prog = ET.SubElement(tv, "programme", start=start, stop=stop, channel=CHANNEL_ID)

    # Title
    title_text = show.get("info", {}).get("fullname") or show.get("name")
    ET.SubElement(prog, "title").text = escape_text(title_text)

    # Description / episode info
    episode_text = show.get("info", {}).get("episode")
    if episode_text:
        ET.SubElement(prog, "desc").text = escape_text(episode_text)

    # Episode number
    ep_num = show.get("episodeNumber")
    if ep_num is not None:
        ET.SubElement(prog, "episode-num", system="xmltv_ns").text = str(ep_num)

    # Icon (image)
    image_url = show.get("info", {}).get("image")
    if image_url:
        ET.SubElement(prog, "icon", src=image_url)

# --- WRITE XML WITH DECLARATION AND FORMATTING ---
rough_string = ET.tostring(tv, encoding="utf-8")
reparsed = xml.dom.minidom.parseString(rough_string)
pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

with open(OUTPUT_XML, "wb") as f:
    f.write(pretty_xml)

print(f"XMLTV file generated: {OUTPUT_XML}")