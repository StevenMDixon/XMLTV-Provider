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

# Load JSON data from file
data = response.json()

# Sort shows by startDate just in case
data.sort(key=lambda x: x["startDate"])

# Create root element
tv = ET.Element("tv")

# Define single channel
channel_id = "toonami"
channel = ET.SubElement(tv, "channel", id=channel_id)
ET.SubElement(channel, "display-name").text = "Toonami"

# Helper to convert ISO time to XMLTV format
def iso_to_xmltv(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%Y%m%d%H%M%S +0000")

# Generate programmes
for i, show in enumerate(data):
    start = iso_to_xmltv(show["startDate"])
    
    # Determine stop time: start of next show, or add 12 min if last show
    if i + 1 < len(data):
        stop = iso_to_xmltv(data[i + 1]["startDate"])
    else:
        # Arbitrary 12 min for last show
        dt_start = datetime.fromisoformat(show["startDate"].replace("Z", "+00:00"))
        dt_stop = dt_start + timedelta(minutes=12)
        stop = dt_stop.strftime("%Y%m%d%H%M%S +0000")
    
    prog = ET.SubElement(tv, "programme", start=start, stop=stop, channel=channel_id)
    
    # Title
    title_text = show.get("info", {}).get("fullname") or show.get("name")
    ET.SubElement(prog, "title").text = title_text
    
    # Description: episode info
    episode_text = show.get("info", {}).get("episode")
    if episode_text:
        ET.SubElement(prog, "desc").text = episode_text
    
    # Episode number
    ep_num = show.get("episodeNumber")
    if ep_num is not None:
        ET.SubElement(prog, "episode-num", system="xmltv_ns").text = str(ep_num)
    
    # Icon
    image_url = show.get("info", {}).get("image")
    if image_url:
        ET.SubElement(prog, "icon", src=image_url)

# Write XML to file
tree = ET.ElementTree(tv)
tree.write("xmltv.xml", encoding="utf-8", xml_declaration=True)

print("XMLTV file generated: xmltv.xml")