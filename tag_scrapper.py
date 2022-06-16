"""
    Song Tag Scrapper:
    This script scrapes metadata from the website: musicbrainz.org, if it matches the search terms (title string and artist string) provided by the user.
    If the search terms matches any of the results, the scraper grabs the title, artist, album, genre, year, and album art (if provided by the website) before adding them to a list as a tag result.
    At the end of the function, it returns the list of song tag results.
"""
import requests
from bs4 import BeautifulSoup

def scrape_song_tags(song_title, song_artist, total_tag_count):
    # This converts the total count into an int, if the count is not ""
    if total_tag_count.isdigit():
        total_tag_count = int(total_tag_count)

    search_query = f"{song_title} - {song_artist}" if song_artist else song_title
    search_query = search_query.replace(" ", "+")
    page = requests.get(f"https://musicbrainz.org/search?query={search_query}&type=recording&method=indexed")
    soup = BeautifulSoup(page.content, "lxml")

    song_links = []
    odd_results = soup.find_all(class_="odd")
    even_results = soup.find_all(class_="even")
    results = odd_results + even_results
    for result in results:
        # Collects Recordings that match title and artist
        result_cells = result.find_all("td")
        title = result_cells[0].find("a")
        artist = result_cells[2].find("a")
        if title is not None and song_title.casefold() in title.text.casefold():
            if song_artist == "":
                song_links.append(title["href"])
            elif artist is not None and song_artist.casefold() in artist.text.casefold():
                song_links.append(title["href"])

    song_tags = []
    tags_added_count = 0
    for link in song_links:
        if tags_added_count == total_tag_count:
            break

        page = requests.get(f"https://musicbrainz.org{link}")
        soup = BeautifulSoup(page.content, "lxml")
        odd_results = soup.find_all(class_="odd")
        even_results = soup.find_all(class_="even")
        results = odd_results + even_results

        for result in results:
            if tags_added_count == total_tag_count:
                break
            # Grabs Song Details
            result_cells = result.find_all("td")
            title = result_cells[1].text
            artist = result_cells[3].text
            album_art_link = result_cells[4].find("a")
            album = album_art_link.text
            year = result.find(class_="release-date")
            year = year.text.split("-")[0] if year else ""
            genre = soup.find(class_="genre-list").find("p").find_all("a")
            genre = genre[0].text.capitalize() if genre else ""

            # Grabs Album Art Link
            album_art_page = requests.get(f'https://musicbrainz.org{album_art_link["href"]}')
            album_art_soup = BeautifulSoup(album_art_page.content, "lxml")
            album_art = album_art_soup.find(class_="cover-art-image")  # Grabs main album art image
            album_art = f'https:{album_art["data-huge-thumbnail"]}' if album_art is not None else ""
            album_art_note = album_art_soup.find(class_="cover-art-note")  # If not found, checks for backup image
            album_art_note = album_art_note.find("a") if album_art_note is not None else None
            if album_art_note is not None:
                if album_art_note.text == "Amazon":
                    album_art = album_art_note["href"]
                else:
                    album_art_page = requests.get(f'https://musicbrainz.org{album_art_note["href"]}')
                    album_art_soup = BeautifulSoup(album_art_page.content, "html.parser")
                    album_art = album_art_soup.find(class_="cover-art-image")["data-huge-thumbnail"]
                    album_art = f'http:{album_art}'

            # If a link is present, extract data from link
            if album_art:
                album_art_download = requests.get(album_art)
                if album_art_download.status_code == 200:
                    album_art = album_art_download.content
            song_tags.append([album_art, title, artist, album, year, genre])
            tags_added_count += 1

    return song_tags
