from pathlib import Path
from typing import Any

import pygame
import yt_dlp

from app.tools.base import Tool

import subprocess
from typing import Optional
import psutil
        
import re
from enum import Enum
from app.tools.video import BraveVideoPlayer
from app.tools.computer import WiFiManager

class GetMusicStatusTool(Tool):
    @property
    def name(self) -> str:
        return "get_music_status"

    @property
    def description(self) -> str:
        return (
            "Get the current music playback state. "
            "Use this when the user asks what song is playing, "
            "whether music is playing, whether playback is paused, "
            "or what playback source is currently active."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": (
                        "Pass the user's complete original music request "
                        "exactly as spoken. Do not remove words such as "
                        "'audio', 'audio only', 'video', or 'any song'."
                    ),
                }
            },
            "required": ["request"],
        }

    def __init__(self, controller):
        self.controller = controller

    def execute(self, arguments: dict[str, Any]) -> dict:
        return self.controller.playback_status()
    
    
class OnlineMusicManager:
    """
    Online music search and audio extraction using yt-dlp.

    This class does not play audio itself.
    It finds the requested YouTube result and returns
    information needed by the playback layer.
    """

    def search_song(
        self,
        query: str,
    ) -> dict:
        if not query.strip():
            raise ValueError(
                "Music search query cannot be empty."
            )

        search_query = (
            f"ytsearch1:{query} official song"
        )

        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(
                options
            ) as ydl:

                info = ydl.extract_info(
                    search_query,
                    download=False,
                )

        except Exception as exc:
            raise RuntimeError(
                f"Online music search failed: {exc}"
            ) from exc

        entries = info.get(
            "entries",
            [],
        )

        if not entries:
            raise RuntimeError(
                f"No online result found for '{query}'."
            )

        result = entries[0]

        # return {
        #     "id": result.get("id"),
        #     "title": result.get(
        #         "title",
        #         "Unknown",
        #     ),
        #     "webpage_url": result.get(
        #         "webpage_url"
        #     ),
        #     "duration": result.get(
        #         "duration"
        #     ),
        # }
        video_id = result.get("id")

        webpage_url = result.get("webpage_url")

        if not webpage_url:
            webpage_url = result.get("url")

        if webpage_url and not webpage_url.startswith("http"):
            webpage_url = f"https://www.youtube.com/watch?v={video_id}"

        if not webpage_url:
            raise RuntimeError(
                f"No usable YouTube URL found for '{query}'."
            )

        return {
            "id": video_id,
            "title": result.get(
                "title",
                "Unknown",
            ),
            "webpage_url": webpage_url,
            "duration": result.get(
                "duration"
            ),
        }

    def get_audio_stream(
        self,
        video_url: str,
    ) -> dict:
        """
        Extract an audio stream URL from a YouTube URL.
        """

        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,

            # Prefer a single audio stream.
            "format": (
                "bestaudio[ext=m4a]/"
                "bestaudio/best"
            ),
        }

        try:
            with yt_dlp.YoutubeDL(
                options
            ) as ydl:

                info = ydl.extract_info(
                    video_url,
                    download=False,
                )

        except Exception as exc:
            raise RuntimeError(
                f"Could not extract online audio: {exc}"
            ) from exc

        stream_url = info.get("url")

        if not stream_url:
            raise RuntimeError(
                "No playable audio stream was found."
            )

        return {
            "title": info.get(
                "title",
                "Unknown",
            ),
            "stream_url": stream_url,
            "webpage_url": info.get(
                "webpage_url",
                video_url,
            ),
            "duration": info.get(
                "duration"
            ),
        }
        
    def search_random_song(self) -> dict:
        """
        Search YouTube for a random song candidate.

        Used when the user asks for:
            "play any song"
            "play something"
            "choose a song"
        """

        import random

        search_queries = [
            "popular official songs",
            "latest popular songs",
            "Tamil popular songs",
            "English popular songs",
            "Indian popular songs",
        ]

        query = random.choice(search_queries)

        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    f"ytsearch5:{query}",
                    download=False,
                )

        except Exception as exc:
            raise RuntimeError(
                f"Random online music search failed: {exc}"
            ) from exc

        entries = [
            entry
            for entry in info.get("entries", [])
            if entry
        ]

        if not entries:
            raise RuntimeError(
                "No random online song was found."
            )

        result = random.choice(entries)

        video_id = result.get("id")

        webpage_url = result.get("webpage_url")

        if not webpage_url:
            webpage_url = result.get("url")

        if webpage_url and not webpage_url.startswith("http"):
            webpage_url = f"https://www.youtube.com/watch?v={video_id}"

        if not webpage_url:
            raise RuntimeError(
                "No usable YouTube URL found for random song."
            )

        return {
            "id": video_id,
            "title": result.get(
                "title",
                "Unknown",
            ),
            "webpage_url": webpage_url,
            "duration": result.get(
                "duration"
            ),
        }
        

