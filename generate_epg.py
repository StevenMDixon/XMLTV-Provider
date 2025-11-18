
from channels.rewind import RewindChannel
from channels.aftermath import AftermathChannel
from utils.XMLConversion import XMLGenerator

import os

folder_path = "./xml_schedules"  # Define the path for the folder to be created
os.makedirs(folder_path, exist_ok=True)

channels = [
    RewindChannel(XMLGenerator),
    AftermathChannel(XMLGenerator)
]

for channel in channels:
    try:
        channel.handle_conversion()
    except Exception as e:
        print(f"Error processing channel {channel}: {e}")
