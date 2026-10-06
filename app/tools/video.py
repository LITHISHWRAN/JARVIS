# # app/tools/video.py

# from pathlib import Path
# import subprocess
# import threading
# from typing import Optional
# import time

# from playwright.sync_api import (
#     Browser,
#     Page,
#     Playwright,
#     sync_playwright,
#     Error as PlaywrightError,
# )


# class BraveVideoPlayer:
#     """
#     Dedicated Brave browser video player for JARVIS.

#     Uses:
#     - Dedicated Brave profile
#     - CDP remote debugging
#     - Playwright for YouTube video controls

#     JARVIS only controls the Brave instance launched by this class.
#     """

#     REMOTE_DEBUGGING_PORT = 9222

#     def __init__(self):
#         self.brave_path = self._find_brave()

#         self.profile_directory = (
#             Path.home()
#             / ".jarvis"
#             / "brave-video-profile"
#         )

#         self.profile_directory.mkdir(
#             parents=True,
#             exist_ok=True,
#         )

#         self.process: subprocess.Popen | None = None

#         self.current_url: str | None = None
#         self.current_title: str | None = None

#         # Always initialize these attributes.
#         self._playwright = None
#         self._browser = None
        
#         self._watcher_thread: Optional[threading.Thread] = None
#         self._watcher_stop = threading.Event()

#     # ---------------------------------------------------------
#     # BRAVE DISCOVERY
#     # ---------------------------------------------------------

#     def _find_brave(self) -> str:
#         candidates = [
#             Path(
#                 r"C:\Program Files\BraveSoftware"
#                 r"\Brave-Browser\Application\brave.exe"
#             ),
#             Path(
#                 r"C:\Program Files (x86)\BraveSoftware"
#                 r"\Brave-Browser\Application\brave.exe"
#             ),
#             Path(
#                 Path.home(),
#             )
#             / "AppData"
#             / "Local"
#             / "BraveSoftware"
#             / "Brave-Browser"
#             / "Application"
#             / "brave.exe",
#         ]

#         for path in candidates:
#             if path.exists():
#                 return str(path)

#         raise FileNotFoundError(
#             "Brave Browser executable was not found."
#         )

#     # ---------------------------------------------------------
#     # PLAYWRIGHT CONNECTION
#     # ---------------------------------------------------------

#     def _connect(self) -> bool:
#         """
#         Connect Playwright to JARVIS's Brave instance.
#         """

#         if self._browser is not None:
#             try:
#                 if self._browser.is_connected():
#                     return True
#             except Exception:
#                 pass

#         try:
#             if self._playwright is not None:
#                 try:
#                     self._playwright.stop()
#                 except Exception:
#                     pass

#             self._playwright = sync_playwright().start()

#             self._browser = (
#                 self._playwright.chromium.connect_over_cdp(
#                     f"http://127.0.0.1:{self.REMOTE_DEBUGGING_PORT}"
#                 )
#             )

#             return True

#         except Exception as exc:
#             print(
#                 "[BraveVideo] CDP connection failed: "
#                 f"{type(exc).__name__}: {exc}"
#             )

#             self._browser = None

#             return False

#     # ---------------------------------------------------------
#     # FIND YOUTUBE PAGE
#     # ---------------------------------------------------------

#     def _get_video_page(self):
#         """
#         Find the active YouTube page belonging to
#         JARVIS's dedicated Brave profile.
#         """

#         if not self._connect():
#             return None

#         try:
#             contexts = self._browser.contexts

#             for context in contexts:
#                 for page in context.pages:

#                     try:
#                         url = page.url

#                         if (
#                             "youtube.com" in url
#                             or "youtube-nocookie.com" in url
#                         ):
#                             return page

#                     except Exception:
#                         continue

#         except Exception as exc:
#             print(
#                 "[BraveVideo] Failed to inspect pages: "
#                 f"{type(exc).__name__}: {exc}"
#             )

#         return None

#     # ---------------------------------------------------------
#     # PLAY
#     # ---------------------------------------------------------

#     def play(
#         self,
#         video_url: str,
#         title: str = "Unknown",
#     ) -> bool:
#         """
#         Open a YouTube video in JARVIS's dedicated Brave instance.
#         """

#         self.stop()

#         self.current_url = video_url
#         self.current_title = title

#         command = [
#             self.brave_path,
#             f"--user-data-dir={self.profile_directory}",
#             f"--remote-debugging-port={self.REMOTE_DEBUGGING_PORT}",
#             "--autoplay-policy=no-user-gesture-required",
#             "--new-window",
#             video_url,
#         ]