class OnlineAudioPlayer:
    """
    Windows online audio player.

    Playback pipeline:

        YouTube
            ↓
        yt-dlp
            ↓
        stdout pipe
            ↓
        ffplay
            ↓
        speakers

    No audio file is downloaded to disk.
    """

    def __init__(self):
        self.yt_process: Optional[subprocess.Popen] = None
        self.ffplay_process: Optional[subprocess.Popen] = None

        self.current_title: Optional[str] = None
        self.current_url: Optional[str] = None

        self._paused = False

    # =========================================================
    # PLAY
    # =========================================================

    # def play(
    #     self,
    #     video_url: str,
    #     title: str = "Unknown",
    # ):
    #     """
    #     Start streaming a YouTube video as audio.
    #     """

    #     self.stop()

    #     yt_command = [
    #         "yt-dlp",
    #         "--no-playlist",
    #         "-f",
    #         "bestaudio[ext=m4a]/bestaudio/best",
    #         "-o",
    #         "-",
    #         video_url,
    #     ]

    #     ffplay_command = [
    #         "ffplay",
    #         "-nodisp",
    #         "-autoexit",
    #         "-loglevel",
    #         "warning",
    #         "-",
    #     ]

    #     try:
    #         self.yt_process = subprocess.Popen(
    #             yt_command,
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.DEVNULL,
    #             stdin=subprocess.DEVNULL,
    #             bufsize=0,
    #             creationflags=subprocess.CREATE_NO_WINDOW,
    #         )

    #         self.ffplay_process = subprocess.Popen(
    #             ffplay_command,
    #             stdin=self.yt_process.stdout,
    #             stdout=subprocess.DEVNULL,
    #             stderr=subprocess.DEVNULL,
    #             creationflags=subprocess.CREATE_NO_WINDOW,
    #         )

    #         self.current_title = title
    #         self.current_url = video_url
    #         self._paused = False
            
    #         return True

    #     except Exception:
    #         self.stop()
    #         raise
    
    def play(
        self,
        video_url: str,
        title: str = "Unknown",
    ) -> bool:
        """
        Start streaming a YouTube video as audio.
        """

        self.stop()

        yt_command = [
            "yt-dlp",
            "--no-playlist",
            "-f",
            "bestaudio[ext=m4a]/bestaudio/best",
            "-o",
            "-",
            video_url,
        ]

        ffplay_command = [
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel",
            "warning",
            "-",
        ]

        try:
            self.yt_process = subprocess.Popen(
                yt_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                bufsize=0,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            self.ffplay_process = subprocess.Popen(
                ffplay_command,
                stdin=self.yt_process.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            self.current_title = title
            self.current_url = video_url
            self._paused = False

            return True

        except Exception:
            self.stop()
            raise

    # =========================================================
    # PAUSE
    # =========================================================

    def pause(self) -> bool:
        """
        Pause ffplay using Windows process suspension.
        """

        if not self.ffplay_process:
            return False

        if self.ffplay_process.poll() is not None:
            return False

        if self._paused:
            return True

        try:
            process = psutil.Process(
                self.ffplay_process.pid
            )

            process.suspend()

            self._paused = True

            return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            return False

    # =========================================================
    # RESUME
    # =========================================================

    def resume(self) -> bool:
        """
        Resume ffplay after pause.
        """

        if not self.ffplay_process:
            return False

        if self.ffplay_process.poll() is not None:
            return False

        if not self._paused:
            return True

        try:
            process = psutil.Process(
                self.ffplay_process.pid
            )

            process.resume()

            self._paused = False

            return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            return False

    # =========================================================
    # STOP
    # =========================================================

    def stop(self):
        """
        Stop both ffplay and yt-dlp.
        """

        self._paused = False

        # Stop ffplay first.
        if self.ffplay_process:
            try:
                if self.ffplay_process.poll() is None:
                    self.ffplay_process.terminate()

                    try:
                        self.ffplay_process.wait(
                            timeout=3
                        )
                    except subprocess.TimeoutExpired:
                        self.ffplay_process.kill()

            except (
                OSError,
                subprocess.SubprocessError,
            ):
                pass

        # Then stop yt-dlp.
        if self.yt_process:
            try:
                if self.yt_process.poll() is None:
                    self.yt_process.terminate()

                    try:
                        self.yt_process.wait(
                            timeout=3
                        )
                    except subprocess.TimeoutExpired:
                        self.yt_process.kill()

            except (
                OSError,
                subprocess.SubprocessError,
            ):
                pass

        self.ffplay_process = None
        self.yt_process = None

        self.current_title = None
        self.current_url = None

    # =========================================================
    # STATE
    # =========================================================

    def is_playing(self) -> bool:
        """
        Return True if ffplay is currently playing.
        """

        if not self.ffplay_process:
            return False

        if self.ffplay_process.poll() is not None:
            return False

        return not self._paused

    def is_paused(self) -> bool:
        """
        Return True if ffplay is currently paused.
        """

        if not self.ffplay_process:
            return False

        if self.ffplay_process.poll() is not None:
            return False

        return self._paused

    def current_song(self) -> Optional[str]:
        """
        Return the currently playing online song title.
        """

        return self.current_title
        



class MusicSource(str, Enum):
    LOCAL = "local"
    ONLINE_AUDIO = "online_audio"
    ONLINE_VIDEO = "online_video"
    
class MusicPlaybackState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class MusicPlaybackController:
    """
    Central music playback router.

    Routing rules:
    - Explicit audio request -> online audio
    - Normal song request -> Brave YouTube video
    - Random request -> random online Brave video
    - No internet -> local fallback
    """

    def __init__(
        self,
        local_manager,
        online_manager,
        online_audio_player,
        brave_video_player,
        wifi_manager,
    ):
        self.local_manager = local_manager
        self.online_manager = online_manager
        self.online_audio_player = online_audio_player
        self.brave_video_player = brave_video_player

        self.source: Optional[MusicSource] = None
        self.state = MusicPlaybackState.STOPPED
        self.current_title: Optional[str] = None
        self.current_url: Optional[str] = None
        self.current_query: Optional[str] = None
        self.wifi_manager = wifi_manager
        

    # ---------------------------------------------------------
    # INTERNET
    # ---------------------------------------------------------


    # ---------------------------------------------------------
    # REQUEST PARSING
    # ---------------------------------------------------------

    def wants_audio(self, request: str) -> bool:
        """
        Audio mode is enabled only when explicitly requested.
        """

        text = request.lower().strip()

        patterns = [
            r"\baudio\b",
            r"\baudio[- ]only\b",
            r"\bin audio mode\b",
            r"\bonly audio\b",
        ]

        return any(re.search(pattern, text) for pattern in patterns)

    def wants_random(self, request: str) -> bool:
        """
        Detect requests such as:
        - play any song
        - play something
        - choose a song
        - play a random song
        """

        text = request.lower().strip()

        random_phrases = [
            "play any song",
            "play something",
            "choose a song",
            "play a random song",
            "random song",
            "pick a song",
            "pick something",
        ]

        return any(phrase in text for phrase in random_phrases)

    def clean_song_query(self, request: str) -> str:
        """
        Convert a natural-language music request into a search query.
        """

        query = request.strip()

        # Remove leading play command.
        query = re.sub(
            r"^\s*play\s+",
            "",
            query,
            flags=re.IGNORECASE,
        )

        # Remove explicit mode words.
        query = re.sub(
            r"\b(audio[- ]only|only audio|in audio mode)\b",
            "",
            query,
            flags=re.IGNORECASE,
        )

        query = re.sub(
            r"\bvideo song\b",
            "",
            query,
            flags=re.IGNORECASE,
        )

        query = re.sub(
            r"\bvideo\b",
            "",
            query,
            flags=re.IGNORECASE,
        )

        query = re.sub(
            r"\bsong\b",
            "",
            query,
            flags=re.IGNORECASE,
        )

        return " ".join(query.split()).strip()

    # ---------------------------------------------------------
    # PUBLIC PLAY
    # ---------------------------------------------------------

    def play(self, request: str) -> dict:
        """
        Main music routing method.
        """

        if not request or not request.strip():
            return {
                "success": False,
                "message": "No song request was provided.",
            }

        # Random request.
        if self.wants_random(request):
            return self._play_random()

        query = self.clean_song_query(request)

        if not query:
            return {
                "success": False,
                "message": "I couldn't determine which song to play.",
            }

        # Explicit audio request.
        if self.wants_audio(request):
            return self._play_online_audio(query)

        # Default = video.
        return self._play_online_video(query)

    # ---------------------------------------------------------
    # ONLINE AUDIO
    # ---------------------------------------------------------

    def _play_online_audio(self, query: str) -> dict:
        """
        Search YouTube and stream audio through yt-dlp -> ffplay.
        """

        if not self.wifi_manager.has_internet():
            return self._fallback_local(query)

        try:
            print(f"[MusicController] Searching YouTube: {query}")

            result = self.online_manager.search_song(query)

            if not result:
                print("[MusicController] No YouTube result found.")
                return self._fallback_local(query)

            video_url = result.get("webpage_url")

            if not video_url:
                print("[MusicController] YouTube result has no URL.")
                return self._fallback_local(query)

            title = result.get("title", query)

            print(f"[MusicController] Audio URL: {video_url}")
            print(f"[MusicController] Audio title: {title}")
            print("[MusicController] Starting audio player...")

            started = self.online_audio_player.play(
                video_url,
                title,
            )

            print(f"[MusicController] Audio player result: {started}")

            # The player may successfully start playback even if its
            # return value is not strictly True.
            if not started:
                if not self.online_audio_player.is_playing():
                    print("[MusicController] Audio playback did not start.")
                    return self._fallback_local(query)

            self.source = MusicSource.ONLINE_AUDIO
            self.state = MusicPlaybackState.PLAYING
            self.current_title = title
            self.current_url = video_url
            self.current_query = query
            

            return {
                "success": True,
                "source": self.source.value,
                "title": title,
                "message": f"Playing {title} in audio mode.",
            }

        except Exception as exc:
            print(f"[MusicController] Online audio failed: {exc}")

            return self._fallback_local(query)

    # ---------------------------------------------------------
    # ONLINE VIDEO
    # ---------------------------------------------------------

    # def _play_online_video(self, query: str) -> dict:
    #     """
    #     Search YouTube and open the result in JARVIS's
    #     dedicated Brave browser session.
    #     """

    #     if not self.wifi_manager.has_internet():
    #         return self._fallback_local(query)

    #     try:
    #         result = self.online_manager.search_song(query)

    #         if not result:
    #             return self._fallback_local(query)

    #         video_url = result.get("webpage_url")

    #         if not video_url:
    #             return self._fallback_local(query)

    #         title = result.get("title", query)

    #         success = self.brave_video.play(
    #             video_url,
    #             title,
    #         )

    #         if not success:
    #             return self._fallback_local(query)

    #         self.source = MusicSource.ONLINE_VIDEO
    #         self.current_title = title
    #         self.current_url = video_url
    #         self.current_query = query

    #         return {
    #             "success": True,
    #             "source": self.source.value,
    #             "title": title,
    #             "message": f"Playing {title} in Brave.",
    #         }

    #     except Exception as exc:
    #         print(
    #             f"[MusicController] Online video failed:\n"
    #             f"{type(exc).__name__}: {exc}"
    #         )

    #         return self._fallback_local(query)
    
    def _play_online_video(self, query: str) -> dict:
        """
        Search YouTube and open the result in JARVIS's
        dedicated Brave browser session.
        """

        if not self.wifi_manager.has_internet():
            print("[MusicController] No internet.")
            return self._fallback_local(query)

        try:
            print(f"[MusicController] Searching YouTube: {query}")

            result = self.online_manager.search_song(query)

            print(f"[MusicController] Search result: {result}")

            if not result:
                print("[MusicController] Search returned no result.")
                return self._fallback_local(query)

            video_url = result.get("webpage_url")

            print(f"[MusicController] Video URL: {video_url}")

            if not video_url:
                print("[MusicController] No video URL.")
                return self._fallback_local(query)

            title = result.get("title", query)

            print(f"[MusicController] Title: {title}")
            print("[MusicController] Starting Brave...")

            success = self.brave_video_player.play(
                video_url,
                title,
            )

            print(f"[MusicController] Brave play result: {success}")

            if not success:
                print("[MusicController] Brave playback returned False.")
                return self._fallback_local(query)

            self.source = MusicSource.ONLINE_VIDEO
            self.state = MusicPlaybackState.PLAYING
            self.current_title = title
            self.current_url = video_url
            self.current_query = query

            return {
                "success": True,
                "source": self.source.value,
                "title": title,
                "message": f"Playing {title} in Brave.",
            }

        except Exception as exc:
            print(
                "[MusicController] Online video failed:\n"
                f"{type(exc).__name__}: {exc}"
            )

            return self._fallback_local(query)

    # ---------------------------------------------------------
    # RANDOM
    # ---------------------------------------------------------

    def _play_random(self) -> dict:
        """
        Random song:
        internet -> random YouTube video
        no internet -> random local song
        """

        if not self.wifi_manager.has_internet():
            return self._play_random_local()

        try:
            result = self.online_manager.search_random_song()

            if not result:
                return self._play_random_local()

            video_url = result.get("webpage_url")

            if not video_url:
                return self._play_random_local()

            title = result.get("title", "Random song")

            success = self.brave_video_player.play(
                video_url,
                title,
            )

            if not success:
                return self._play_random_local()

            self.source = MusicSource.ONLINE_VIDEO
            self.current_title = title
            self.current_url = video_url
            self.current_query = None

            return {
                "success": True,
                "source": self.source.value,
                "title": title,
                "message": f"Playing random song: {title}",
            }

        except Exception as exc:
            print(f"[MusicController] Random online playback failed: {exc}")

            return self._play_random_local()

    # ---------------------------------------------------------
    # LOCAL FALLBACK
    # ---------------------------------------------------------

    def _fallback_local(self, query: str) -> dict:
        """
        Try to play the requested song from the local library.
        """

        try:
            result = self.local_manager.play(query)
            current_song = self.local_manager.current_song()

            if not current_song:
                return {
                    "success": False,
                    "source": MusicSource.LOCAL.value,
                    "title": None,
                    "message": (
                        f"I couldn't find '{query}' in the local music library."
                    ),
                }

            self.source = MusicSource.LOCAL
            self.state = MusicPlaybackState.PLAYING
            self.current_title = current_song
            self.current_url = None
            self.current_query = query

            return {
                "success": True,
                "source": self.source.value,
                "title": current_song,
                "message": (
                    f"Online playback was unavailable. "
                    f"Playing local song: {current_song}"
                ),
                "result": result,
            }

        except Exception as exc:
            return {
                "success": False,
                "source": MusicSource.LOCAL.value,
                "title": None,
                "message": (
                    f"Online playback was unavailable and "
                    f"'{query}' was not found in the local library."
                ),
                "error": str(exc),
            }

    def _play_random_local(self) -> dict:
        """
        Play a random song from the local library.
        """

        try:
            result = self.local_manager.play_random()

            self.source = MusicSource.LOCAL
            self.current_title = self.local_manager.current_song()
            self.current_url = None
            self.current_query = None

            return {
                "success": True,
                "source": self.source.value,
                "title": self.current_title,
                "message": (
                    f"Playing random local song: "
                    f"{self.current_title}"
                ),
                "result": result,
            }

        except Exception as exc:
            return {
                "success": False,
                "source": MusicSource.LOCAL.value,
                "message": "No local songs are available.",
                "error": str(exc),
            }

    # ---------------------------------------------------------
    # CONTROLS
    # ---------------------------------------------------------

    # def pause(self) -> dict:
    #     if self.source == MusicSource.LOCAL:
    #         result = self.local_manager.pause()

    #     elif self.source == MusicSource.ONLINE_AUDIO:
    #         result = self.online_audio_player.pause()

    #     elif self.source == MusicSource.ONLINE_VIDEO:
    #         result = self.brave_video.pause()

    #     else:
    #         return {
    #             "success": False,
    #             "message": "Nothing is currently playing.",
    #         }

    #     return {
    #         "success": bool(result),
    #         "message": "Playback paused." if result else "Unable to pause playback.",
    #     }
    
    def pause(self) -> dict:
        if self.source is None:
            return {
                "success": False,
                "message": "No music is currently playing.",
            }

        try:
            if self.source == MusicSource.ONLINE_VIDEO:
                success = self.brave_video_player.pause()

            elif self.source == MusicSource.ONLINE_AUDIO:
                success = self.online_audio_player.pause()

            elif self.source == MusicSource.LOCAL:
                success = self.local_manager.pause()

            else:
                success = False

            if not success:
                return {
                    "success": False,
                    "message": "Unable to pause the current playback.",
                }

            self.state = MusicPlaybackState.PAUSED

            return {
                "success": True,
                "state": self.state.value,
                "source": self.source.value,
                "message": "Playback paused.",
            }

        except Exception as exc:
            return {
                "success": False,
                "message": "Failed to pause playback.",
                "error": str(exc),
            }
    
    # def resume(self) -> dict:
    #     if self.source == MusicSource.LOCAL:
    #         result = self.local_manager.resume()

    #     elif self.source == MusicSource.ONLINE_AUDIO:
    #         result = self.online_audio_player.resume()

    #     elif self.source == MusicSource.ONLINE_VIDEO:
    #         result = self.brave_video.resume()

    #     else:
    #         return {
    #             "success": False,
    #             "message": "Nothing is currently paused.",
    #         }

    #     return {
    #         "success": bool(result),
    #         "message": "Playback resumed." if result else "Unable to resume playback.",
    #     }
    
    def resume(self) -> dict:
        if self.source is None:
            return {
                "success": False,
                "message": "No music is currently playing.",
            }

        try:
            if self.source == MusicSource.ONLINE_VIDEO:
                success = self.brave_video_player.resume()

            elif self.source == MusicSource.ONLINE_AUDIO:
                success = self.online_audio_player.resume()

            elif self.source == MusicSource.LOCAL:
                success = self.local_manager.resume()

            else:
                success = False

            if not success:
                return {
                    "success": False,
                    "message": "Unable to resume the current playback.",
                }

            self.state = MusicPlaybackState.PLAYING

            return {
                "success": True,
                "state": self.state.value,
                "source": self.source.value,
                "message": "Playback resumed.",
            }

        except Exception as exc:
            return {
                "success": False,
                "message": "Failed to resume playback.",
                "error": str(exc),
            }

    # def stop(self) -> dict:
    #     if self.source == MusicSource.LOCAL:
    #         result = self.local_manager.stop()

    #     elif self.source == MusicSource.ONLINE_AUDIO:
    #         result = self.online_audio_player.stop()

    #     elif self.source == MusicSource.ONLINE_VIDEO:
    #         result = self.brave_video.stop()

    #     else:
    #         return {
    #             "success": False,
    #             "message": "Nothing is currently playing.",
    #         }

    #     self.source = None
    #     self.current_title = None
    #     self.current_url = None
    #     self.current_query = None

    #     return {
    #         "success": bool(result),
    #         "message": "Playback stopped." if result else "Unable to stop playback.",
    #     }
    
    def stop(self) -> dict:
        if self.source is None:
            return {
                "success": True,
                "state": MusicPlaybackState.STOPPED.value,
                "message": "No music is currently playing.",
            }

        try:
            previous_source = self.source

            if previous_source == MusicSource.ONLINE_VIDEO:
                self.brave_video_player.stop()

            elif previous_source == MusicSource.ONLINE_AUDIO:
                self.online_audio_player.stop()

            elif previous_source == MusicSource.LOCAL:
                self.local_manager.stop()

            self.source = None
            self.state = MusicPlaybackState.STOPPED
            self.current_title = None
            self.current_url = None
            self.current_query = None

            return {
                "success": True,
                "state": self.state.value,
                "message": "Playback stopped.",
            }

        except Exception as exc:
            return {
                "success": False,
                "message": "Failed to stop playback.",
                "error": str(exc),
            }
            
    def sync_state(self) -> None:
        """
        Synchronize MusicPlaybackController state with
        the underlying playback engine.
        """

        if self.source == MusicSource.ONLINE_VIDEO:

            if self.brave_video_player.is_video_ended():
                self.source = None
                self.state = MusicPlaybackState.STOPPED
                self.current_title = None
                self.current_url = None
                self.current_query = None
                return

            if self.brave_video_player.is_playing():
                self.state = MusicPlaybackState.PLAYING
                return

            if self.brave_video_player.is_paused():
                self.state = MusicPlaybackState.PAUSED
                return

            return

        if self.source == MusicSource.ONLINE_AUDIO:

            if self.online_audio_player.is_playing():
                self.state = MusicPlaybackState.PLAYING
                return

            if self.online_audio_player.is_paused():
                self.state = MusicPlaybackState.PAUSED
                return

            self.source = None
            self.state = MusicPlaybackState.STOPPED
            self.current_title = None
            self.current_url = None
            self.current_query = None
            return

        if self.source == MusicSource.LOCAL:

            current_song = self.local_manager.current_song()

            if current_song:
                self.current_title = current_song
                
    # def sync_state(self):
    #     """Synchronize controller state with the actual playback state."""

    #     if self.source == MusicSource.LOCAL:
    #         if self.local_manager.is_playing():
    #             self.state = MusicPlaybackState.PLAYING
    #         elif self.local_manager.is_paused():
    #             self.state = MusicPlaybackState.PAUSED
    #         else:
    #             self.state = MusicPlaybackState.STOPPED

    #     elif self.source == MusicSource.ONLINE_AUDIO:
    #         if self.online_audio_player.is_playing():
    #             self.state = MusicPlaybackState.PLAYING
    #         elif self.online_audio_player.is_paused():
    #             self.state = MusicPlaybackState.PAUSED
    #         else:
    #             self.state = MusicPlaybackState.STOPPED

    #     elif self.source == MusicSource.ONLINE_VIDEO:
    #         # Brave/YouTube video
    #         if self.brave_video_player.is_video_ended():
    #             self.state = MusicPlaybackState.STOPPED
    #             self.source = None
    #             self.current_title = None
    #             self.current_url = None
    #             self.current_query = None
    #             return

    #         if self.brave_video_player.is_playing():
    #             self.state = MusicPlaybackState.PLAYING
    #         elif self.brave_video_player.is_paused():
    #             self.state = MusicPlaybackState.PAUSED
    #         else:
    #             self.state = MusicPlaybackState.STOPPED
    
    def playback_status(self) -> dict:
        """
        Return the current playback state.
        """

        self.sync_state()

        return {
            "source": self.source.value if self.source else None,
            "state": self.state.value,
            "title": self.current_title,
            "url": self.current_url,
            "query": self.current_query,
    }

    def current_song(self) -> Optional[str]:
        return self.current_title

    def current_source(self) -> Optional[str]:
        return self.source.value if self.source else None
    
#---------------------------------------------------------------------------Local Music Manager------------------------------------------------------------------------------------
class LocalMusicManager:
    """
    Local music playback manager.

    Local library:
        D:\\refrain!\\songs

    Supported:
        - song discovery
        - song search
        - play
        - pause
        - resume
        - next
        - previous
        - stop

    This manager does not assume that every song exists
    locally.
    """

    SUPPORTED_EXTENSIONS = {
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".m4a",
    }

    def __init__(
        self,
        music_directory: str = r"D:\refrain!\songs",
    ):
        self.music_directory = Path(
            music_directory
        )

        self.songs: list[Path] = []
        self.current_index: int | None = None

        self._is_playing = False
        self._is_paused = False

        pygame.mixer.init()

        self.refresh_library()

    # --------------------------------------------------
    # Library
    # --------------------------------------------------

    def refresh_library(self) -> None:
        """
        Scan the music directory for supported audio files.
        """

        if not self.music_directory.exists():
            self.songs = []
            return

        self.songs = sorted(
            [
                path
                for path in self.music_directory.iterdir()
                if (
                    path.is_file()
                    and path.suffix.lower()
                    in self.SUPPORTED_EXTENSIONS
                )
            ],
            key=lambda path: path.name.lower(),
        )

    def song_count(self) -> int:
        return len(self.songs)

    def find_song(
        self,
        query: str,
    ) -> Path | None:
        """
        Find the best local song matching the query.
        """

        query = query.strip().lower()

        if not query:
            return None

        # Remove extension if the user included it.
        query_without_extension = Path(
            query
        ).stem

        # Exact filename/stem match.
        for song in self.songs:
            stem = song.stem.lower()

            if stem == query_without_extension:
                return song

        # Query contained inside song name.
        for song in self.songs:
            stem = song.stem.lower()

            if query_without_extension in stem:
                return song

        # All query words appear in the song name.
        words = query_without_extension.split()

        for song in self.songs:
            stem = song.stem.lower()

            if all(
                word in stem
                for word in words
            ):
                return song

        return None

    # --------------------------------------------------
    # Playback
    # --------------------------------------------------

    # def play_song(
    #     self,
    #     song: Path,
    # ) -> str:
    #     """
    #     Play a specific local song.
    #     """

    #     try:
    #         pygame.mixer.music.load(
    #             str(song)
    #         )

    #         pygame.mixer.music.play()

    #     except Exception as exc:
    #         return (
    #             f"I couldn't play {song.name}: "
    #             f"{exc}"
    #         )

    #     try:
    #         self.current_index = self.songs.index(
    #             song
    #         )
    #     except ValueError:
    #         self.current_index = None

    #     self.is_playing = True
    #     self.is_paused = False

    #     return f"Playing {song.stem}."
    
    def play_song(
        self,
        song: Path,
    ) -> str:
        """
        Play a specific local song.
        """

        try:
            pygame.mixer.music.load(
                str(song)
            )

            pygame.mixer.music.play()

        except Exception as exc:
            return (
                f"I couldn't play {song.name}: "
                f"{exc}"
            )

        try:
            self.current_index = self.songs.index(
                song
            )
        except ValueError:
            self.current_index = None

        self._is_playing = True
        self._is_paused = False

        return f"Playing {song.stem}."

    def play(
        self,
        query: str,
    ) -> str:
        """
        Find and play a local song.
        """

        self.refresh_library()

        song = self.find_song(query)

        if song is None:
            return (
                f"I couldn't find '{query}' "
                "in the local music library."
            )

        return self.play_song(song)

    # def pause(self) -> str:
    #     if not self.is_playing():
    #         return "No song is currently playing."

    #     if self.is_paused:
    #         return "The song is already paused."

    #     pygame.mixer.music.pause()

    #     self.is_paused = True

    #     return "Music paused."
    
    def pause(self) -> str:
        if not self._is_playing:
            return "No song is currently playing."

        if self._is_paused:
            return "The song is already paused."

        pygame.mixer.music.pause()

        self._is_paused = True

        return "Music paused."

    # def resume(self) -> str:
    #     if not self.is_playing():
    #         return "No song is currently playing."

    #     if not self.is_paused:
    #         return "Music is already playing."

    #     pygame.mixer.music.unpause()

    #     self.is_paused = False

    #     return "Music resumed."
    
    def resume(self) -> str:
        if not self._is_playing:
            return "No song is currently playing."

        if not self._is_paused:
            return "Music is already playing."

        pygame.mixer.music.unpause()

        self._is_paused = False

        return "Music resumed."

    # def stop(self) -> str:
    #     if not self.is_playing():
    #         return "No song is currently playing."

    #     pygame.mixer.music.stop()

    #     self.is_playing = False
    #     self.is_paused = False
    #     self.current_index = None

    #     return "Music stopped."
    
    def stop(self) -> str:
        if not self._is_playing:
            return "No song is currently playing."

        pygame.mixer.music.stop()

        self._is_playing = False
        self._is_paused = False
        self.current_index = None

        return "Music stopped."

    def next(self) -> str:
        self.refresh_library()

        if not self.songs:
            return (
                "There are no songs in the local "
                "music library."
            )

        if self.current_index is None:
            return (
                "There is no current song to skip from."
            )

        next_index = (
            self.current_index + 1
        ) % len(self.songs)

        return self.play_song(
            self.songs[next_index]
        )

    def previous(self) -> str:
        self.refresh_library()

        if not self.songs:
            return (
                "There are no songs in the local "
                "music library."
            )

        if self.current_index is None:
            return (
                "There is no current song to go back from."
            )

        previous_index = (
            self.current_index - 1
        ) % len(self.songs)

        return self.play_song(
            self.songs[previous_index]
        )

    def current_song(self) -> str | None:
        if (
            self.current_index is None
            or not self.songs
        ):
            return None

        if (
            self.current_index
            >= len(self.songs)
        ):
            return None

        return self.songs[
            self.current_index
        ].stem
        
    def play_random(self) -> str:
        """
        Choose a random song from the local library
        and play it.
        """

        import random

        self.refresh_library()

        if not self.songs:
            return (
                "There are no songs in the local "
                "music library."
            )

        song = random.choice(
            self.songs
        )

        return self.play_song(song)



# class PlayMusicTool(Tool):

#     @property
#     def name(self) -> str:
#         return "play_music"

#     @property
#     def description(self) -> str:
#         return (
#             "Play a song from the local JARVIS music library. "
#             "Use this only when local music playback is requested "
#             "or when the agent explicitly chooses the local "
#             "music source."
#         )

#     @property
#     def parameters(self) -> dict[str, Any]:
#         return {
#             "type": "object",
#             "properties": {
#                 "query": {
#                     "type": "string",
#                     "description": (
#                         "The song name to search for in "
#                         "the local music library."
#                     ),
#                 },
#             },
#             "required": [
#                 "query",
#             ],
#         }

#     def __init__(
#         self,
#         manager: LocalMusicManager,
#     ):
#         self.manager = manager

#     def execute(
#         self,
#         arguments: dict[str, Any],
#     ) -> str:
#         query = arguments.get("query")

#         if not query:
#             raise ValueError(
#                 "The 'query' argument is required."
#             )

#         return self.manager.play(query)


class PlayMusicTool(Tool):
    @property
    def name(self) -> str:
        return "play_music"

    @property
    def description(self) -> str:
        return (
            "Play music requested by the user. "
            "Normal song requests use YouTube video playback in JARVIS's "
            "dedicated Brave browser. "
            "Use audio playback ONLY when the user's request explicitly "
            "contains 'audio', 'audio only', or 'in audio mode'. "
            "Requests such as 'play any song' or 'play a random song' "
            "select a random song. "
            "If internet is unavailable, automatically fall back to the "
            "local music library."
    )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": (
                        "The complete music request from the user, "
                        "for example 'play Pavalamalli', "
                        "'play Pavalamalli audio', or "
                        "'play any song'."
                    ),
                }
            },
            "required": ["request"],
        }

    def __init__(
        self,
        controller,
    ):
        self.controller = controller

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> dict:
        request = arguments.get("request", "").strip()

        if not request:
            return {
                "success": False,
                "message": "No music request was provided.",
            }

        return self.controller.play(request)
    
    
