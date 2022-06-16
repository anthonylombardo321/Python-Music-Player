# Python Music Player
Python Project mainly coded with **Tkinter** and **Pygame** (for music playback functionality)

![playerScreenshot](https://i.gyazo.com/68cd448847d5c1b0ad0028b4089e9290.png)

## Features
- Control Keybinds
- Tag Editor (Manual and Automatic)
  - Automatic Tag Editor uses a web scraper to scrape tags from *MusicBrainz.org*
- Add/Remove Songs
- Repeat Song
- Shuffle Songs
- Play Songs by Artist
- Play Songs by Genre
- Sort List by Column (Title, Artist, Duration, Year, Genre, etc.)

## Controls
- &#x2191; - Increase Volume
- &#x2193; - Decrease Volume
- **M** - Mute
- &#x2192; - Forward 5 seconds
- &#x2190; - Back 5 seconds

- **SPACE** - Play/Pause Song
- **S** - Stop Song
- **P** - Play Previous Song in List
- **N** - Play Next Song in List

## Play Songs by Artist
![ArtistScreenshot](https://i.gyazo.com/c9a741467b6e677a6f23cf0ce7b2be40.png)

## Play Songs by Genre
![ArtistScreenshot](https://i.gyazo.com/4703dc9fa758e75ff718cc64f79c6109.png)

## Edit Tags Manually
**Note:** The song you want to edit tags on must not be playing.
1. Right Click on the song you want to edit tags on.
2. Click on *Add Tags Manually*.
![ManualTagEditorRightClick](https://i.imgur.com/R7R9t0p.png)
3. In the window, edit song title, artist, album, genre, year fields.
![ManualTagEditor](https://i.gyazo.com/38e24020f8de8331648326724054e03c.png)
* You can also add JPEG/JPG/PNG file for the Album Art or save the album art image stored in the file.
4. Click *Apply* to save changes.

## Edit Tags Automatically
**Note:** The song you want to edit tags on must not be playing.
1. Right Click on the song you want to edit tags on.
2. Click on *Add Tags Automatically*.
![AutomaticTagEditorRightClick](https://i.imgur.com/58I2ViZ.png)
3. In the window, fill in the title and artist fields (If the song does not have a title and artist tag) and the number of tags you want the program to return.
![AutomaticTagEditor](https://i.gyazo.com/34df1b9890e7ee593110737e8990f614.png)
* **Note:**  If the window is not responding, **DON'T PANIC!** Due to the web scraper going through numerous pages, the program will take a minute, at least, to return the default number of tags from the MusicBrainz site.
4. Select a tag from the list and click *Apply Tags from Selected Result* to save changes.
