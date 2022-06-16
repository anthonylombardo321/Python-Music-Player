import random
from PIL import ImageTk
import PIL.Image
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os.path
from io import BytesIO
import time
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, APIC, TPE1, TALB, TDRC, TCON
from mutagen import MutagenError
import pygame
from tag_scrapper import scrape_song_tags

# Dictionaries to store songs
song_dict = {}
artist_dict = {}
genre_dict = {}
album_art_images = []  # Stores custom album art images, so Python doesn't remove them after function completes
album_art_results = []  # Stores custom album art images from Automatic Tag Search
# =======================================================================================================================================================================
# Setting up the window
root = Tk()
root.title("Python Music Player")
root.iconphoto(True, PhotoImage(file="icons/Python Music Player Logo.png"))
root.geometry("800x600")

pygame.mixer.init()

# Creating Global Control Variables
paused = False
repeat = False
shuffle = False
stopped = False
muted = False
album_art_removed = False
currently_playing_song = ""
edit_album_art_tag = ""  # Used to store album art image within Song Tag Editor
album_art_path = ""  # Stores path of album art image if user adds an image through Song Tag Editor
# =======================================================================================================================================================================
# Custom scale where left click works like right click
class Scale(ttk.Scale):
    def __init__(self, master=None, **kwargs):
        ttk.Scale.__init__(self, master, **kwargs)
        self.bind('<Button-1>', self.set_value)

    def set_value(self, event):
        self.event_generate('<Button-3>', x=event.x, y=event.y)
        return 'break'

# Sorts column when column is clicked on
def treeview_sort_column(tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    l.sort(reverse=reverse)

    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    # reverse sort next time
    tv.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tv, _col, not reverse))
# =======================================================================================================================================================================
def right_click_song_menu(event):
    # Selects song item in tree based on mouse coordinates
    tree_list.selection_set(tree_list.identify_row(event.y))
    song_menu.post(event.x_root, event.y_root)

def return_to_list():
    if artist_button.cget("bg") == "green":
        set_artist_tree()
    elif genre_button.cget("bg") == "green":
        set_genre_tree()
# ==================================================================================================================================================
def set_song_tree():
    global tree_list
    global album_art_images
    # Reset album art images
    album_art_images = []

    # Remove everything from frame
    for widget in tree_frame.winfo_children():
        widget.destroy()

    # Create the list (with ascending/descending columns)
    columns = ("Title", "Artist", "Duration", "Album", "Year", "Genre")
    tree_list = ttk.Treeview(tree_frame, column=columns, selectmode="browse", height=5)

    # Managing Column Width and Height
    tree_list.column("#0", width=80)
    tree_list.column('Title', anchor="center", width=100)
    tree_list.column('Artist', anchor="center", width=100)
    tree_list.column('Duration', anchor="center", width=100)
    tree_list.column('Album', anchor="center", width=100)
    tree_list.column('Year', anchor="center", width=100)
    tree_list.column('Genre', anchor="center", width=100)
    row_height = ttk.Style().configure('Treeview', rowheight=50)

    # Setup column headings
    for col in columns:
        tree_list.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree_list, _col, False))

    # Appending Scroll Bars to TreeView
    horizontal_scroll_bar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree_list.xview)
    vertical_scroll_bar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_list.yview)
    tree_list.grid(in_=tree_frame, row=0, column=0, sticky=N + S + W + E)
    horizontal_scroll_bar.grid(row=1, column=0, sticky=W + E + S)
    vertical_scroll_bar.grid(row=0, column=1, sticky=N + S + W)

    tree_list.configure(xscrollcommand=horizontal_scroll_bar.set, yscrollcommand=vertical_scroll_bar.set)

    tree_list.bind("<Double-1>", play_song_click)
    tree_list.bind("<Button-3>", right_click_song_menu)

    # Change background color to match active button
    artist_button.config(bg="white")
    genre_button.config(bg="white")
    song_button.config(bg="green")

    # Check if dictionary holds songs
    if song_dict:
        for song in song_dict:
            insert_song(song_dict.get(song))
    else:
        count_label.config(text=f"Songs: 0")
# ==================================================================================================================================================
def set_artist_tree():
    global tree_list
    # Remove everything from frame
    for widget in tree_frame.winfo_children():
        widget.destroy()

    # Create the list (with ascending/descending columns)
    columns = ("Artist", "Count")
    tree_list = ttk.Treeview(tree_frame, column=columns, selectmode="browse", height=5,)

    # Managing Column Width and Height
    tree_list.column('Artist', anchor="center", width=340)
    tree_list.column('Count', anchor="center", width=340)
    row_height = ttk.Style().configure('Treeview', rowheight=50)
    tree_list["show"] = "headings"

    # Setup column headings
    for col in columns:
        tree_list.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree_list, _col, False))

    # Appending Scroll Bars to TreeView
    horizontal_scroll_bar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree_list.xview)
    vertical_scroll_bar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_list.yview)
    tree_list.grid(in_=tree_frame, row=0, column=0, sticky=N + S + W + E)
    horizontal_scroll_bar.grid(row=1, column=0, sticky=W + E + S)
    vertical_scroll_bar.grid(row=0, column=1, sticky=N + S + W)

    tree_list.configure(xscrollcommand=horizontal_scroll_bar.set, yscrollcommand=vertical_scroll_bar.set)

    tree_list.bind("<Double-1>", set_artist_song_list)

    # Change background color to match active button
    song_button.config(bg="white")
    genre_button.config(bg="white")
    artist_button.config(bg="green")

    # Check if dictionary holds artists
    if artist_dict:
        insert_artists()
    else:
        count_label.config(text=f"Artists: 0")


def insert_artists():
    for artist in artist_dict:
        count = len(artist_dict.get(artist))
        tree_list.insert('', 'end', values=(artist, count))
        count_label.config(text=f"Artists: {len(tree_list.get_children())}")