#         try:
#             self.process = subprocess.Popen(
#                 command,
#                 creationflags=subprocess.CREATE_NO_WINDOW,
#             )

#         except Exception as exc:
#             print(
#                 "[BraveVideo] Failed to launch Brave: "
#                 f"{type(exc).__name__}: {exc}"
#             )

#             self.process = None
#             self.current_url = None
#             self.current_title = None

#             return False

#         # Give Brave time to create the CDP endpoint.
#         for _ in range(30):
#             time.sleep(0.2)

#             if self._connect():
#                 break
        
#         self._start_video_watcher()

#         return True
    
#     # def _start_video_watcher(self) -> None:
#     #     """
#     #     Start a background watcher for the currently playing video.
#     #     """

#     #     # Stop an existing watcher first.
#     #     self._watcher_stop.set()

#     #     if (
#     #         self._watcher_thread is not None
#     #         and self._watcher_thread.is_alive()
#     #     ):
#     #         self._watcher_thread.join(timeout=1)

#     #     self._watcher_stop.clear()

#     #     self._watcher_thread = threading.Thread(
#     #         target=self._watch_video_end,
#     #         daemon=True,
#     #         name="jarvis-video-watcher",
#     #     )

#     #     self._watcher_thread.start()

#     #     print("[BraveVideo] Video-end watcher started.")

#     # ---------------------------------------------------------
#     # VIDEO ELEMENT
#     # ---------------------------------------------------------

#     def _video_exists(self, page) -> bool:
#         try:
#             return bool(
#                 page.evaluate(
#                     """
#                     () => {
#                         return document.querySelector("video") !== null;
#                     }
#                     """
#                 )
#             )

#         except Exception:
#             return False

#     # ---------------------------------------------------------
#     # PAUSE
#     # ---------------------------------------------------------

#     def pause(self) -> bool:
#         """
#         Pause the actual YouTube HTML5 video.

#         Retries because YouTube may be navigating/updating
#         its SPA page when the command arrives.
#         """

#         for attempt in range(5):

#             try:
#                 page = self._get_video_page()

#                 if page is None:
#                     print(
#                         "[BraveVideo] Pause: "
#                         "YouTube page not found."
#                     )

#                     time.sleep(0.5)
#                     continue

#                 # Wait briefly for the video element.
#                 for _ in range(10):
#                     if self._video_exists(page):
#                         break

#                     time.sleep(0.2)

#                 result = page.evaluate(
#                     """
#                     () => {
#                         const video =
#                             document.querySelector("video");

#                         if (!video) {
#                             return false;
#                         }

#                         video.pause();

#                         return true;
#                     }
#                     """
#                 )

#                 print(
#                     f"[BraveVideo] Pause result: {result}"
#                 )

#                 return bool(result)

#             except PlaywrightError as exc:
#                 print(
#                     f"[BraveVideo] Pause attempt "
#                     f"{attempt + 1} failed: {exc}"
#                 )

#                 # YouTube navigation destroyed the execution
#                 # context. Reconnect before retrying.
#                 self._reset_connection()

#                 time.sleep(0.5)

#             except Exception as exc:
#                 print(
#                     "[BraveVideo] Pause failed: "
#                     f"{type(exc).__name__}: {exc}"
#                 )

#                 time.sleep(0.5)

#         return False

#     # ---------------------------------------------------------
#     # RESUME
#     # ---------------------------------------------------------

#     def resume(self) -> bool:
#         """
#         Resume the actual YouTube HTML5 video.
#         """

#         for attempt in range(5):

#             try:
#                 page = self._get_video_page()

#                 if page is None:
#                     print(
#                         "[BraveVideo] Resume: "
#                         "YouTube page not found."
#                     )

#                     time.sleep(0.5)
#                     continue

#                 for _ in range(10):
#                     if self._video_exists(page):
#                         break

#                     time.sleep(0.2)

#                 result = page.evaluate(
#                     """
#                     async () => {
#                         const video =
#                             document.querySelector("video");

#                         if (!video) {
#                             return false;
#                         }

#                         await video.play();

#                         return true;
#                     }
#                     """
#                 )

#                 print(
#                     f"[BraveVideo] Resume result: {result}"
#                 )

#                 return bool(result)

#             except PlaywrightError as exc:
#                 print(
#                     f"[BraveVideo] Resume attempt "
#                     f"{attempt + 1} failed: {exc}"
#                 )

#                 self._reset_connection()

#                 time.sleep(0.5)

#             except Exception as exc:
#                 print(
#                     "[BraveVideo] Resume failed: "
#                     f"{type(exc).__name__}: {exc}"
#                 )

#                 time.sleep(0.5)

#         return False

