import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import xml.dom.minidom
from zoneinfo import ZoneInfo

class XMLGenerator():
    def __init__(self):
        pass

    def convert_to_dto(show):
        pass

    def convert_to_xml(channel, shows):

        # Need output file

        # Need Channel Input 
        # ID & Name

        # --- CREATE ROOT ELEMENT ---
        tv = ET.Element("tv")

        # --- DEFINE CHANNEL ---
        channel_elem = ET.SubElement(tv, "channel", id=channel.CHANNEL_ID)
        ET.SubElement(channel_elem, "display-name").text = channel.CHANNEL_NAME

        # --- ADD PROGRAMMES ---
        for show in shows:  
            prog = ET.SubElement(tv, "programme", start=show.startDate, stop=show.endDate, channel=channel.CHANNEL_ID)

            ET.SubElement(prog, "title").text = XMLGenerator.escape_text(show.name)

            if show.description:
                ET.SubElement(prog, "desc").text = XMLGenerator.escape_text(show.description)
            else :
                ET.SubElement(prog, "desc").text = "No description available."

            if show.episodeNumber is not None:
                ET.SubElement(prog, "episode-num", system="xmltv_ns").text = str(show.episodeNumber)

            if show.iconUrl:
                ET.SubElement(prog, "icon", src=show.iconUrl)

        # --- WRITE XML WITH DECLARATION AND FORMATTING ---
        rough_string = ET.tostring(tv, encoding="utf-8")
        reparsed = xml.dom.minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

        with open("./xml_schedules/" + channel.OUTPUT_XML, "wb") as f:
            f.write(pretty_xml)

        print(f"XMLTV file generated: {channel.OUTPUT_XML}")

    def iso_to_xmltv(iso_str):
            """Convert ISO 8601 string to XMLTV timestamp (YYYYMMDDHHMMSS +0000)"""
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return dt.strftime("%Y%m%d%H%M%S +0000")
    
    def xmltv_dt(dt: datetime):
            return dt.astimezone(ZoneInfo("UTC")).strftime("%Y%m%d%H%M%S +0000")
    
    def escape_text(text):
        """Escape characters invalid in XML"""
        if text:
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return text

    def weekday_name(dt):
        return dt.strftime("%A")  # Monday, Tuesday, etc.
