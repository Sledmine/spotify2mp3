from const import colours
from pytubefix.exceptions import AgeRestrictedError
from exceptions import SpotifyAlbumNotFound, SpotifyTrackNotFound, SpotifyPlaylistNotFound, ConfigVideoMaxLength, ConfigVideoLowViewCount, YoutubeItemNotFound
from apis.spotify import Spotify
from utils import resave_audio_clip_with_metadata, save_song_metadata
import sys
import os
import shutil
import time
import string
from apis.youtube import YouTube

from pathlib import Path

import ssl

ssl._create_default_https_context = ssl._create_stdlib_context


class SpotifyDownloader():
    def __init__(self, spotify: Spotify, youtube: YouTube, audio_quality=1000000, max_length=60*30, min_view_count=10000):
        self.spotify_client = spotify
        self.youtube_client = youtube
        self.audio_quality = audio_quality
        self.max_length = max_length
        self.min_view_count = min_view_count

    def download_album(self, playlist_url):
        
        skipped_songs = 0

        print(f"\n{colours.OKBLUE}[!] Retrieving spotify album")

        try:

            album = self.spotify_client.album(playlist_url)

            self.prep_folder("downloads/albums/" + album.get_title(True))

            tracks = album.get_tracks()

            print(f"\n{colours.OKBLUE}[!] Found {len(tracks)} tracks in album.")
            
            time.sleep(3)

            output_path = "downloads/albums/" + album.get_title(True) + "/"
            self.download_tracks(output_path, tracks)

            return True
        
        except SpotifyAlbumNotFound as e:
            
            print(f"\n{colours.FAIL}Error: {colours.ENDC}{colours.WARNING}It's probably that this album does not exist {colours.ENDC} (e: {e}).{colours.ENDC}\n")
            sys.exit(1)
    
    def download_liked_songs(self):

        print(f"\n{colours.OKBLUE}[!] Retrieving liked songs from Spotify (many songs will take time)")

        try:
            likedplaylist = self.spotify_client.likedSongs()

            self.prep_folder("downloads/liked/" + likedplaylist.get_title(True))

            tracks = likedplaylist.get_tracks()

            print(f"\n{colours.OKBLUE}[!] Found {len(tracks)} liked tracks.")
            time.sleep(3)

            output_path = "downloads/liked/" + likedplaylist.get_title(True) + "/"
            self.download_tracks(output_path, tracks)

            return True
       
        except SpotifyPlaylistNotFound as e:
            print(f"\n{colours.FAIL}Error: {colours.ENDC} (e: {e}).{colours.ENDC}\n")
            sys.exit(1)
        
    def download_playlist(self, playlist_url):

        print(f"\n{colours.OKBLUE}[!] Retrieving spotify playlist (large playlists will take time)")

        try:
            playlist = self.spotify_client.playlist(playlist_url)

            self.prep_folder("downloads/playlists/" + playlist.get_title(True))

            tracks = playlist.get_tracks()

            print(f"\n{colours.OKBLUE}[!] Found {len(tracks)} tracks in playlist.")
            time.sleep(3)

            output_path = "downloads/playlists/" + playlist.get_title(True) + "/"
            self.download_tracks(output_path, tracks)

            return True
        
        except SpotifyPlaylistNotFound:
            print(f"\n{colours.FAIL}Error: {colours.ENDC}{colours.WARNING}It's probably that this playlist is private or does not exist. Re-run with --login to access private playlists.{colours.ENDC}\n")
            sys.exit(1)
        
    def download_tracks(self, output_path, tracks):

        skipped_tracks = []

        idx_max = len(tracks)
        for i in range(idx_max):
            
            try:
                track = tracks[i]
                self.download_track(None, track, i, idx_max, output_path, True)

            except SpotifyTrackNotFound as e:
                
                print(f"   - {colours.WARNING}[!] Skipped a song we could not find.{colours.ENDC} {e}")

                skipped_tracks.append((track, e))
            
            except YoutubeItemNotFound as e:
                
                print(f"   - {colours.WARNING}[!] Skipped a song we found on Spotify but not on YouTube.{colours.ENDC}\n")

                skipped_tracks.append((track, e))

            except ConfigVideoMaxLength as e:
                
                print(f"\n{colours.WARNING}[!] Skipped a song - The found song was longer than the configured max song length, {colours.ENDC}(use the cli to increase this).{colours.ENDC}\n")

                skipped_tracks.append((track, e))
            
            except ConfigVideoLowViewCount as e:
                
                print(f"\n{colours.WARNING}[!] Skipped a song - The found song had less views than the minimum view count, {colours.ENDC}(use the cli to increase this).\n")

                skipped_tracks.append((track, e))

            except AgeRestrictedError as e:

                print(f"   - {colours.FAIL}[!] Skipped a song - Age restricted video.{colours.ENDC} {e}")

                skipped_tracks.append((track, e))

            except Exception as e:
                
                print(f"   - {colours.FAIL}[!] Skipped a song - Something went wrong.{colours.ENDC} {e}")

                skipped_tracks.append((track, e))

        if len(skipped_tracks) > 0:

            print(f"\n{colours.WARNING}[!] Skipped {len(skipped_tracks)} songs.{colours.ENDC}\n")

            for (track, reason) in skipped_tracks:
                print(f"    {track.get_title(True)} {colours.WARNING}[{reason}]{colours.ENDC}")

        return skipped_tracks

    def download_track(self, track_url = None, track = None, idx = 0, idx_max = 0, output_path = None, as_sub_function = False):

        try:

            output_path = output_path if output_path else "downloads/tracks/"

            if track_url:
                track = self.spotify_client.track(track_url)
            else:
                if(track is None):
                    print("No Track was supplied to download track!")
                    raise Exception("No Track was supplied to download track!")
                
            if(track):
                print(f"\n{colours.OKGREEN}Searching for song [{idx+1}/{idx_max}] {colours.ENDC}: {track.get_title(True)} by {track.get_artist()}")
            
            track_path = output_path + track.get_title(True) + ".mp3"

            self.prep_folder(output_path)
            if self.file_exists(track_path):
                save_song_metadata(track.get_metadata())
                print(f"{colours.OKCYAN}   - File exists, skipping.")
                return True
                
            searchable_name = track.get_searchable_title()

            # hardcoded for now max_length, min_view_count

            youtube_link = self.youtube_client.search( searchable_name, self.max_length, self.min_view_count )

            print(f"{colours.ENDC}   - Downloading, please wait{colours.ENDC}")

            video_downloaded_path, self.audio_quality = self.youtube_client.download(youtube_link, self.audio_quality)

            # consider updating searchable name to something nicer for the end user

            print(f"{colours.ENDC}   - Converting the song and adding metadata{colours.ENDC}")

            resave_audio_clip_with_metadata(video_downloaded_path, track.get_metadata(), output_path + track.get_title(True) + ".mp3", self.audio_quality)

            print(f"{colours.ENDC}   - Done!")

            return True

        except SpotifyTrackNotFound as e:

            if(not as_sub_function):
                print(f"\n{colours.FAIL}Error: {colours.ENDC}We could not find this particular song online {colours.ENDC} (e: {e}).{colours.ENDC}\n")
                return False
            else:
                raise e

        except ConfigVideoMaxLength as e:
            if(not as_sub_function):
                print(f"\n{colours.FAIL}Error: {colours.ENDC}The found song was longer than the configured max song length (use the cli to increase this) {colours.ENDC} (e: {e}).{colours.ENDC}\n")
                return False
            else:
                raise e

        except ConfigVideoLowViewCount as e:
            if(not as_sub_function):
                print(f"\n{colours.FAIL}Error: {colours.ENDC}The found song had less views than the minimum view count (use the cli to increase this){colours.ENDC} (e: {e}).{colours.ENDC}\n")
                return False
            else:
                raise e


    def prep_folder(self, folder_name):
        Path(str(folder_name)).mkdir(parents=True, exist_ok=True)
        Path('temp/').mkdir(parents=True, exist_ok=True)

    def file_exists(self, file_path):
        return Path.exists(Path(str(file_path)))

    def rm_tmp_folder(self):
        shutil.rmtree('./temp')

if __name__ == "__main__":
    pass