def set_artist_song_list(event):
    global tree_list
    global album_art_images
    artist_item = tree_list.focus()
    artist = tree_list.item(artist_item).get("values")[0]
    album_art_images = []

    # Remove everything from frame
    for widget in tree_frame.winfo_children():
        widget.destroy()

    # Create the list (with ascending/descending columns)
    columns = ("Title", "Artist", "Duration", "Album", "Year", "Genre")
    tree_list = ttk.Treeview(tree_frame, column=columns, selectmode="browse", height=5)

    # Managing Column Width and Height
    tree_list.column("#0", width=80)
    tree_list.column('Title', anchor="center", width=100)
    tree_list.column('Artist', anchor="center", width=100)
    tree_list.column('Duration', anchor="center", width=100)
    tree_list.column('Album', anchor="center", width=100)
    tree_list.column('Year', anchor="center", width=100)
    tree_list.column('Genre', anchor="center", width=100)
    row_height = ttk.Style().configure('Treeview', rowheight=50)

    # Setup column headings
    for col in columns:
        tree_list.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree_list, _col, False))

    # Appending Scroll Bars to TreeView
    horizontal_scroll_bar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree_list.xview)
    vertical_scroll_bar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_list.yview)
    tree_list.grid(in_=tree_frame, row=0, column=0, sticky=N + S + W + E)
    horizontal_scroll_bar.grid(row=1, column=0, sticky=W + E + S)
    vertical_scroll_bar.grid(row=0, column=1, sticky=N + S + W)

    tree_list.configure(xscrollcommand=horizontal_scroll_bar.set, yscrollcommand=vertical_scroll_bar.set)

    tree_list.bind("<Double-1>", play_song_click)
    tree_list.bind("<Button-3>", right_click_song_menu)

    song_button.config(bg="green")
    artist_button.config(bg="white")
    # Check if dictionary holds songs
    artist_list = artist_dict.get(artist)
    for song in artist_list:
        insert_song(song_dict.get(song))

    song_button.config(bg="white")
    artist_button.config(bg="green")
# ==================================================================================================================================================
def set_genre_tree():
    global tree_list
    # Remove everything from frame
    for widget in tree_frame.winfo_children():
        widget.destroy()

    # Create the list (with ascending/descending columns)
    columns = ("Genre", "Count")
    tree_list = ttk.Treeview(tree_frame, column=columns, selectmode="browse", height=5)

    # Managing Column Width and Height
    tree_list.column('Genre', anchor="center", width=340)
    tree_list.column('Count', anchor="center", width=340)
    row_height = ttk.Style().configure('Treeview', rowheight=50)
    tree_list["show"] = "headings"

    # Setup column headings
    for col in columns:
        tree_list.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree_list, _col, False))

    # Appending Scroll Bars to TreeView
    horizontal_scroll_bar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree_list.xview)
    vertical_scroll_bar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_list.yview)
    tree_list.grid(in_=tree_frame, row=0, column=0, sticky=N + S + W + E)
    horizontal_scroll_bar.grid(row=1, column=0, sticky=W + E + S)
    vertical_scroll_bar.grid(row=0, column=1, sticky=N + S + W)

    tree_list.configure(xscrollcommand=horizontal_scroll_bar.set, yscrollcommand=vertical_scroll_bar.set)

    # Change background color to match active button
    song_button.config(bg="white")
    artist_button.config(bg="white")
    genre_button.config(bg="green")

    # Check if dictionary holds genres
    if genre_dict:
        insert_genres()
    else:
        count_label.config(text=f"Genres: 0")

    tree_list.bind("<Double-1>", set_genre_song_list)

def insert_genres():
    for genre in genre_dict:
        count = len(genre_dict.get(genre))
        tree_list.insert('', 'end', values=(genre, count))
        count_label.config(text=f"Genres: {len(tree_list.get_children())}")

def set_genre_song_list(event):
    global tree_list
    global album_art_images
    genre_item = tree_list.focus()
    genre = tree_list.item(genre_item).get("values")[0]
    album_art_images = []

    # Remove everything from frame
    for widget in tree_frame.winfo_children():
        widget.destroy()

    # Create the list (with ascending/descending columns)
    columns = ("Title", "Artist", "Duration", "Album", "Year", "Genre")
    tree_list = ttk.Treeview(tree_frame, column=columns, selectmode="browse", height=5)

    # Managing Column Width and Height
    tree_list.column("#0", width=80)
    tree_list.column('Title', anchor="center", width=100)
    tree_list.column('Artist', anchor="center", width=100)
    tree_list.column('Duration', anchor="center", width=100)
    tree_list.column('Album', anchor="center", width=100)
    tree_list.column('Year', anchor="center", width=100)
    tree_list.column('Genre', anchor="center", width=100)
    row_height = ttk.Style().configure('Treeview', rowheight=50)

    # Setup column headings
    for col in columns:
        tree_list.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree_list, _col, False))

    # Appending Scroll Bars to TreeView
    horizontal_scroll_bar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree_list.xview)
    vertical_scroll_bar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_list.yview)
    tree_list.grid(in_=tree_frame, row=0, column=0, sticky=N + S + W + E)
    horizontal_scroll_bar.grid(row=1, column=0, sticky=W + E + S)
    vertical_scroll_bar.grid(row=0, column=1, sticky=N + S + W)

    tree_list.configure(xscrollcommand=horizontal_scroll_bar.set, yscrollcommand=vertical_scroll_bar.set)

    tree_list.bind("<Double-1>", play_song_click)
    tree_list.bind("<Button-3>", right_click_song_menu)

    song_button.config(bg="green")
    genre_button.config(bg="white")
    # Check if dictionary holds songs
    genre_list = genre_dict.get(genre)
    for song in genre_list:
        insert_song(song_dict.get(song))

    song_button.config(bg="white")
    genre_button.config(bg="green")
# ==================================================================================================================================================
def add_songs():
    song_locations = filedialog.askopenfilenames(title="Choose Songs", filetypes=[("Audio files", ".mp3")])
    for song in song_locations:
        insert_song(song)

def get_album_art(song_tags, width, height):
    if song_tags.get("APIC:"):
        album_art_data = song_tags.get("APIC:").data
        album_art_img = PIL.Image.open(BytesIO(album_art_data)).resize((width, height))
        album_art = ImageTk.PhotoImage(album_art_img)
        return album_art
    else:
        album_art_img = PIL.Image.open("icons/Default Album Art.jpg").resize((width, height))
        album_art = ImageTk.PhotoImage(album_art_img)
        return album_art