class PauseMusicTool(Tool):
    @property
    def name(self) -> str:
        return "pause_music"

    @property
    def description(self) -> str:
        return (
            "Pause the currently active music playback. "
            "Use this for commands such as 'pause', "
            "'pause the song', or 'pause music'."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        controller,
    ):
        self.controller = controller

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> dict:
        return self.controller.pause()

class ResumeMusicTool(Tool):
    @property
    def name(self) -> str:
        return "resume_music"

    @property
    def description(self) -> str:
        return (
            "Resume currently paused music playback. "
            "Use this for commands such as 'resume', "
            "'continue', 'resume the song', or 'continue the music'."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        controller,
    ):
        self.controller = controller

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> dict:
        return self.controller.resume()

class NextMusicTool(Tool):

    @property
    def name(self) -> str:
        return "next_music"

    @property
    def description(self) -> str:
        return (
            "Skip to the next song in the local music library."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        manager: LocalMusicManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.next()


class PreviousMusicTool(Tool):

    @property
    def name(self) -> str:
        return (
            "previous_music"
        )

    @property
    def description(self) -> str:
        return (
            "Go back to the previous song in the "
            "local music library."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        manager: LocalMusicManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.previous()

class StopMusicTool(Tool):
    @property
    def name(self) -> str:
        return "stop_music"

    @property
    def description(self) -> str:
        return (
            "Stop the currently active music playback completely. "
            "Use this for commands such as 'stop', "
            "'stop the song', or 'stop music'."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        controller,
    ):
        self.controller = controller

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> dict:
        return self.controller.stop()


class ListLocalSongsTool(Tool):

    @property
    def name(self) -> str:
        return "list_local_songs"

    @property
    def description(self) -> str:
        return (
            "List songs currently available in the local "
            "JARVIS music library. Use this when the user "
            "asks to list, show, or see available local songs."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        manager: LocalMusicManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        self.manager.refresh_library()

        if not self.manager.songs:
            return (
                "There are no songs in the local "
                "music library."
            )

        lines = [
            (
                f"Local music library contains "
                f"{len(self.manager.songs)} songs:"
            )
        ]

        for index, song in enumerate(
            self.manager.songs,
            start=1,
        ):
            lines.append(
                f"{index}. {song.stem}"
            )

        return "\n".join(lines)
