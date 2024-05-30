import os
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse


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




def download_links_from_html(html_file, download_folder):
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Create the download folder if it doesn't exist
    if not os.path.exists(download_folder): os.makedirs(download_folder)

    # Find all 'a' elements and extract href attributes
    links = soup.find_all('a', href=True)
    for link in links:
        url = link['href']

        # Parse the URL to ensure a valid file name
        parsed_url = urlparse(url)
        file_name = os.path.basename(parsed_url.path)
        
        # If the URL path ends with a slash, use a default file name
        if not file_name: file_name = "default_download"

        # Join the download folder path and file name
        file_path = os.path.join(download_folder, file_name)

        # Download the resource
        try:
            response = requests.get(url)
            # Raise an error for bad status codes
            response.raise_for_status()
            # save
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded {url} to {file_path}")
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")

# Usage example
download_links_from_html("/home/juju/geodata/CZ/services.cuzk.cz.html", "/home/juju/geodata/CZ/downloads/")


# CZ BU.xml
#download_atom_links("/home/juju/geodata/CZ/BU.xml", "/home/juju/geodata/CZ/BU_xml_downloads/")