def insert_song(song_location):
    global album_art_images
    try:
        song = MP3(song_location)
    except MutagenError:
        print("MP3 not encoded correctly. Use online-audio-converter.com to convert your file and try again")
    try:
        song_tags = ID3(song_location)
    except MutagenError:
        print("Song Has No Tag Encoding")

    # Encodes a Title Tag to MP3 if missing
    try:
        song_title = str(song["TIT2"])
    except KeyError:
        song.tags = ID3()
        song.tags["TIT2"] = TIT2(encoding=3, text=os.path.basename(song_location).split(".")[0])
        song.save(v1=0)
        song_title = str(song["TIT2"])

    # Song is already in list, leave function (Prevents duplicates)
    if tree_list.get_children():
        for item in tree_list.get_children():
            child_song_name = tree_list.item(item)["values"][0]
            if song_title == child_song_name:
                return

    if song_tags.get("APIC:"):
        album_art_images.append(get_album_art(song_tags, 50, 50))
    else:
        album_art_images.append(get_album_art(song_tags, 50, 50))
    try:
        title = song["TIT2"]
    except KeyError:
        title = os.path.basename(song_location).split(".")[0]
    try:
        artist = song["TPE1"]
    except KeyError:
        artist = ""
    duration = time.strftime('%M:%S', time.gmtime(song.info.length))
    try:
        album = song["TALB"]
    except KeyError:
        album = ""
    try:
        year = song["TDRC"]
    except KeyError:
        year = ""
    try:
        genre = song["TCON"]
    except KeyError:
        genre = ""

    song_dict.update({str(title): song_location})  # Updating Song Dictionary
    # Updating Artist Dictionary
    if artist == "" and "Unknown" not in artist_dict:
        artist_dict.update({"Unknown": [str(title)]})
    elif artist == "" and "Unknown" in artist_dict:
        artist_list = artist_dict.get("Unknown")
        if str(title) not in artist_list:
            artist_list.append(str(title))
        artist_dict.update({"Unknown": artist_list})
    elif str(artist) not in artist_dict:
        artist_dict.update({str(artist): [str(title)]})
    else:
        artist_list = artist_dict.get(str(artist))
        if str(title) not in artist_list:
            artist_list.append(str(title))
        artist_dict.update({str(artist): artist_list})

    # Updating Genre Dictionary
    if genre == "" and "Unknown" not in genre_dict:
        genre_dict.update({"Unknown": [str(title)]})
    elif genre == "" and "Unknown" in genre_dict:
        genre_list = genre_dict.get("Unknown")
        if str(title) not in genre_list:
            genre_list.append(str(title))
        genre_dict.update({"Unknown": genre_list})
    elif str(genre) not in genre_dict:
        genre_dict.update({str(genre): [str(title)]})
    else:
        genre_list = genre_dict.get(str(genre))
        if str(title) not in genre_list:
            genre_list.append(str(title))
        genre_dict.update({str(genre): genre_list})

    if artist_button.cget("bg") == "green":
        try:
            tree_list.insert('', 'end', values=(artist, len(artist_dict.get(str(artist)))))
            count_label.config(text=f"Artists: {len(tree_list.get_children())}")
        except TypeError:
            tree_list.insert('', 'end', values=("Unknown", len(artist_dict.get("Unknown"))))
            count_label.config(text=f"Artists: {len(tree_list.get_children())}")
    elif genre_button.cget("bg") == "green":
        try:
            tree_list.insert('', 'end', values=(genre, len(genre_dict.get(str(genre)))))
            count_label.config(text=f"Genres: {len(tree_list.get_children())}")
        except TypeError:
            tree_list.insert('', 'end', values=("Unknown", len(genre_dict.get("Unknown"))))
            count_label.config(text=f"Genres: {len(tree_list.get_children())}")
    elif song_button.cget("bg") == "green":
        tree_list.insert('', 'end', image=album_art_images[len(tree_list.get_children())], values=(title, artist, duration, album, year, genre))
        count_label.config(text=f"Songs: {len(tree_list.get_children())}")

def remove_song(chosen_song):
    global currently_playing_song
    if not chosen_song:
        messagebox.showerror("Error", "Select a Song to Remove First")
    else:
        # Get Song Details
        song_title = tree_list.item(chosen_song).get("values")[0]
        song_artist = tree_list.item(chosen_song).get("values")[1]
        song_genre = tree_list.item(chosen_song).get("values")[5]

        # Stops song if the removed song is the same as the song playing
        chosen_song_file = song_dict.get(song_title)
        if chosen_song_file == currently_playing_song:
            stop_song()
            currently_playing_song = ""

        # Remove Song from Dictionaries
        song_dict.pop(song_title)
        if song_artist == "":
            artist_song_list = artist_dict.get("Unknown")
            artist_song_list.remove(song_title)
            if not artist_song_list:
                artist_dict.pop("Unknown")
        else:
            artist_song_list = artist_dict.get(song_artist)
            artist_song_list.remove(song_title)
            if not artist_song_list:
                artist_dict.pop(song_artist)
        if song_genre == "":
            genre_song_list = genre_dict.get("Unknown")
            genre_song_list.remove(song_title)
            if not genre_song_list:
                genre_dict.pop("Unknown")
        else:
            genre_song_list = genre_dict.get(song_genre)
            genre_song_list.remove(song_title)
            if not genre_song_list:
                genre_dict.pop(song_genre)

        # Resets Treeview based on active button
        if song_button.cget("bg") == "green":
            set_song_tree()
        elif artist_button.cget("bg") == "green":
            set_artist_tree()
        elif genre_button.cget("bg") == "green":
            set_genre_tree()
# ==================================================================================================================================================
# Manual Tag Editor Functions
def add_album_art_in_tag_window():
    global edit_album_art_tag
    global album_art_label
    global album_art_removed
    global album_art_path
    album_art_path = filedialog.askopenfilename(title="Choose Album Art Image", filetypes=[("Image files", ".png .jpg .jpeg")])
    manual_tag_window.attributes("-topmost", 1)
    if album_art_path:
        album_art_img = PIL.Image.open(album_art_path).resize((128, 128))
        edit_album_art_tag = ImageTk.PhotoImage(album_art_img)
        album_art_label.config(image=edit_album_art_tag)
        album_art_removed = False

def remove_album_art_in_tag_window():
    global edit_album_art_tag
    global album_art_label
    global album_art_removed
    album_art_img = PIL.Image.open("icons/Default Album Art.jpg").resize((128, 128))
    edit_album_art_tag = ImageTk.PhotoImage(album_art_img)
    album_art_label.config(image=edit_album_art_tag)
    album_art_removed = True

def save_album_art(chosen_song):
    chosen_song = ID3(chosen_song)
    try:
        album_art_data = chosen_song.get("APIC:").data
        album_art_save_path = filedialog.asksaveasfilename(title="Save Album Art as...", defaultextension="*.png", initialfile="Default Album Art.png", filetypes=[("PNG File", "*.png"), ("JPEG File", "*.jpg *.jpeg")])
        manual_tag_window.attributes("-topmost", 1)
        if album_art_save_path:
            with open(album_art_save_path, 'wb') as f:
                f.write(album_art_data)
    except AttributeError:
        messagebox.showerror("Error", "Album Art Not Found")

