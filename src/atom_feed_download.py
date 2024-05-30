import feedparser
import requests
import os

def download_atom_links(atom_file, download_folder):
    # Parse the Atom feed
    feed = feedparser.parse(atom_file)

    # Create download folder if it doesn't exist
    if not os.path.exists(download_folder): os.makedirs(download_folder)

    # Iterate through each entry in the feed
    for entry in feed.entries:
        # Get the link URL
        link = entry.link
        # Download the resource
        try:
            response = requests.get(link)
            response.raise_for_status()  # Raise an error for bad status codes
            # Determine the file name
            file_name = os.path.join(download_folder, os.path.basename(link))
            # Save the file
            with open(file_name, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded {link} to {file_name}")
        except requests.RequestException as e:
            print(f"Failed to download {link}: {e}")


# CZ BU.xml
download_atom_links("/home/juju/geodata/CZ/BU.xml", "/home/juju/geodata/CZ/BU_xml_downloads/")
