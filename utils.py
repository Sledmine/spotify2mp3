from const import colours, BASE62
import logging
import string
import sys
import random
import eyed3
from eyed3.id3.frames import ImageFrame
import moviepy.editor as mp
from moviepy.editor import *
import requests
import shutil
import os

logging.getLogger('moviepy').setLevel(logging.CRITICAL)


def print_splash_screen():
        print(colours.SPOTIFYGREEN + '''
              


              
        ███████╗██████╗  ██████╗ ████████╗██╗███████╗██╗   ██╗██████╗ ███╗   ███╗██████╗ ██████╗ 
        ██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝██║██╔════╝╚██╗ ██╔╝╚════██╗████╗ ████║██╔══██╗╚════██╗
        ███████╗██████╔╝██║   ██║   ██║   ██║█████╗   ╚████╔╝  █████╔╝██╔████╔██║██████╔╝ █████╔╝
        ╚════██║██╔═══╝ ██║   ██║   ██║   ██║██╔══╝    ╚██╔╝  ██╔═══╝ ██║╚██╔╝██║██╔═══╝  ╚═══██╗
        ███████║██║     ╚██████╔╝   ██║   ██║██║        ██║   ███████╗██║ ╚═╝ ██║██║     ██████╔╝
        ╚══════╝╚═╝      ╚═════╝    ╚═╝   ╚═╝╚═╝        ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝     ╚═════╝         
              
        ''' + colours.ENDC + colours.BOLD + '''         Download your favourite songs as mp3s with the click of a button.  ''' + colours.ENDC + "\n")


def random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_letters  # This includes both lowercase and uppercase letters.
    return ''.join(random.choice(letters) for i in range(length))

def make_alphanum(str):
    asc = str.encode("ascii", errors="ignore").decode()
    return ''.join(e for e in asc if e.isalnum())

def save_song_metadata(song_metadata):
    image_url = song_metadata['image_url']
    image_data = requests.get(image_url).content

    title = song_metadata['title']
    artist = "".join(song_metadata['artist'])
    album = song_metadata['album']

    # Check if the covers directory exists, if not create it
    if not os.path.exists("downloads/covers"):
        os.makedirs("downloads/covers")

    hash = title + artist + album
    hash = make_alphanum(hash)
    hash = hash.lower()
    output_image_path = "downloads/covers/" + hash + ".jpg"

    # Check if the song cover already exists, if it does, skip saving it
    if os.path.exists(output_image_path):
        return

    # Write image data to disk
    with open(output_image_path, 'wb') as image_handler:
        image_handler.write(image_data)

def resave_audio_clip_with_metadata(audio_input_path, song_metadata, song_output_path, audio_quality):

    temporary_audio_path = "./temp/" + random_string(20) + ".mp3"

    clip = AudioFileClip(audio_input_path)
    clip.write_audiofile(temporary_audio_path, logger=None, bitrate=f'{audio_quality}k')

    audiofile = eyed3.load(temporary_audio_path)

    if audiofile.tag is None:
        audiofile.initTag()

    # Setting album cover from the provided image_url
    image_url = song_metadata['image_url']
    image_data = requests.get(image_url).content

    # Save the image data as the album cover and other data
    save_song_metadata(song_metadata)

    audiofile.tag.images.set(ImageFrame.FRONT_COVER, image_data, 'image/jpeg', "Cover Image from Spotify")

    # Setting title, artist, and album details
    audiofile.tag.title = song_metadata['title']            
    audiofile.tag.artist = ", ".join(song_metadata['artist'])  # Joining the artist list into a single string
    audiofile.tag.album = song_metadata['album']       
    audiofile.tag.track_num = (song_metadata['track_num'], 0)  # Track number (total tracks unknown based on provided metadata)
    audiofile.tag.release_date = song_metadata['release_date'][:4] # Only the year is provided in the metadata

    # Optionally, you can add more metadata fields here...

    audiofile.tag.save()

    shutil.copy(temporary_audio_path, song_output_path)

    # Remove the temporary file
    os.remove(temporary_audio_path)   # changed from shutil.rmtree which deletes directories