def apply_tags_to_song(chosen_song, title, artist, genre, album, year):
    global song_dict
    try:
        song_tags = ID3(chosen_song)
        if album_art_path:
            album_art_extension = os.path.basename(album_art_path).split(".")[1]
            if album_art_extension == "jpg":
                album_art_extension = "jpeg"
            with open(album_art_path, "rb") as album_art:
                song_tags["APIC"] = APIC(
                    encoding=3,
                    mime=f"image/{album_art_extension}",
                    type=3,
                    data=album_art.read()
                )
        if album_art_removed:
            song_tags.setall("APIC", [])  # Clears Artwork from song file
        song_tags["TIT2"] = TIT2(
            encoding=3,
            text=title
        )
        song_tags["TPE1"] = TPE1(
            encoding=3,
            text=artist
        )
        song_tags["TCON"] = TCON(
            encoding=3,
            text=genre
        )
        song_tags["TALB"] = TALB(
            encoding=3,
            text=album
        )
        song_tags["TDRC"] = TDRC(
            encoding=3,
            text=year
        )
        song_tags.save()

        # Replace key in song_dict with new song title
        song_title_index = list(song_dict.values()).index(chosen_song)
        song_dict_list = list(song_dict.keys())
        song_title = song_dict_list[song_title_index]
        song_dict_list[song_title_index] = title
        song_dictionary = {}
        for i in range(len(song_dict_list)):
            song_dictionary.update({song_dict_list[i]: list(song_dict.values())[i]})
        song_dict = song_dictionary

        # Remove song from artist_dict and genre_dict
        artist_dict_key = ""
        genre_dict_key = ""

        index = 0
        for value in list(artist_dict.values()):
            for song in value:
                if song_title == song:
                    artist_dict_key = list(artist_dict.keys())[index]
            index += 1

        index = 0
        for value in list(genre_dict.values()):
            for song in value:
                if song_title == song:
                    genre_dict_key = list(genre_dict.keys())[index]
            index += 1

        if artist_dict_key and genre_dict_key:
            artist_dict.pop(artist_dict_key)
            genre_dict.pop(genre_dict_key)

        exit_manual_tag_window()
    except MutagenError:
        # Informs User that Song Tags can't be applied to song
        applied_tags_label = Label(applied_tags_frame, text="Song can't be edited if song is playing.\nStop or play a different song before trying again.", fg="red")
        applied_tags_label.pack(pady=10)
        applied_tags_label.after(3000, lambda: applied_tags_label.destroy())

def exit_manual_tag_window():
    global manual_tag_window
    global album_art_removed
    manual_tag_window.destroy()
    album_art_removed = False

    # Resets Treeview based on active button
    if song_button.cget("bg") == "green":
        set_song_tree()
    elif artist_button.cget("bg") == "green":
        set_artist_tree()
    elif genre_button.cget("bg") == "green":
        set_genre_tree()

def add_tags_manually(chosen_song):
    global edit_album_art_tag
    global manual_tag_window
    if not chosen_song:
        messagebox.showerror("Error", "Select a Song to Edit")
    else:
        # Extract Song Info
        song_info = tree_list.item(chosen_song).get("values")
        song_title = song_info[0]
        song_artist = song_info[1]
        song_album = song_info[3]
        song_year = song_info[4]
        song_genre = song_info[5]
        edit_album_art_tag = get_album_art(ID3(song_dict.get(song_title)), 128, 128)

        manual_tag_window = Toplevel(root)
        manual_tag_window.title("Song Tag Editor")
        manual_tag_window.protocol("WM_DELETE_WINDOW", exit_manual_tag_window)
        # Album Art Section
        global album_art_label
        album_art_label = Label(manual_tag_window, image=edit_album_art_tag, width=128, height=128)
        album_art_label.pack()
        album_art_frame = Frame(manual_tag_window)
        album_art_frame.pack(pady=10)
        add_album_art_button = Button(album_art_frame, text="Add Album Art", command=add_album_art_in_tag_window)
        remove_album_art_button = Button(album_art_frame, text="Remove Album Art", command=remove_album_art_in_tag_window)
        save_album_art_button = Button(album_art_frame, text="Save Album Art", command=lambda: save_album_art(song_dict.get(song_title)))
        add_album_art_button.grid(row=0, column=0, padx=10)
        remove_album_art_button.grid(row=0, column=1, padx=10)
        save_album_art_button.grid(row=0, column=2, padx=10)
        # Song Section
        song_frame = Frame(manual_tag_window)
        song_frame.pack()
        song_label = Label(song_frame, text="Song")
        song_input = Entry(song_frame, width=62)
        song_input.insert(0, song_title)
        song_label.grid(row=0, column=0)
        song_input.grid(row=1, column=0)
        # Artist and Genre Section
        artist_genre_frame = Frame(manual_tag_window)
        artist_genre_frame.pack()
        artist_label = Label(artist_genre_frame, text="Artist")
        artist_input = Entry(artist_genre_frame, width=30)
        artist_input.insert(0, song_artist)
        genre_label = Label(artist_genre_frame, text="Genre")
        genre_input = Entry(artist_genre_frame, width=30)
        genre_input.insert(0, song_genre)
        artist_label.grid(row=0, column=0)
        artist_input.grid(row=1, column=0, padx=5)
        genre_label.grid(row=0, column=1)
        genre_input.grid(row=1, column=1, padx=5)
        # Album and Year Section
        album_year_frame = Frame(manual_tag_window)
        album_year_frame.pack()
        album_label = Label(album_year_frame, text="Album")
        album_input = Entry(album_year_frame, width=30)
        album_input.insert(0, song_album)
        year_label = Label(album_year_frame, text="Year")
        year_input = Entry(album_year_frame, width=30)
        year_input.insert(0, song_year)
        album_label.grid(row=0, column=0)
        album_input.grid(row=1, column=0, padx=5)
        year_label.grid(row=0, column=1)
        year_input.grid(row=1, column=1, padx=5)
        # Frame that shows a label when tags are applied to song
        global applied_tags_frame
        applied_tags_frame = Frame(manual_tag_window)
        applied_tags_frame.pack()
        # Apply and Cancel Buttons
        button_frame = Frame(manual_tag_window)
        button_frame.pack(pady=10)
        cancel_button = Button(button_frame, text="Cancel", fg="red", width=20, command=exit_manual_tag_window)
        apply_button = Button(button_frame, text="Apply", fg="green", width=20, command=lambda: apply_tags_to_song(song_dict.get(song_title), song_input.get(), artist_input.get(), genre_input.get(), album_input.get(), year_input.get()))
        cancel_button.grid(row=0, column=0, padx=15)
        apply_button.grid(row=0, column=1, padx=15)
