
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URL of the directory containing the MP4 files
BASE_URL = "https://xnadmin.salesstarnetworks.com/recordings/calls/"
DOWNLOAD_DIR = "downloaded_mp4s"

def get_mp4_links(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    mp4_links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.lower().endswith('.mp4'):
            mp4_links.append(urljoin(url, href))
    return mp4_links

def download_file(url, dest_folder):
    local_filename = os.path.join(dest_folder, url.split('/')[-1])
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded: {local_filename}")

def main():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    mp4_links = get_mp4_links(BASE_URL)
    if not mp4_links:
        print("No MP4 files found at the specified URL.")
        return
    for link in mp4_links:
        download_file(link, DOWNLOAD_DIR)

if __name__ == "__main__":
    main()


