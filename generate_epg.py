
from channels.rewind import RewindChannel
from channels.aftermath import AftermathChannel
from utils.XMLConversion import XMLGenerator
from channels.cneast import CNEastChannel
from channels.aseast import ASEastChannel
from channels.nickeast import NickEastChannel

from dotenv import load_dotenv
import os

load_dotenv()

tvg_api_key = os.getenv("TVG_API_KEY")

print(f"TV Guide API Key: {tvg_api_key}")

folder_path = "./xml_schedules"  # Define the path for the folder to be created
os.makedirs(folder_path, exist_ok=True)

channels = [
    RewindChannel(XMLGenerator),
    AftermathChannel(XMLGenerator),
    ASEastChannel(XMLGenerator, tvg_api_key=tvg_api_key),
    CNEastChannel(XMLGenerator, tvg_api_key=tvg_api_key),
    NickEastChannel(XMLGenerator, tvg_api_key=tvg_api_key),
]

for channel in channels:
    try:
        channel.handle_conversion()
    except Exception as e:
        print(f"Error processing channel {channel}: {e}")