# ==================================================================================================================================================
# Automatic Tag Editor Functions
def search_for_tags(title, artist, count):
    global album_art_results
    album_art_results = []  # Removes album art images from previous search

    # Resets tree if search has already been done:
    results_list.delete(*results_list.get_children())
    if title == "":
        messagebox.showerror("Error", "Enter Song Title to Search For Tags")
        automatic_tag_window.attributes("-topmost", 1)
    elif count and not count.isdigit():
        messagebox.showerror("Error", 'Enter a valid number for "Number of Tags Shown"\nor leave "Number of Tags Shown" blank.')
        automatic_tag_window.attributes("-topmost", 1)
    else:
        global song_tags_list
        song_tags_list = scrape_song_tags(title, artist, count)
        if not song_tags_list:
            messagebox.showinfo("Result", "No Tags Found")
            automatic_tag_window.attributes("-topmost", 1)
        else:
            for song_tag in song_tags_list:
                add_tags_to_results_list(song_tag)
            automatic_tag_window.attributes("-topmost", 1)

def add_tags_to_results_list(tag_list):
    global album_art_results
    if tag_list[0]:
        album_art_img = PIL.Image.open(BytesIO(tag_list[0])).resize((50, 50))
        album_art = ImageTk.PhotoImage(album_art_img)
        album_art_results.append(album_art)
        results_list.insert('', 'end', image=album_art, values=(tag_list[1], tag_list[2], tag_list[3], tag_list[4], tag_list[5]))
    else:
        album_art_results.append("")
        results_list.insert('', 'end', values=(tag_list[1], tag_list[2], tag_list[3], tag_list[4], tag_list[5]))

def apply_tags_from_results_list(chosen_song):
    global song_dict
    try:
        result_index = results_list.index(results_list.selection()[0])
        result_tags = song_tags_list[result_index]
        song_tags = ID3(chosen_song)
        album_art = result_tags[0]
        title = result_tags[1]
        artist = result_tags[2]
        album = result_tags[3]
        year = result_tags[4]
        genre = result_tags[5]
        if album_art:
            song_tags["APIC"] = APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                data=album_art
            )
        song_tags["TIT2"] = TIT2(
            encoding=3,
            text=title
        )
        song_tags["TPE1"] = TPE1(
            encoding=3,
            text=artist
        )
        song_tags["TCON"] = TCON(
            encoding=3,
            text=genre
        )
        song_tags["TALB"] = TALB(
            encoding=3,
            text=album
        )
        song_tags["TDRC"] = TDRC(
            encoding=3,
            text=year
        )
        song_tags.save()

        # Replace key in song_dict with new song title
        song_title_index = list(song_dict.values()).index(chosen_song)
        song_dict_list = list(song_dict.keys())
        song_title = song_dict_list[song_title_index]
        song_dict_list[song_title_index] = title
        song_dictionary = {}
        for i in range(len(song_dict_list)):
            song_dictionary.update({song_dict_list[i]: list(song_dict.values())[i]})
        song_dict = song_dictionary

        # Remove song from artist_dict and genre_dict
        artist_dict_key = ""
        genre_dict_key = ""

        index = 0
        for value in list(artist_dict.values()):
            for song in value:
                if song_title == song:
                    artist_dict_key = list(artist_dict.keys())[index]
            index += 1

        index = 0
        for value in list(genre_dict.values()):
            for song in value:
                if song_title == song:
                    genre_dict_key = list(genre_dict.keys())[index]
            index += 1

        if artist_dict_key and genre_dict_key:
            artist_dict.pop(artist_dict_key)
            genre_dict.pop(genre_dict_key)

        exit_automatic_tag_window()
    except IndexError:
        messagebox.showerror("Error", "Select a tag to apply to song file.\nIf there are no tags to select, search for tags.")
        automatic_tag_window.attributes("-topmost", 1)
    except MutagenError:
        messagebox.showerror("Error", "Song can't be edited if song is playing.\nStop or play a different song before trying again.")
        automatic_tag_window.attributes("-topmost", 1)

def exit_automatic_tag_window():
    automatic_tag_window.destroy()

    # Resets Treeview based on active button
    if song_button.cget("bg") == "green":
        set_song_tree()
    elif artist_button.cget("bg") == "green":
        set_artist_tree()
    elif genre_button.cget("bg") == "green":
        set_genre_tree()

def add_tags_automatically(chosen_song):
    if not chosen_song:
        messagebox.showerror("Error", "Select a Song to Edit")
    else:
        # Extract Song Title and Artist
        song_info = tree_list.item(chosen_song).get("values")
        song_title = song_info[0]
        song_artist = song_info[1]

        global automatic_tag_window
        automatic_tag_window = Toplevel(root)
        automatic_tag_window.geometry("700x500")
        automatic_tag_window.title("Automatic Song Tag Editor")
        automatic_tag_window.protocol("WM_DELETE_WINDOW", exit_automatic_tag_window)

        # Search Terms
        search_frame = Frame(automatic_tag_window)
        search_frame.pack()
        song_label = Label(search_frame, text="Title")
        song_input = Entry(search_frame, width=30)
        song_input.insert(0, song_title)
        artist_label = Label(search_frame, text="Artist")
        artist_input = Entry(search_frame, width=30)
        artist_input.insert(0, song_artist)
        tag_number_label = Label(search_frame, text="Number of Tags Shown")
        tag_number_input = Entry(search_frame, width=30)
        tag_number_input.insert(0, "5")
        search_button = Button(search_frame, text="Search", width=25, command=lambda: search_for_tags(song_input.get(), artist_input.get(), tag_number_input.get()))
        song_label.grid(row=0, column=0)
        song_input.grid(row=1, column=0)
        artist_label.grid(row=2, column=0)
        artist_input.grid(row=3, column=0)
        tag_number_label.grid(row=4, column=0)
        tag_number_input.grid(row=5, column=0)
        search_button.grid(row=6, column=0, pady=10)

        # Search Result List
        results_frame = Frame(automatic_tag_window)
        results_frame.pack()

        columns = ("Title", "Artist", "Album", "Year", "Genre")
        global results_list
        results_list = ttk.Treeview(results_frame, column=columns, selectmode="browse", height=5)

        # Managing Column Width and Height
        results_list.column("#0", width=80, stretch=True)
        results_list.column('Title', anchor="center", width=100, stretch=True)
        results_list.column('Artist', anchor="center", width=100, stretch=True)
        results_list.column('Album', anchor="center", width=100, stretch=True)
        results_list.column('Year', anchor="center", width=100, stretch=True)
        results_list.column('Genre', anchor="center", width=100, stretch=True)
        row_height = ttk.Style().configure('Treeview', rowheight=50)

        # Setup column headings
        for col in columns:
            results_list.heading(col, text=col, command=lambda _col=col: treeview_sort_column(results_list, _col, False))

        # Appending Scroll Bars to TreeView
        horizontal_scroll_bar = ttk.Scrollbar(results_frame, orient="horizontal", command=results_list.xview)
        vertical_scroll_bar = ttk.Scrollbar(results_frame, orient="vertical", command=results_list.yview)
        results_list.grid(in_=results_frame, row=0, column=0, sticky=N + S + W + E)
        horizontal_scroll_bar.grid(row=1, column=0, sticky=W + E + S)
        vertical_scroll_bar.grid(row=0, column=1, sticky=N + S + W)

        results_list.configure(xscrollcommand=horizontal_scroll_bar.set, yscrollcommand=vertical_scroll_bar.set)

        apply_tag_button = Button(automatic_tag_window, text="Apply Tags from Selected Result", command=lambda: apply_tags_from_results_list(song_dict.get(song_title)))
        apply_tag_button.pack()
