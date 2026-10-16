from channels.tv_passport_channel import tv_passport_channel
from channels.rewind import RewindChannel
from channels.aftermath import AftermathChannel
from utils.XMLConversion import XMLGenerator

from dotenv import load_dotenv
import os
import json

load_dotenv()

tvg_api_key = os.getenv("TVG_API_KEY")

print(f"TV Guide API Key: {tvg_api_key}")

folder_path = "./xml_schedules"  # Define the path for the folder to be created
os.makedirs(folder_path, exist_ok=True)

channels = [
    RewindChannel(XMLGenerator),
    AftermathChannel(XMLGenerator),
]

with open('./channels.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    print(f"Loaded channel data: {data}")
    for channel in data:
        print(channel)
        channels.append(tv_passport_channel(XMLGenerator, file_data=channel))

for channel in channels:
    try:
        channel.handle_conversion()
    except Exception as e:
        print(f"Error processing channel {channel}: {e}")
