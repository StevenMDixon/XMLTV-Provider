import xml.etree.ElementTree as ET
import os

def merge_epg_files(input_files, output_file):
    """
    Combines multiple XMLTV EPG files into a single valid XMLTV file.
    
    :param input_files: List of paths to individual input EPG XML files
    :param output_file: Path where the merged EPG XML will be saved
    """
    if not input_files:
        print("No input files provided.")
        return

    print(f"Initializing merge. Root source: {input_files[0]}")
    
    try:
        # Load the first file to preserve the correct root <tv> element and attributes
        tree = ET.parse(input_files[0])
        root = tree.getroot()
    except Exception as e:
        print(f"Error reading base file {input_files[0]}: {e}")
        return

    # Track distinct channel IDs to filter out exact duplicates
    existing_channels = {ch.get('id') for ch in root.findall('channel') if ch.get('id')}

    # Process remaining XMLTV files
    for file_path in input_files[1:]:
        if not os.path.exists(file_path):
            print(f"Skipping missing file: {file_path}")
            continue
            
        print(f"Merging: {file_path}")
        try:
            sub_tree = ET.parse(file_path)
            sub_root = sub_tree.getroot()
            
            # 1. Append new channels (skipping duplicates)
            for channel in sub_root.findall('channel'):
                ch_id = channel.get('id')
                if ch_id and ch_id not in existing_channels:
                    existing_channels.add(ch_id)
                    root.append(channel)
                    
            # 2. Append all programmes
            for programme in sub_root.findall('programme'):
                root.append(programme)
                
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")

    # Write the compiled tree back into a standard formatted XMLTV file
    try:
        # XMLTV files typically require a specific doctype declaration
        tree.write(output_file, encoding='utf-8', xml_declaration=True, method='xml')
        print(f"Successfully generated merged EPG file at: {output_file}")
    except Exception as e:
        print(f"Error writing the consolidated EPG output: {e}")
