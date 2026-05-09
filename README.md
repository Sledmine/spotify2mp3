<div align="center">
  <img src="assets/logo.png" alt="logo" width="250" height="auto" />  
  <p>
    Simple and unlimited Spotify MP3 downloads
  </p>
</p>
   
<h4>
    <a href="https://github.com/Sledmine/spotify2mp3/issues">Report Bug</a>
  </h4>
</div>

**NOTE:** This is a fork of the original spotify2mp3 project, which is no longer maintained. It was made
only with the intention to fit my needs for downloading my Spotify playlists, I have no plan to
commit to maintaining this project in the long term, but I have been adding a few features and fixes
here and there, expect some vibe coding and some questionable design decisions
(I'll try to keep quality in line), but hey, it works and it's free, so enjoy!

<!-- Important Notice -->
## ⚠️ Important: Spotify Premium Now Required for API Access

Spotify has introduced significant changes to their Web API platform. **The owner of the Spotify developer app must have an active Spotify Premium subscription** for apps in [Development Mode](https://developer.spotify.com/documentation/web-api/concepts/quota-modes) to function.

If the app owner's account does not have Premium, **all API requests will fail with a 403 error**:

> `Active premium subscription required for the owner of the app.`

This affects **every endpoint** - not just user-specific ones. Public playlists, tracks, albums, and all other resources will be blocked.

### What you need to know

- The Spotify account that **created the developer app** (Client ID / Client Secret) must have **Premium**.
- Free-tier Spotify accounts **can no longer use the Web API** in Development Mode.
- After subscribing (or re-subscribing) to Premium, it can take **a few hours** before API access is restored.

Be aware of this if you are looking for a free solution to download Spotify playlists.


---

<!-- Getting Started -->
## 	:toolbox: Getting Started

<!-- Prerequisites -->
### :bangbang: Prerequisites

1. Ideally use Python 3.10 or higher.
2. Install git.
   - Windows: https://git-scm.com/download/win
   - Ubuntu: It should come pre-installed
   - Mac OS: It should come pre-installed

<!-- Run Locally -->
### :running: Run Locally

Clone the project

`$ git clone https://github.com/Sledmine/spotify2mp3.git`

<!-- Installation -->
### :gear: Installation

Go to the project directory

`$ cd spotify2mp3 `

Install packages using pip

`$ pip install -r requirements.txt`

Run the script

`$ python spotify2mp3.py`

Brew yourself a coffee, you deserved it!

`If this project helped you, feel free to give us a star`

## Getting spotify playlist URL

Paste a Spotify Song, Playlist or Album URL into the program. You can also specify 'liked' to retrieve your liked songs.

To get the url:

1. Right click on a Song, Playlist or Album
2. Share
3. Copy link

On mobile:

1. Three dots
2. Share
3. Copy link

## Troubleshooting

If you have any issues at all, please post a full log <a href="https://github.com/Sledmine/spotify2mp3/issues">here</a>

## Coming soon

- Documentation for the spotify2mp3 Python API.
- Refactor of the codebase to be more modular and maintainable.
- Local server to handle API requests and downloads, allowing for integration with other applications and services.
- Frontend interface for integration with other playlists providers like YouTube Music, SoundCloud, etc.