#     # ---------------------------------------------------------
#     # PLAYING STATE
#     # ---------------------------------------------------------

#     def is_playing(self) -> bool:

#         try:
#             page = self._get_video_page()

#             if page is None:
#                 return False

#             return bool(
#                 page.evaluate(
#                     """
#                     () => {
#                         const video =
#                             document.querySelector("video");

#                         return (
#                             video !== null &&
#                             !video.paused &&
#                             !video.ended
#                         );
#                     }
#                     """
#                 )
#             )

#         except Exception:
#             return False

#     # ---------------------------------------------------------
#     # PAUSED STATE
#     # ---------------------------------------------------------

#     def is_paused(self) -> bool:

#         try:
#             page = self._get_video_page()

#             if page is None:
#                 return False

#             return bool(
#                 page.evaluate(
#                     """
#                     () => {
#                         const video =
#                             document.querySelector("video");

#                         return (
#                             video !== null &&
#                             video.paused &&
#                             !video.ended
#                         );
#                     }
#                     """
#                 )
#             )

#         except Exception:
#             return False

#     # ---------------------------------------------------------
#     # RESET CONNECTION
#     # ---------------------------------------------------------

#     def _reset_connection(self):
#         """
#         Reset Playwright/CDP connection without
#         closing Brave.
#         """

#         self._browser = None

#         if self._playwright is not None:
#             try:
#                 self._playwright.stop()
#             except Exception:
#                 pass

#         self._playwright = None

#     # ---------------------------------------------------------
#     # CLEANUP PLAYWRIGHT
#     # ---------------------------------------------------------

#     def _cleanup_playwright(self):
#         if self._playwright is not None:
#             try:
#                 self._playwright.stop()
#             except Exception as exc:
#                 print(
#                     "[BraveVideo] Playwright cleanup failed: "
#                     f"{type(exc).__name__}: {exc}"
#                 )

#         self._playwright = None
#         self._browser = None

#     # ---------------------------------------------------------
#     # STOP
#     # ---------------------------------------------------------

#     # def stop(self) -> bool:
        
#     #     self._watcher_stop.set()

#     #     had_process = (
#     #         self.process is not None
#     #     )

#     #     self._cleanup_playwright()

#     #     if self.process is not None:

#     #         try:
#     #             if self.process.poll() is None:
#     #                 self.process.terminate()

#     #                 try:
#     #                     self.process.wait(
#     #                         timeout=5
#     #                     )
#     #                 except subprocess.TimeoutExpired:
#     #                     self.process.kill()

#     #         except Exception as exc:
#     #             print(
#     #                 "[BraveVideo] Failed to stop Brave: "
#     #                 f"{type(exc).__name__}: {exc}"
#     #             )

#     #     self.process = None
#     #     self.current_url = None
#     #     self.current_title = None

#     #     return had_process
    
#     def stop(self) -> bool:

#         self._watcher_stop.set()

#         watcher = self._watcher_thread

#         if (
#             watcher is not None
#             and watcher.is_alive()
#             and watcher is not threading.current_thread()
#         ):
#             watcher.join(timeout=3)

#         self._watcher_thread = None

#         had_process = (
#             self.process is not None
#         )

#         self._cleanup_playwright()

#         if self.process is not None:

#             try:
#                 if self.process.poll() is None:
#                     self.process.terminate()

#                     try:
#                         self.process.wait(timeout=5)
#                     except subprocess.TimeoutExpired:
#                         self.process.kill()

#             except Exception as exc:
#                 print(
#                     "[BraveVideo] Failed to stop Brave: "
#                     f"{type(exc).__name__}: {exc}"
#                 )

#         self.process = None
#         self.current_url = None
#         self.current_title = None

#         return had_process

#     # ---------------------------------------------------------
#     # CURRENT VIDEO
#     # ---------------------------------------------------------

#     def current_video(self):
#         if self.current_url is None:
#             return None

#         return {
#             "title": self.current_title,
#             "url": self.current_url,
#         }
        
#     def is_video_ended(self) -> bool:
#         """
#         Check whether the currently playing YouTube video has naturally ended.
#         """

#         try:
#             page = self._get_video_page()

#             if not page:
#                 return False

#             ended = page.evaluate(
#                 """
#                 () => {
#                     const video = document.querySelector("video");

#                     if (!video) {
#                         return false;
#                     }

#                     return video.ended === true;
#                 }
#                 """
#             )

#             return bool(ended)

#         except PlaywrightError:
#             return False

#         except Exception:
#             return False
        
    
#     # def _watch_video_end(self) -> None:
#     #     """
#     #     Watch the active YouTube video until it ends.
#     #     """

