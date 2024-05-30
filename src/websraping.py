import os
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import subprocess


#download all resources from an atom feed
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



#download all a_href resources from a html page
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



#load all *.xml files from a folder and compile them into a geopackage file
def gml_to_geopackage(gml_folder, geopackage_file, target_epsg):
    # Create a list of all GML files in the directory
    gml_files = [os.path.join(gml_folder, f) for f in os.listdir(gml_folder) if f.endswith('.xml')]
    
    # Check if there are any GML files to process
    if not gml_files:
        print("No GML files found in the specified directory.")
        return

    # Define the command to convert GML to GeoPackage and reproject to the target EPSG
    for i, gml_file in enumerate(gml_files):
        if i == 0:
            # For the first file, create a new GeoPackage
            command = [
                'ogr2ogr',
                '-f', 'GPKG',
                '-t_srs', f'EPSG:{target_epsg}',
                geopackage_file,
                gml_file
            ]
        else:
            # For subsequent files, append to the existing GeoPackage
            command = [
                'ogr2ogr',
                '-f', 'GPKG',
                '-t_srs', f'EPSG:{target_epsg}',
                '-append',
                geopackage_file,
                gml_file
            ]
        
        # Run the command
        subprocess.run(command, check=True)
        print(f"Processed {gml_file} into {geopackage_file}")


# CZ
#gml_to_geopackage("/home/juju/geodata/CZ/downloads/", "/home/juju/geodata/CZ/bu.gpkg", 3035)

# CZ
#download_links_from_html("/home/juju/geodata/CZ/services.cuzk.cz.html", "/home/juju/geodata/CZ/downloads/")

# CZ BU.xml
#download_atom_links("/home/juju/geodata/CZ/BU.xml", "/home/juju/geodata/CZ/BU_xml_downloads/")