# ==================================================================================================================================================
# Play Song Functionality Functions
def get_duration():
    if stopped:
        return
    # Grab Elapsed Time of Current Song (in Seconds)
    current_seconds = pygame.mixer.music.get_pos() / 1000
    global total_seconds
    total_seconds = MP3(currently_playing_song).info.length
    total_duration = time.strftime('%M:%S', time.gmtime(total_seconds))

    if int(song_slider.get()) == int(total_seconds):
        stop_song()
    elif paused:  # If paused, don't check the rest of the cases
        pass
    elif int(song_slider.get()) == int(current_seconds):
        song_slider.config(to=int(total_seconds), value=int(current_seconds))
    else:
        song_slider.config(to=int(total_seconds), value=int(song_slider.get()))
        current_duration = time.strftime('%M:%S', time.gmtime(int(song_slider.get()+1)))
        current_duration_label.config(text=f"{current_duration}")
        total_duration_label.config(text=f"{total_duration}")

        # Move slider, since we're not relying on current duration
        song_slider.config(value=int(song_slider.get()) + 1)

    playback_frame.after(1000, get_duration)

def play_song(selected_song):
    global now_playing_image
    global currently_playing_song
    global stopped
    stopped = False
    # Grab song path before playing song
    song_info = tree_list.item(selected_song).get("values")
    song_title = song_info[0]
    song_artist = song_info[1]
    song_duration = song_info[2]
    currently_playing_song = song_dict.get(song_title)
    pygame.mixer.music.load(currently_playing_song)
    pygame.mixer.music.play(loops=0)
    # Set up Player
    current_duration_label.config(text="00:00")
    total_duration_label.config(text=f'{time.strftime("%M:%S", time.gmtime(MP3(currently_playing_song).info.length))}')
    song_slider.config(value=0)
    # Get Future Duration of Song
    get_duration()
    # Set details in Now Playing
    now_playing_image = get_album_art(ID3(currently_playing_song), 32, 32)
    now_playing_label.config(image=now_playing_image, text=f' Now Playing: {song_title}{" - " if song_artist != "" else ""}{song_artist} [{song_duration}]')
    play_button.config(image=pause_icon)

def play_song_while_playing(selected_song):
    global currently_playing_song
    global now_playing_image
    # Sets up player
    current_duration_label.config(text="00:00")
    total_duration_label.config(text=f'{time.strftime("%M:%S", time.gmtime(MP3(currently_playing_song).info.length))}')
    song_slider.config(value=0)
    # Sets up song to be played
    song_info = tree_list.item(selected_song).get("values")
    song_title = song_info[0]
    song_artist = song_info[1]
    song_duration = song_info[2]
    currently_playing_song = song_dict.get(song_title)
    pygame.mixer.music.load(currently_playing_song)
    pygame.mixer.music.play(loops=0)
    # Set details in Now Playing
    now_playing_image = get_album_art(ID3(currently_playing_song), 32, 32)
    now_playing_label.config(image=now_playing_image, text=f' Now Playing: {song_title}{" - " if song_artist != "" else ""}{song_artist} [{song_duration}]')
    play_button.config(image=pause_icon)

def play_song_click(event):
    if tree_list.focus():
        current_song = tree_list.focus()
        if currently_playing_song == "":
            play_song(current_song)
        else:
            play_song_while_playing(current_song)
# ==================================================================================================================================================
# Play/Pause Song Functions
def play_pause_keybind(event):
    play_pause_selected_song(paused)

def play_pause_selected_song(is_paused):
    # Handling Pause Variable
    global paused
    paused = is_paused

    if currently_playing_song == "":
        if tree_list.focus():
            paused = False
            current_song = tree_list.focus()
            play_song(current_song)  # Gets highlighted song
        elif paused:
            paused = False
            play_button.config(image=play_icon)
        else:
            paused = True
            play_button.config(image=pause_icon)
    else:
        if paused:
            pygame.mixer.music.unpause()
            paused = False
            play_button.config(image=pause_icon)
        else:
            pygame.mixer.music.pause()
            paused = True
            play_button.config(image=play_icon)
# ==================================================================================================================================================
# Play Previous Song Functions
def play_previous_keybind(event):
    play_previous_song()

def play_previous_song():
    list_length = len(tree_list.get_children())
    if repeat and shuffle or repeat and not shuffle:
        prev_song = tree_list.focus()
    elif shuffle and not repeat and list_length > 1:
        prev_song = tree_list.get_children()[random.randint(0, list_length - 1)]
        # Loops until a new song is chosen
        while song_dict.get(tree_list.item(prev_song).get("values")[0]) == currently_playing_song:
            prev_song = tree_list.get_children()[random.randint(0, list_length-1)]
    else:
        prev_song = tree_list.prev(tree_list.focus())
    if tree_list.get_children():
        try:
            tree_list.focus(prev_song)
            tree_list.selection_set(prev_song)
            if currently_playing_song == "":
                play_song(prev_song)
            else:
                play_song_while_playing(prev_song)
        except IndexError:
            prev_song = tree_list.get_children()[0]
            tree_list.focus(prev_song)
            tree_list.selection_set(prev_song)
            if currently_playing_song == "":
                play_song(prev_song)
            else:
                play_song_while_playing(prev_song)