#     #     while not self._watcher_stop.is_set():

#     #         if self.is_video_ended():
#     #             print("[BraveVideo] Video ended.")

#     #             self._handle_video_end()
#     #             return

#     #         time.sleep(1)
    
#     def _watch_video_end(self) -> None:
#         """
#         Watch the active YouTube video until it ends.
#         """

#         while not self._watcher_stop.is_set():

#             if self.is_video_ended():
#                 print("[BraveVideo] Video ended.")

#                 self._handle_video_end()
#                 return

#             self._watcher_stop.wait(1)
            
        
#     # def _handle_video_end(self) -> None:
#     #     """
#     #     Clean up JARVIS's dedicated Brave instance after video completion.
#     #     """

#     #     print("[BraveVideo] Cleaning up after video completion...")

#     #     self._watcher_stop.set()

#     #     self._cleanup_playwright()

#     #     # if self._brave_process is not None:
#     #     #     try:
#     #     #         if self._brave_process.poll() is None:
#     #     #             self._brave_process.terminate()
#     #     #             self._brave_process.wait(timeout=5)

#     #     #             print("[BraveVideo] JARVIS Brave closed.")

#     #     #     except Exception as exc:
#     #     #         print(f"[BraveVideo] Failed to close Brave: {exc}")

#     #     #     finally:
#     #     #         self._brave_process = None
        
#     #     if self.process is not None:
#     #         try:
#     #             if self.process.poll() is None:
#     #                 self.process.terminate()

#     #                 try:
#     #                     self.process.wait(timeout=5)
#     #                 except subprocess.TimeoutExpired:
#     #                     self.process.kill()

#     #                 print("[BraveVideo] JARVIS Brave closed.")

#     #         except Exception as exc:
#     #             print(
#     #                 f"[BraveVideo] Failed to close Brave: {exc}"
#     #             )

#     #         finally:
#     #             self.process = None
    
#     def _handle_video_end(self) -> None:
#         """
#         Clean up JARVIS's dedicated Brave instance after video completion.
#         """

#         print(
#             "[BraveVideo] Cleaning up after video completion..."
#         )

#         self._watcher_stop.set()

#         self._cleanup_playwright()

#         if self.process is not None:
#             try:
#                 if self.process.poll() is None:
#                     self.process.terminate()

#                     try:
#                         self.process.wait(timeout=5)
#                     except subprocess.TimeoutExpired:
#                         self.process.kill()

#                     print(
#                         "[BraveVideo] JARVIS Brave closed."
#                     )

#             except Exception as exc:
#                 print(
#                     f"[BraveVideo] Failed to close Brave: {exc}"
#                 )

#             finally:
#                 self.process = None

#         self.current_url = None
#         self.current_title = None
#         self._watcher_thread = None
                
                
#     def _start_video_watcher(self) -> None:
#         """
#         Start a background watcher for the currently playing video.
#         """

#         # Stop any previous watcher.
#         self._watcher_stop.set()

#         old_thread = self._watcher_thread

#         if old_thread is not None and old_thread.is_alive():
#             old_thread.join(timeout=3)

#         self._watcher_thread = None

#         # Start a fresh watcher.
#         self._watcher_stop.clear()

#         self._watcher_thread = threading.Thread(
#             target=self._watch_video_end,
#             daemon=True,
#             name="jarvis-video-watcher",
#         )

#         self._watcher_thread.start()

#         print("[BraveVideo] Video-end watcher started.")




from pathlib import Path
import queue
import subprocess
import threading
import time
from typing import Any, Optional

from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    sync_playwright,
    Error as PlaywrightError,
)


