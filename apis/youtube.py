from exceptions import ConfigVideoLowViewCount, ConfigVideoMaxLength, YoutubeItemNotFound
from pytubefix import YouTube as pytubeYouTube
from pytubefix import Playlist as pytubePlaylist
from youtube_search import YoutubeSearch
import json
import re
import socket

import ssl
import socks

# Clients tried per proxy in order. ANDROID_VR skips JS player cipher entirely.
# TV (oauth) is the fallback if YouTube flags the proxy IP as a bot.
_CLIENTS = [
    {'client': 'ANDROID_VR', 'use_oauth': False},
    {'client': 'TV',         'use_oauth': True,  'allow_oauth_cache': True},
]

import random


_original_socket = socket.socket
_original_getaddrinfo = socket.getaddrinfo
_original_create_connection = socket.create_connection

_proxy_type = None
_proxy_host = None
_proxy_port = None


def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    results = _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    if not results:
        results = _original_getaddrinfo(host, port, family, type, proto, flags)
    return results


def _patched_create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, **kwargs):
    """Drop-in for socket.create_connection that tunnels through the proxy.
    Returns a plain connected socket so SSL can wrap it without issues."""
    sock = socks.socksocket()
    sock.set_proxy(_proxy_type, _proxy_host, _proxy_port, rdns=True)
    if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
        sock.settimeout(timeout)
    sock.connect(address)
    return sock


def _install_proxy_patch(proxy: str):
    global _proxy_type, _proxy_host, _proxy_port

    scheme, rest = proxy.split("://", 1)
    _proxy_host, port_str = rest.rsplit(":", 1)
    _proxy_port = int(port_str)
    _proxy_type = {
        "socks5": socks.SOCKS5,
        "socks5h": socks.SOCKS5,
        "socks4": socks.SOCKS4,
        "http": socks.HTTP,
    }.get(scheme.lower(), socks.SOCKS5)

    # Patch create_connection — used by http.client for both HTTP and HTTPS.
    # SSL then wraps the already-tunnelled plain socket, which works correctly.
    socket.create_connection = _patched_create_connection
    socket.getaddrinfo = _ipv4_only_getaddrinfo
    # Proxy may present its own certificate; disable verification for the session
    ssl._create_default_https_context = ssl._create_unverified_context


def _remove_proxy_patch():
    socket.create_connection = _original_create_connection
    socket.getaddrinfo = _original_getaddrinfo


class YouTube:
    def __init__(self):
        pass

    # TODO: Make videos to search configurable via parameter
    def search(self, search_query, max_length, min_view_count, search_count = 1):
        youtube_results = YoutubeSearch(search_query, max_results=search_count).to_json()

        if len(json.loads(youtube_results)['videos']) < 1:
            raise YoutubeItemNotFound('Skipped song -- Could not load from YouTube')

        youtube_videos = json.loads(youtube_results)['videos']
        videos_meta = []

        for video in youtube_videos:
            # print(video)
            # youtube_video_title = video['title']
            # TODO: pass in spotify song + artist and find which one matches most

            # TODO: Check duration against spotify song duration to find closest

            youtube_video_duration = video['duration'].split(':')
            youtube_video_duration_seconds = int(youtube_video_duration[0]) * 60  + int(youtube_video_duration[1])

            youtube_video_views = re.sub('[^0-9]','', video['views'])
            youtube_video_viewcount_safe = int(youtube_video_views) if str(youtube_video_views).isdigit() else 0

            videos_meta.append((video, youtube_video_duration_seconds, youtube_video_viewcount_safe))

        sorted_videos = sorted(videos_meta, key=lambda vid: vid[2], reverse=True) # Find top N videos with the most views
        chosen_video = sorted_videos[0]

        youtube_video_link = "https://www.youtube.com" + chosen_video[0]['url_suffix']

        if(chosen_video[1] >= max_length):
            raise ConfigVideoMaxLength(f'Length {chosen_video[1]}s exceeds MAX_LENGTH value of {max_length}s [{youtube_video_link}]')

        if(chosen_video[2] <= min_view_count):
            raise ConfigVideoLowViewCount(f'View count {chosen_video[2]} does not meet MIN_VIEW_COUNT value of {min_view_count} [{youtube_video_link}]')
    
        return youtube_video_link
    
    # Pool of proxies - shuffled on each download so no single IP always gets hit first
    FALLBACK_PROXIES = [
        "socks5://34.174.40.246:1080",
        "socks5://142.248.80.110:1080",
        "socks5://45.83.140.16:1080",
        "socks5://23.175.248.21:1080",
        "socks5://104.233.195.149:1080",
        "socks5://152.53.53.166:1080",
        "socks5://51.15.20.32:1088",
        "socks5://146.103.125.38:1080",
    ]

    def download(self, url, audio_bitrate, proxy: str = None):
        # Build pool: configured proxy first (if any), then the rest shuffled
        pool = list(self.FALLBACK_PROXIES)
        if proxy and proxy in pool:
            pool.remove(proxy)
        random.shuffle(pool)
        proxies_to_try = ([proxy] if proxy else []) + pool

        last_error = None
        for attempt, current_proxy in enumerate(proxies_to_try):
            if attempt > 0:
                print(f"   - Retrying with fallback proxy [{attempt}/{len(proxies_to_try)-1}]: {current_proxy}")
            _install_proxy_patch(current_proxy)
            try:
                # Try each client in order for this proxy
                for client_cfg in _CLIENTS:
                    try:
                        return self._do_download(url, audio_bitrate, **client_cfg)
                    except Exception as client_err:
                        err_str = str(client_err)
                        # Only fall through to next client on bot/auth errors
                        if any(k in err_str for k in ('429', 'bot', 'sign in', 'login', 'BotDetection', 'LoginRequired')):
                            print(f"   - Client {client_cfg['client']} blocked on {current_proxy}: {client_err}")
                            continue
                        raise  # real error - propagate immediately
                last_error = Exception(f"All clients blocked on {current_proxy}")
                print(f"   - {last_error}")
            except Exception as e:
                last_error = e
                print(f"   - Proxy {current_proxy} failed: {e}")
            finally:
                _remove_proxy_patch()

        raise Exception(f"All proxies exhausted. Last error: {last_error}")

    def _do_download(self, url, audio_bitrate, client='ANDROID_VR', use_oauth=False, allow_oauth_cache=False):
        youtube_video = pytubeYouTube(url, use_oauth=use_oauth, allow_oauth_cache=allow_oauth_cache, client=client)

        if youtube_video.age_restricted:
            youtube_video.bypass_age_gate()
        youtube_video_streams = youtube_video.streams.filter(only_audio=True)

        selected_bitrate_normalised = audio_bitrate / 1000

        finalKbps = 0
        correctIndex = 0
        for i, vid in enumerate(youtube_video_streams):
            currKbps = int(re.sub("[^0-9]", "", vid.abr))
            if currKbps <= selected_bitrate_normalised:
                correctIndex = i
                finalKbps = currKbps

        video_stream = youtube_video_streams[correctIndex]
        yt_tmp_out = video_stream.download(output_path="./temp/")
        return yt_tmp_out, finalKbps * 1000