# ==================================================================================================================================================
# Play Next Song Functions
def play_next_keybind(event):
    play_next_song()

def play_next_song():
    list_length = len(tree_list.get_children())
    if repeat and shuffle or repeat and not shuffle:
        next_song = tree_list.focus()
    elif shuffle and not repeat and list_length > 1:
        next_song = tree_list.get_children()[random.randint(0, list_length - 1)]
        # Loops until a new song is chosen
        while song_dict.get(tree_list.item(next_song).get("values")[0]) == currently_playing_song:
            next_song = tree_list.get_children()[random.randint(0, list_length-1)]
    else:
        next_song = tree_list.next(tree_list.focus())
    if tree_list.get_children():
        try:
            tree_list.focus(next_song)
            tree_list.selection_set(next_song)
            if currently_playing_song == "":
                play_song(next_song)
            else:
                play_song_while_playing(next_song)
        except IndexError:
            next_song = tree_list.get_children()[0]
            tree_list.focus(next_song)
            tree_list.selection_set(next_song)
            if currently_playing_song == "":
                play_song(next_song)
            else:
                play_song_while_playing(next_song)
# ==================================================================================================================================================
# Stop Song Functions
def stop_keybind(event):
    stop_song()

def stop_song():
    global now_playing_image
    global stopped
    global currently_playing_song
    global last_song_played
    pygame.mixer.music.stop()  # Stops music
    stopped = True
    # Resets everything below to default position
    currently_playing_song = ""
    pygame.mixer.music.unload()  # Unloads mp3 file from music player, so tags can be applied
    current_duration_label.config(text="--:--")
    total_duration_label.config(text="--:--")
    song_slider.config(value=0)
    play_button.config(image=play_icon)
    now_playing_image = ImageTk.PhotoImage(default_now_playing_image)
    now_playing_label.config(image=now_playing_image, text=" Now Playing:")
# ==================================================================================================================================================
def set_repeat():
    global repeat
    if repeat:
        repeat = False
        repeat_button.config(bg="SystemButtonFace")  # Set to default color
    else:
        repeat = True
        repeat_button.config(bg="green")

def set_shuffle():
    global shuffle
    if shuffle:
        shuffle = False
        shuffle_button.config(bg="SystemButtonFace")  # Set to default color
    else:
        shuffle = True
        shuffle_button.config(bg="green")
# ==================================================================================================================================================
def playback_slide(event):
    if currently_playing_song:
        pygame.mixer.music.load(currently_playing_song)
        pygame.mixer.music.play(loops=0, start=int(song_slider.get()))

def rewind_song(event):
    rewind_seconds = int(song_slider.get()) - 5
    if rewind_seconds < 0:
        rewind_seconds = 0
    # Update current_duration and slider value
    current_duration = time.strftime('%M:%S', time.gmtime(rewind_seconds))
    current_duration_label.config(text=f"{current_duration}")
    song_slider.set(rewind_seconds)

def fast_forward_song(event):
    fast_forward_seconds = int(song_slider.get()) + 5
    if fast_forward_seconds > total_seconds:
        stop_song()
    # Update current_duration and slider value
    current_duration = time.strftime("%M:%S", time.gmtime(fast_forward_seconds))
    current_duration_label.config(text=f'{current_duration}')
    song_slider.set(fast_forward_seconds)
# ==================================================================================================================================================
# Volume Functions
def mute_keybind(event):
    mute(event)

def mute(event):
    global muted
    if muted:
        muted = False
    else:
        muted = True
        pygame.mixer.music.set_volume(0)
        volume_label.config(image=volume1)
    volume(event)

def volume(event):
    if not muted:
        pygame.mixer.music.set_volume(volume_slider.get())
        current_volume = pygame.mixer.music.get_volume() * 100

        if int(current_volume) < 1:
            volume_label.config(image=volume1)
        elif 0 < int(current_volume) <= 33:
            volume_label.config(image=volume2)
        elif 33 < int(current_volume) <= 66:
            volume_label.config(image=volume3)
        elif 66 < int(current_volume) <= 100:
            volume_label.config(image=volume4)

def decrease_volume(event):
    volume_decreased = volume_slider.get()-.05
    if volume_decreased < 0:
        volume_decreased = 0
    volume_slider.set(volume_decreased)

def increase_volume(event):
    volume_increased = volume_slider.get()+.05
    if volume_increased > 1:
        volume_increased = 1
    volume_slider.set(volume_increased)
# =======================================================================================================================================================================
# Create the menu bar
menu = Menu(root)
root.config(menu=menu)

fileMenu = Menu(menu, tearoff="off")
menu.add_cascade(label="File", menu=fileMenu)
fileMenu.add_command(label="Add Songs", command=add_songs)
fileMenu.add_separator()
fileMenu.add_command(label="Exit", command=root.destroy)
# =======================================================================================================================================================================
# Create buttons that handles List View
list_type_frame = Frame(root)
list_type_frame.pack(pady=10)

back_button = Button(list_type_frame, text="Back", width=10, height=2, bg="white", command=return_to_list)
song_button = Button(list_type_frame, text="Songs", width=10, height=2, bg="green", command=set_song_tree)
artist_button = Button(list_type_frame, text="Artists", width=10, height=2, bg="white", command=set_artist_tree)
genre_button = Button(list_type_frame, text="Genres", width=10, height=2, bg="white", command=set_genre_tree)
back_button.grid(row=0, column=0, padx=10)
song_button.grid(row=0, column=1, padx=10)
artist_button.grid(row=0, column=2, padx=10)
genre_button.grid(row=0, column=3, padx=10)
count_label = Label(list_type_frame, text="Songs: 0")
count_label.grid(row=0, column=4, padx=40, sticky=E)
# =======================================================================================================================================================================
# Create song view with scrollbars
tree_frame = Frame(root)
tree_frame.pack()

# Create the list (with ascending/descending columns)
columns = ("Title", "Artist", "Duration", "Album", "Year", "Genre")
tree_list = ttk.Treeview(tree_frame, column=columns, selectmode="browse", height=5)

# Managing Column Width and Height
tree_list.column("#0", width=80)
tree_list.column('Title', anchor="center", width=100)
tree_list.column('Artist', anchor="center", width=100)
tree_list.column('Duration', anchor="center", width=100)
tree_list.column('Album', anchor="center", width=100)
tree_list.column('Year', anchor="center", width=100)
tree_list.column('Genre', anchor="center", width=100)
row_height = ttk.Style().configure('Treeview', rowheight=50)