class BraveVideoPlayer:
    """
    Dedicated Brave browser video player for JARVIS.

    Architecture:
    - Brave runs as a separate process.
    - One dedicated worker thread owns Playwright completely.
    - Main JARVIS thread sends commands to the worker.
    - The worker monitors the YouTube <video> element.
    - When the video naturally ends, the worker closes Brave.

    This design avoids Playwright Sync API thread-safety problems.
    """

    REMOTE_DEBUGGING_PORT = 9222

    def __init__(self):
        self.brave_path = self._find_brave()

        self.profile_directory = (
            Path.home()
            / ".jarvis"
            / "brave-video-profile"
        )

        self.profile_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Brave process.
        self.process: subprocess.Popen | None = None

        # Current video information.
        self.current_url: str | None = None
        self.current_title: str | None = None

        # -----------------------------------------------------
        # PLAYWRIGHT WORKER
        # -----------------------------------------------------

        self._command_queue: queue.Queue = queue.Queue()

        self._worker_thread: Optional[threading.Thread] = None

        self._worker_ready = threading.Event()

        self._worker_stop = threading.Event()

        self._state_lock = threading.Lock()

        # Worker-owned Playwright objects.
        #
        # IMPORTANT:
        # These objects are ONLY accessed by _playwright_worker().
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    # =========================================================
    # BRAVE DISCOVERY
    # =========================================================

    def _find_brave(self) -> str:
        candidates = [
            Path(
                r"C:\Program Files\BraveSoftware"
                r"\Brave-Browser\Application\brave.exe"
            ),
            Path(
                r"C:\Program Files (x86)\BraveSoftware"
                r"\Brave-Browser\Application\brave.exe"
            ),
            (
                Path.home()
                / "AppData"
                / "Local"
                / "BraveSoftware"
                / "Brave-Browser"
                / "Application"
                / "brave.exe"
            ),
        ]

        for path in candidates:
            if path.exists():
                return str(path)

        raise FileNotFoundError(
            "Brave Browser executable was not found."
        )

    # =========================================================
    # WORKER MANAGEMENT
    # =========================================================

    def _ensure_worker(self) -> None:
        """
        Start the dedicated Playwright worker if it is not running.
        """

        if (
            self._worker_thread is not None
            and self._worker_thread.is_alive()
        ):
            return

        self._worker_stop.clear()
        self._worker_ready.clear()

        self._worker_thread = threading.Thread(
            target=self._playwright_worker,
            daemon=True,
            name="jarvis-playwright-worker",
        )

        self._worker_thread.start()

        # Wait for Playwright to initialize.
        if not self._worker_ready.wait(timeout=10):
            print(
                "[BraveVideo] Playwright worker failed to start."
            )

    def _submit(
        self,
        command: str,
        *args: Any,
        timeout: float = 15,
    ) -> Any:
        """
        Send a command to the Playwright worker.

        All Playwright operations happen inside the worker thread.
        """

        self._ensure_worker()

        result_queue: queue.Queue = queue.Queue(maxsize=1)

        self._command_queue.put(
            (
                command,
                args,
                result_queue,
            )
        )

        try:
            success, result = result_queue.get(
                timeout=timeout
            )

        except queue.Empty:
            print(
                f"[BraveVideo] Command timed out: {command}"
            )
            return False

        if success:
            return result

        print(
            f"[BraveVideo] Command failed: "
            f"{command}: {result}"
        )

        return False

    # =========================================================
    # PLAYWRIGHT WORKER
    # =========================================================

    def _playwright_worker(self) -> None:
        """
        Dedicated thread that owns ALL Playwright operations.

        No other thread may access:
        - self._playwright
        - self._browser
        - Playwright pages
        - page.evaluate()
        """

        try:
            self._playwright = sync_playwright().start()

            self._worker_ready.set()

            print(
                "[BraveVideo] Playwright worker started."
            )

            while not self._worker_stop.is_set():

                # -------------------------------------------------
                # Process queued commands.
                # -------------------------------------------------

                try:
                    command, args, result_queue = (
                        self._command_queue.get(
                            timeout=0.25
                        )
                    )

                except queue.Empty:
                    self._check_video_end()
                    continue

                try:
                    result = self._execute_command(
                        command,
                        *args,
                    )

                    result_queue.put(
                        (
                            True,
                            result,
                        )
                    )

                except Exception as exc:
                    result_queue.put(
                        (
                            False,
                            f"{type(exc).__name__}: {exc}",
                        )
                    )

                # Check whether the video naturally ended.
                self._check_video_end()

        except Exception as exc:
            print(
                "[BraveVideo] Playwright worker crashed: "
                f"{type(exc).__name__}: {exc}"
            )

        finally:
            self._cleanup_playwright_worker()

            self._worker_ready.set()

            print(
                "[BraveVideo] Playwright worker stopped."
            )

    # =========================================================
    # COMMAND DISPATCH
    # =========================================================

    def _execute_command(
        self,
        command: str,
        *args: Any,
    ) -> Any:
        
        if command == "__shutdown__":
            self._worker_stop.set()
            return True
        if command == "connect":
            return self._connect_worker()

        if command == "pause":
            return self._pause_worker()

        if command == "resume":
            return self._resume_worker()

        if command == "is_playing":
            return self._is_playing_worker()

        if command == "is_paused":
            return self._is_paused_worker()

        if command == "is_video_ended":
            return self._is_video_ended_worker()

        if command == "stop":
            return self._stop_worker()

        raise ValueError(
            f"Unknown Playwright command: {command}"
        )

    # =========================================================
    # PLAYWRIGHT CONNECTION
    # =========================================================

    def _connect_worker(self) -> bool:
        """
        Connect to JARVIS's Brave instance.

        MUST ONLY be called by the Playwright worker.
        """

        if self._browser is not None:
            try:
                if self._browser.is_connected():
                    return True
            except Exception:
                pass

        try:
            self._browser = (
                self._playwright.chromium.connect_over_cdp(
                    "http://127.0.0.1:"
                    f"{self.REMOTE_DEBUGGING_PORT}"
                )
            )

            print(
                "[BraveVideo] Connected to Brave via CDP."
            )

            return True

        except Exception as exc:
            print(
                "[BraveVideo] CDP connection failed: "
                f"{type(exc).__name__}: {exc}"
            )

            self._browser = None

            return False

    # =========================================================
    # FIND YOUTUBE PAGE
    # =========================================================

    def _get_video_page_worker(self) -> Page | None:
        """
        Find the active YouTube page.

        MUST ONLY be called by the Playwright worker.
        """

        if not self._connect_worker():
            return None

        try:
            for context in self._browser.contexts:

                for page in context.pages:

                    try:
                        url = page.url

                        if (
                            "youtube.com" in url
                            or "youtube-nocookie.com" in url
                        ):
                            return page

                    except Exception:
                        continue

        except Exception as exc:
            print(
                "[BraveVideo] Failed to inspect pages: "
                f"{type(exc).__name__}: {exc}"
            )

        return None

    # =========================================================
    # PLAY
    # =========================================================

    def play(
        self,
        video_url: str,
        title: str = "Unknown",
    ) -> bool:
        """
        Open a YouTube video in JARVIS's dedicated Brave.
        """

        # Stop previous video first.
        self.stop()

        with self._state_lock:
            self.current_url = video_url
            self.current_title = title

        command = [
            self.brave_path,
            f"--user-data-dir={self.profile_directory}",
            (
                "--remote-debugging-port="
                f"{self.REMOTE_DEBUGGING_PORT}"
            ),
            "--autoplay-policy=no-user-gesture-required",
            "--new-window",
            video_url,
        ]

        try:
            self.process = subprocess.Popen(
                command,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

        except Exception as exc:
            print(
                "[BraveVideo] Failed to launch Brave: "
                f"{type(exc).__name__}: {exc}"
            )

            self.process = None

            with self._state_lock:
                self.current_url = None
                self.current_title = None

            return False

        # Start Playwright worker.
        self._ensure_worker()

        # Give Brave time to create the CDP endpoint.
        connected = False

        for _ in range(40):

            result = self._submit(
                "connect",
                timeout=3,
            )

            if result:
                connected = True
                break

            time.sleep(0.25)

        if not connected:
            print(
                "[BraveVideo] Could not connect to Brave."
            )

            self.stop()
            return False

        print(
            "[BraveVideo] Video monitoring started."
        )

        return True

    # =========================================================
    # VIDEO STATE HELPERS
    # =========================================================

    def _video_exists_worker(
        self,
        page: Page,
    ) -> bool:
        try:
            return bool(
                page.evaluate(
                    """
                    () => {
                        return (
                            document.querySelector("video")
                            !== null
                        );
                    }
                    """
                )
            )

        except Exception:
            return False

    # =========================================================
    # PAUSE
    # =========================================================

    def _pause_worker(self) -> bool:
        """
        Pause YouTube video.

        Runs entirely inside the Playwright worker.
        """

        page = self._get_video_page_worker()

        if page is None:
            return False

        try:
            for _ in range(10):

                if self._video_exists_worker(page):
                    break

                page.wait_for_timeout(200)

            result = page.evaluate(
                """
                () => {
                    const video =
                        document.querySelector("video");

                    if (!video) {
                        return false;
                    }

                    video.pause();

                    return true;
                }
                """
            )

            print(
                f"[BraveVideo] Pause result: {result}"
            )

            return bool(result)

        except PlaywrightError as exc:
            print(
                "[BraveVideo] Pause failed: "
                f"{type(exc).__name__}: {exc}"
            )

            return False

        except Exception as exc:
            print(
                "[BraveVideo] Pause failed: "
                f"{type(exc).__name__}: {exc}"
            )

            return False

    def pause(self) -> bool:
        return bool(
            self._submit(
                "pause",
                timeout=10,
            )
        )

    # =========================================================
    # RESUME
    # =========================================================

    def _resume_worker(self) -> bool:
        """
        Resume YouTube video.

        Runs entirely inside the Playwright worker.
        """

        page = self._get_video_page_worker()

        if page is None:
            return False

        try:
            for _ in range(10):

                if self._video_exists_worker(page):
                    break

                page.wait_for_timeout(200)

            result = page.evaluate(
                """
                async () => {
                    const video =
                        document.querySelector("video");

                    if (!video) {
                        return false;
                    }

                    await video.play();

                    return true;
                }
                """
            )

            print(
                f"[BraveVideo] Resume result: {result}"
            )

            return bool(result)

        except PlaywrightError as exc:
            print(
                "[BraveVideo] Resume failed: "
                f"{type(exc).__name__}: {exc}"
            )

            return False

        except Exception as exc:
            print(
                "[BraveVideo] Resume failed: "
                f"{type(exc).__name__}: {exc}"
            )

            return False

    def resume(self) -> bool:
        return bool(
            self._submit(
                "resume",
                timeout=10,
            )
        )

    # =========================================================
    # PLAYING STATE
    # =========================================================

    def _is_playing_worker(self) -> bool:

        page = self._get_video_page_worker()

        if page is None:
            return False

        try:
            return bool(
                page.evaluate(
                    """
                    () => {
                        const video =
                            document.querySelector("video");

                        return (
                            video !== null &&
                            !video.paused &&
                            !video.ended
                        );
                    }
                    """
                )
            )

        except Exception:
            return False

    def is_playing(self) -> bool:
        return bool(
            self._submit(
                "is_playing",
                timeout=5,
            )
        )

    # =========================================================
    # PAUSED STATE
    # =========================================================

    def _is_paused_worker(self) -> bool:

        page = self._get_video_page_worker()

        if page is None:
            return False

        try:
            return bool(
                page.evaluate(
                    """
                    () => {
                        const video =
                            document.querySelector("video");

                        return (
                            video !== null &&
                            video.paused &&
                            !video.ended
                        );
                    }
                    """
                )
            )

        except Exception:
            return False

    def is_paused(self) -> bool:
        return bool(
            self._submit(
                "is_paused",
                timeout=5,
            )
        )

    # =========================================================
    # VIDEO ENDED
    # =========================================================

    def _is_video_ended_worker(self) -> bool:
        """
        Check whether the current YouTube video ended.

        Runs ONLY inside the Playwright worker.
        """

        page = self._get_video_page_worker()

        if page is None:
            return False

        try:
            return bool(
                page.evaluate(
                    """
                    () => {
                        const video =
                            document.querySelector("video");

                        if (!video) {
                            return false;
                        }

                        return video.ended === true;
                    }
                    """
                )
            )

        except Exception:
            return False

    def is_video_ended(self) -> bool:
        return bool(
            self._submit(
                "is_video_ended",
                timeout=5,
            )
        )

    # =========================================================
    # AUTOMATIC VIDEO-END WATCHER
    # =========================================================

    def _check_video_end(self) -> None:
        """
        Called by the Playwright worker itself.

        This is NOT another thread.

        Therefore Playwright is always accessed from
        the same thread that created it.
        """

        if self.process is None:
            return

        try:
            if self.process.poll() is not None:
                return

        except Exception:
            return

        page = self._get_video_page_worker()

        if page is None:
            return

        try:
            state = page.evaluate(
                """
                () => {
                    const video =
                        document.querySelector("video");

                    if (!video) {
                        return {
                            exists: false,
                            ended: false
                        };
                    }

                    return {
                        exists: true,
                        ended: video.ended === true
                    };
                }
                """
            )

            if not state:
                return

            if (
                state.get("exists")
                and state.get("ended")
            ):
                print(
                    "[BraveVideo] Video ended."
                )

                self._handle_video_end_worker()

        except PlaywrightError:
            # Page may be navigating.
            return

        except Exception:
            return

    # =========================================================
    # HANDLE VIDEO END
    # =========================================================

    def _handle_video_end_worker(self) -> None:
        """
        Close the dedicated Brave instance after
        natural video completion.

        Runs inside the Playwright worker.
        """

        print(
            "[BraveVideo] Cleaning up after "
            "video completion..."
        )

        # -----------------------------------------------------
        # Clean Playwright first.
        # -----------------------------------------------------

        # self._cleanup_playwright_worker()
        self._worker_stop.set()

        # -----------------------------------------------------
        # Then close Brave.
        # -----------------------------------------------------

        process = self.process

        if process is not None:

            try:
                if process.poll() is None:

                    process.terminate()

                    try:
                        process.wait(
                            timeout=5
                        )

                    except subprocess.TimeoutExpired:
                        process.kill()

                        try:
                            process.wait(
                                timeout=2
                            )
                        except Exception:
                            pass

                    print(
                        "[BraveVideo] "
                        "JARVIS Brave closed."
                    )

            except Exception as exc:
                print(
                    "[BraveVideo] Failed to close Brave: "
                    f"{type(exc).__name__}: {exc}"
                )

            finally:
                self.process = None

        with self._state_lock:
            self.current_url = None
            self.current_title = None
            
        self._worker_thread = None

    # =========================================================
    # STOP
    # =========================================================

    # def _stop_worker(self) -> bool:
    #     """
    #     Stop Playwright connection.

    #     Runs inside the Playwright worker.
    #     """

    #     self._cleanup_playwright_worker()

    #     return True
    
    def _stop_worker(self) -> bool:
        """
        Stop the Playwright worker.

        Runs inside the Playwright worker.
        """

        self._worker_stop.set()

        return True

    # def stop(self) -> bool:
    #     """
    #     Stop the current Brave video safely.

    #     Playwright cleanup is performed by its owner thread.
    #     """

    #     had_process = self.process is not None

    #     if (
    #         self._worker_thread is not None
    #         and self._worker_thread.is_alive()
    #     ):
    #         self._submit(
    #             "stop",
    #             timeout=10,
    #         )

    #     process = self.process

    #     if process is not None:

    #         try:
    #             if process.poll() is None:

    #                 process.terminate()

    #                 try:
    #                     process.wait(
    #                         timeout=5
    #                     )

    #                 except subprocess.TimeoutExpired:
    #                     process.kill()

    #                     try:
    #                         process.wait(
    #                             timeout=2
    #                         )
    #                     except Exception:
    #                         pass

    #         except Exception as exc:
    #             print(
    #                 "[BraveVideo] Failed to stop Brave: "
    #                 f"{type(exc).__name__}: {exc}"
    #             )

    #         finally:
    #             self.process = None

    #     with self._state_lock:
    #         self.current_url = None
    #         self.current_title = None

    #     return had_process
    
    def stop(self) -> bool:
        """
        Stop the current Brave video safely.

        Stops the Playwright worker first, then closes Brave.
        """

        had_process = self.process is not None

        # -----------------------------------------------------
        # Stop Playwright worker
        # -----------------------------------------------------

        worker = self._worker_thread

        if worker is not None and worker.is_alive():

            self._submit(
                "stop",
                timeout=10,
            )

            # Wait for the worker to finish its cleanup.
            if (
                worker is not threading.current_thread()
            ):
                worker.join(timeout=5)

        # Worker is now dead.
        self._worker_thread = None

        # -----------------------------------------------------
        # Close Brave
        # -----------------------------------------------------

        process = self.process

        if process is not None:

            try:
                if process.poll() is None:

                    process.terminate()

                    try:
                        process.wait(timeout=5)

                    except subprocess.TimeoutExpired:

                        process.kill()

                        try:
                            process.wait(timeout=2)
                        except Exception:
                            pass

            except Exception as exc:

                print(
                    "[BraveVideo] Failed to stop Brave: "
                    f"{type(exc).__name__}: {exc}"
                )

            finally:
                self.process = None

        # -----------------------------------------------------
        # Clear current video state
        # -----------------------------------------------------

        with self._state_lock:
            self.current_url = None
            self.current_title = None

        return had_process

    # =========================================================
    # PLAYWRIGHT CLEANUP
    # =========================================================

    def _cleanup_playwright_worker(self) -> None:
        """
        Clean up Playwright.

        IMPORTANT:
        This method must ONLY be called by the worker thread.
        """

        if self._browser is not None:

            try:
                # We intentionally do not close the browser
                # because Brave itself is managed separately.
                pass

            except Exception:
                pass

        self._browser = None

        if self._playwright is not None:

            try:
                self._playwright.stop()

            except Exception as exc:
                print(
                    "[BraveVideo] Playwright cleanup failed: "
                    f"{type(exc).__name__}: {exc}"
                )

            finally:
                self._playwright = None

    # =========================================================
    # CURRENT VIDEO
    # =========================================================

    def current_video(self):
        with self._state_lock:

            if self.current_url is None:
                return None

            return {
                "title": self.current_title,
                "url": self.current_url,
            }

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self) -> None:
        """
        Final cleanup for JARVIS shutdown.
        """

        print(
            "[BraveVideo] Closing video player..."
        )

        self.stop()

        self._worker_stop.set()

        # Wake the worker if it is waiting for a command.
        self._command_queue.put(
            (
                "__shutdown__",
                (),
                queue.Queue(),
            )
        )

        worker = self._worker_thread

        if (
            worker is not None
            and worker.is_alive()
            and worker is not threading.current_thread()
        ):
            worker.join(timeout=5)

        self._worker_thread = None

        print(
            "[BraveVideo] Video player closed."
        )
