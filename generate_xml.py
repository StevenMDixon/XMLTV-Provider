
from channels.rewind import RewindChannel
from channels.aftermath import AftermathChannel

import os

folder_path = "./xml_schedules"  # Define the path for the folder to be created

# Use os.makedirs with exist_ok=True
os.makedirs(folder_path, exist_ok=True)


channels = [RewindChannel(), AftermathChannel()]

for channel in channels:
    channel.handle_conversion()

