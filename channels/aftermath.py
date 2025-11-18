import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
import requests
import json
import xml.dom.minidom

from utils.showDTO import ShowDTO

class AftermathChannel:
    def __init__(self, xml_generator = None):
        self.OUTPUT_XML = "toonami.xml"      # Output XMLTV file
        self.CHANNEL_ID = "toonami"
        self.CHANNEL_NAME = "Toonami"

        today = datetime.now().date()
        self.url = f"https://api.toonamiaftermath.com/media?scheduleName=Toonami%20Aftermath%20EST&dateString={today}T11%3A00%3A00Z&count=100"
        
        self.generator = xml_generator

    def fetch_shows(self):
        response = requests.get(self.url, verify=False)

        print(f"Status Code: {response.status_code}")

        # Access the response content
        if response.status_code == 200:
            return response.json()
        else:
            print("Request failed.")
            return []
        
    def handle_conversion(self):
        shows = self.fetch_shows()

        if not shows:
            print("No shows to convert.")
            return
        
        self.convert(shows)
        
    def convert(self, shows):
        shows.sort(key=lambda x: x["startDate"])

        converted_shows = []

        for i, show in enumerate(shows):
            start = self.generator.iso_to_xmltv(show["startDate"])
            
            # Stop time = start of next show, or add 12 min for last show
            if i + 1 < len(shows):
                stop = self.generator.iso_to_xmltv(shows[i + 1]["startDate"])
            else:
                dt_start = datetime.fromisoformat(show["startDate"].replace("Z", "+00:00"))
                dt_stop = dt_start + timedelta(minutes=12)
                stop = dt_stop.strftime("%Y%m%d%H%M%S +0000")

            title_text = show.get("info", {}).get("fullname") or show.get("name")

            episode_text = show.get("info", {}).get("episode")

            ep_num = show.get("episodeNumber")

            image_url = show.get("info", {}).get("image")

            converted_shows.append(
                ShowDTO(
                name=title_text,
                startDate=start,
                endDate=stop,
                description=episode_text,
                episodeNumber=ep_num,
                iconUrl=image_url
                )
            )

        self.generator.convert_to_xml(self, converted_shows)