# Setup column headings
for col in columns:
    tree_list.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree_list, _col, False))

# Appending Scroll Bars to TreeView
horizontal_scroll_bar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree_list.xview)
vertical_scroll_bar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_list.yview)
tree_list.grid(in_=tree_frame, row=0, column=0, sticky=N+S+W+E)
horizontal_scroll_bar.grid(row=1, column=0, sticky=W+E+S)
vertical_scroll_bar.grid(row=0, column=1, sticky=N+S+W)

tree_list.configure(xscrollcommand=horizontal_scroll_bar.set, yscrollcommand=vertical_scroll_bar.set)

tree_list.bind("<Double-1>", play_song_click)
# Right Click Menu for Songs in Treeview
song_menu = Menu(root, tearoff="off")
song_menu.add_command(label="Remove Song", command=lambda: remove_song(tree_list.selection()[0]))
song_menu.add_command(label="Add Tags Manually", command=lambda: add_tags_manually(tree_list.selection()[0]))
song_menu.add_command(label="Add Tags Automatically", command=lambda: add_tags_automatically(tree_list.selection()[0]))

tree_list.bind("<Button-3>", right_click_song_menu)
# =======================================================================================================================================================================
# Add playback slider with current and total duration labels
playback_frame = Frame(root)
playback_frame.pack()

# Creating custom slider
style = ttk.Style()
trough = PIL.Image.open("icons/line.png")
trough_resized = trough.resize((128, 50))
trough_img = ImageTk.PhotoImage(trough_resized)
slider = PIL.Image.open("icons/White_Slider.png")
slider_resized = slider.resize((24, 24))
slider_img = ImageTk.PhotoImage(slider_resized)

style.element_create('custom.Scale.trough', 'image', trough_img)
style.element_create('custom.Scale.slider', 'image', slider_img)
style.layout('custom.Horizontal.TScale',
             [('custom.Scale.trough', {'sticky': 'we'}),
              ('custom.Scale.slider',
               {'side': 'left', 'sticky': '',
                'children': [('custom.Horizontal.Scale.label', {'sticky': ''})]
                })])

current_duration_label = Label(playback_frame, text="--:--")
total_duration_label = Label(playback_frame, text="--:--")
song_slider = Scale(playback_frame, from_=0, to=100, length=600, style="custom.Horizontal.TScale", command=playback_slide)
current_duration_label.grid(row=0, column=0, padx=20)
song_slider.grid(row=0, column=1)
total_duration_label.grid(row=0, column=2, padx=20)
# =======================================================================================================================================================================
# Add playback buttons with keybinds.
control_frame = Frame(root)
control_frame.pack(pady=20)

# Adding Music Control Buttons
control_buttons_frame = Frame(control_frame)
control_buttons_frame.pack(side=LEFT)

# Button Icons
play_icon = ImageTk.PhotoImage(file="icons/Play.png")
stop_icon = ImageTk.PhotoImage(file="icons/Stop.png")
pause_icon = ImageTk.PhotoImage(file="icons/Pause.png")
prev_icon = ImageTk.PhotoImage(file="icons/Prev.png")
next_icon = ImageTk.PhotoImage(file="icons/Next.png")
shuffle_icon = ImageTk.PhotoImage(file="icons/Shuffle.png")
repeat_icon = ImageTk.PhotoImage(file="icons/Repeat.png")

play_button = Button(control_buttons_frame, image=play_icon, width=32, height=32, command=lambda: play_pause_selected_song(paused))
previous_button = Button(control_buttons_frame, image=prev_icon, width=32, height=32, command=play_previous_song)
next_button = Button(control_buttons_frame, image=next_icon, width=32, height=32, command=play_next_song)
shuffle_button = Button(control_buttons_frame, image=shuffle_icon, width=32, height=32, command=set_shuffle)
repeat_button = Button(control_buttons_frame, image=repeat_icon, width=32, height=32, command=set_repeat)
play_button.grid(row=0, column=2, padx=5)
previous_button.grid(row=0, column=1, padx=5)
next_button.grid(row=0, column=3, padx=5)
shuffle_button.grid(row=0, column=0, padx=5)
repeat_button.grid(row=0, column=4, padx=5)

# Playback Keybinds
root.bind("<space>", play_pause_keybind)
root.bind("n", play_next_keybind)
root.bind("p", play_previous_keybind)
root.bind("s", stop_keybind)
root.bind('<Left>', rewind_song)
root.bind('<Right>', fast_forward_song)
# =======================================================================================================================================================================
# Create volume slider with keybinds
volume_frame = Frame(control_frame)
volume_frame.pack(side=RIGHT)

# Volume icons
volume1_resize = PIL.Image.open("icons/vol1.png").resize((32, 32))
volume1 = ImageTk.PhotoImage(volume1_resize)
volume2_resize = PIL.Image.open("icons/vol2.png").resize((32, 32))
volume2 = ImageTk.PhotoImage(volume2_resize)
volume3_resize = PIL.Image.open("icons/vol3.png").resize((32, 32))
volume3 = ImageTk.PhotoImage(volume3_resize)
volume4_resize = PIL.Image.open("icons/vol4.png").resize((32, 32))
volume4 = ImageTk.PhotoImage(volume4_resize)

volume_label = Label(volume_frame, image=volume4)
volume_slider = Scale(volume_frame, value=1, from_=0, to=1, length=200, style="custom.Horizontal.TScale", command=volume)
volume_label.grid(row=0, column=0, padx=(150, 10))
volume_slider.grid(row=0, column=1)

# Volume Keybinds
volume_label.bind("<Button-1>", mute)
root.bind('<Up>', increase_volume)
root.bind('<Down>', decrease_volume)
root.bind("m", mute_keybind)
# =======================================================================================================================================================================
# Adds a now playing view with stop button
playing_frame = Frame(root)
playing_frame.pack(fill=X, side=BOTTOM)
playing_frame.columnconfigure(0, weight=1)
# Create default Now Playing Image
default_now_playing_image = PIL.Image.open("icons/Default Album Art.jpg").resize((32, 32))
now_playing_image = ImageTk.PhotoImage(default_now_playing_image)
now_playing_label = Label(playing_frame, text=" Now Playing: ", image=now_playing_image, compound=LEFT, anchor=W, relief=GROOVE, bg="white")
stop_button = Button(playing_frame, image=stop_icon, width=32, height=32, command=stop_song)
now_playing_label.grid(row=0, column=0, sticky=N+S+W+E)
stop_button.grid(row=0, column=1)

mainloop()
