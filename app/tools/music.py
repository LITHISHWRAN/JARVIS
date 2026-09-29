from pathlib import Path
from typing import Any

import pygame

from app.tools.base import Tool


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

        self.is_playing = False
        self.is_paused = False

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

        self.is_playing = True
        self.is_paused = False

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

    def pause(self) -> str:
        if not self.is_playing:
            return "No song is currently playing."

        if self.is_paused:
            return "The song is already paused."

        pygame.mixer.music.pause()

        self.is_paused = True

        return "Music paused."

    def resume(self) -> str:
        if not self.is_playing:
            return "No song is currently playing."

        if not self.is_paused:
            return "Music is already playing."

        pygame.mixer.music.unpause()

        self.is_paused = False

        return "Music resumed."

    def stop(self) -> str:
        if not self.is_playing:
            return "No song is currently playing."

        pygame.mixer.music.stop()

        self.is_playing = False
        self.is_paused = False
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
            "Play a song from the local JARVIS music library. "
            "Use a specific song query when the user names a song. "
            "If the user asks to play any song, something random, "
            "or asks JARVIS to choose a song, choose a random song "
            "from the local library."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The song name to search for. "
                        "Leave empty when the user asks JARVIS "
                        "to choose any song."
                    ),
                },
                "selection": {
                    "type": "string",
                    "enum": [
                        "specific",
                        "random",
                    ],
                    "description": (
                        "Use 'specific' when the user names a song. "
                        "Use 'random' when the user asks JARVIS "
                        "to choose any song."
                    ),
                },
            },
            "required": [
                "selection",
            ],
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

        selection = arguments.get(
            "selection",
            "specific",
        )

        query = arguments.get(
            "query",
            "",
        )

        if selection == "random":
            return self.manager.play_random()

        if not query:
            raise ValueError(
                "A song name is required when "
                "selection is 'specific'."
            )

        return self.manager.play(query)


class PauseMusicTool(Tool):

    @property
    def name(self) -> str:
        return "pause_music"

    @property
    def description(self) -> str:
        return "Pause the currently playing music."

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
        return self.manager.pause()


class ResumeMusicTool(Tool):

    @property
    def name(self) -> str:
        return "resume_music"

    @property
    def description(self) -> str:
        return "Resume paused music."

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
        return self.manager.resume()


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
        return "Stop the currently playing music."

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
        return self.manager.stop()


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
