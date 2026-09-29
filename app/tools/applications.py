import os
import psutil
import json
import subprocess
from dataclasses import dataclass
from typing import Any

from app.tools.base import Tool

@dataclass(frozen=True)
class ApplicationInfo:
    name: str
    app_id: str

class ApplicationManager:
    """
    Discovers applications registered with the Windows Start Menu
    and launches them without exposing an arbitrary shell to the LLM.
    """
    
    APPLICATION_ALIASES = {
        "vs code": "visual studio code",
        "vscode": "visual studio code",
        "vs": "visual studio code",
        "chatgpt": "chatgpt classic",
        "gpt": "chatgpt classic",
    }


    def __init__(self):
        self._applications: list[ApplicationInfo] = []
        self.refresh()

    def refresh(self) -> None:
        """
        Refresh the application index from Windows.
        """

        command = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "Get-StartApps | "
                "Select-Object Name, AppID | "
                "ConvertTo-Json -Compress"
            ),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Windows application discovery failed: "
                + result.stderr.strip()
            )

        output = result.stdout.strip()

        if not output:
            self._applications = []
            return

        data = json.loads(output)

        if isinstance(data, dict):
            data = [data]

        applications = []

        for item in data:
            name = str(item.get("Name", "")).strip()
            app_id = str(item.get("AppID", "")).strip()

            if not name or not app_id:
                continue

            applications.append(
                ApplicationInfo(
                    name=name,
                    app_id=app_id,
                )
            )

        self._applications = applications

    # def find(
    #     self,
    #     application: str,
    # ) -> list[ApplicationInfo]:
    #     """
    #     Find applications using exact and partial name matching.
    #     """

    #     query = application.strip().lower()

    #     if not query:
    #         return []

    #     exact_matches = [
    #         app
    #         for app in self._applications
    #         if app.name.lower() == query
    #     ]

    #     if exact_matches:
    #         return exact_matches

    #     partial_matches = [
    #         app
    #         for app in self._applications
    #         if query in app.name.lower()
    #     ]

    #     return partial_matches
    
    def find(
        self,
        application: str,
    ) -> list[ApplicationInfo]:
        """
        Find applications using progressively broader matching.
        Matching order:
        1. Exact name
        2. Normalized name
        3. Token-based matching
        4. Substring matching
        """

        query = self._normalize(application)

        if not query:
            return []
        
        query = self.APPLICATION_ALIASES.get(
            query,
            query,
        )

        # ---------------------------------------------------------
        # 1. Exact normalized match
        # ---------------------------------------------------------

        exact_matches = [
            app
            for app in self._applications
            if self._normalize(app.name) == query
        ]

        if exact_matches:
            return exact_matches

        # ---------------------------------------------------------
        # 2. Token-based match
        # ---------------------------------------------------------

        query_tokens = set(query.split())

        token_matches = []

        for app in self._applications:
            app_tokens = set(
                self._normalize(app.name).split()
            )

            if query_tokens.issubset(app_tokens):
                token_matches.append(app)

        if token_matches:
            return token_matches

        # ---------------------------------------------------------
        # 3. Substring match
        # ---------------------------------------------------------

        substring_matches = [
            app
            for app in self._applications
            if query in self._normalize(app.name)
        ]

        return substring_matches

    @staticmethod
    def _normalize(value: str) -> str:
        """
        Normalize an application name for comparison.
        """

        value = value.lower().strip()

        replacements = {
            ".": " ",
            "_": " ",
            "-": " ",
            "(": " ",
            ")": " ",
        }

        for old, new in replacements.items():
            value = value.replace(old, new)

        return " ".join(
            value.split()
        )


    def launch(
        self,
        application: str,
    ) -> str:
        """
        Find and launch an application.

        Only application IDs discovered from Windows are used.
        The caller cannot provide an arbitrary command.
        """

        matches = self.find(application)

        if not matches:
            return (
                f"I could not find an installed application "
                f"matching '{application}'."
            )

        if len(matches) > 1:
            names = [
                app.name
                for app in matches[:10]
            ]

            return (
                f"I found multiple applications matching "
                f"'{application}': "
                + ", ".join(names)
                + "."
            )

        app = matches[0]

        launch_target = (
            f"shell:AppsFolder\\{app.app_id}"
        )

        try:
            subprocess.Popen(
                [
                    "explorer.exe",
                    launch_target,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

        except Exception as exc:
            return (
                f"Failed to launch '{app.name}': "
                f"{type(exc).__name__}: {exc}"
            )

        return (
            f"Successfully launched '{app.name}'."
        )
        
    def close(
        self,
        application: str,
    ) -> str:
        """
        Gracefully close an application's visible Windows processes.
        The application name is resolved through the existing
        application discovery system. No arbitrary process name
        supplied by the LLM is executed.
        """

        matches = self.find(application)

        if not matches:
            return (
                f"I could not find an installed application "
                f"matching '{application}'."
            )

        if len(matches) > 1:
            names = [
                app.name
                for app in matches[:10]
            ]

            return (
                f"I found multiple applications matching "
                f"'{application}': "
                + ", ".join(names)
                + "."
            )

        app = matches[0]

        running = self._find_running_processes(
            app
        )

        if not running:
            return (
                f"'{app.name}' is not currently running."
            )

        closed = 0
        failed = []

        for process in running:
            try:
                process.terminate()
                closed += 1

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ) as exc:
                failed.append(
                    f"{type(exc).__name__}"
                )

        if closed == 0:
            return (
                f"I could not close '{app.name}'."
            )

        if failed:
            return (
                f"Requested '{app.name}' to close, "
                f"but some processes could not be terminated."
            )

        return (
            f"Successfully requested '{app.name}' to close."
        )

    def _find_running_processes(
        self,
        app: ApplicationInfo,
    ) -> list[psutil.Process]:
        """
        Find running processes associated with an application.
        The initial implementation uses the application's
        discovered AppID and process metadata where available.
        """

        processes = []

        app_name = self._normalize(app.name)

        for process in psutil.process_iter(
            ["pid", "name", "exe"],
        ):
            try:
                info = process.info

                process_name = self._normalize(
                    info.get("name") or ""
                )

                if not process_name:
                    continue

                process_base = process_name.rsplit(
                    ".",
                    1,
                )[0]

                app_tokens = set(
                    app_name.split()
                )

                process_tokens = set(
                    process_base.split()
                )

                if (
                    app_name in process_name
                    or process_name in app_name
                    or (
                        app_tokens
                        and app_tokens.intersection(
                            process_tokens
                        )
                    )
                ):
                    processes.append(process)

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

        return processes
    
    def is_running(
        self,
        application: str,
    ) -> str:
        """
        Check whether an installed application is currently running.
        """

        matches = self.find(application)

        if not matches:
            return (
                f"I could not find an installed application "
                f"matching '{application}'."
            )

        if len(matches) > 1:
            names = [
                app.name
                for app in matches[:10]
            ]

            return (
                f"I found multiple applications matching "
                f"'{application}': "
                + ", ".join(names)
                + "."
            )

        app = matches[0]

        running = self._find_running_processes(app)

        if running:
            return (
                f"'{app.name}' is currently running."
            )

        return (
            f"'{app.name}' is not currently running."
        )



class LaunchApplicationTool(Tool):
    @property
    def name(self) -> str:
        return "launch_applications"

    @property
    def description(self) -> str:
        return (
            "Launch one or more installed Windows applications "
            "by name. Use this when the user asks to open, "
            "launch, start, or run applications. If the user "
            "asks to open multiple applications, include every "
            "requested application in the applications list."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "applications": {
                    "type": "array",
                    "description": (
                        "List of application names to launch."
                    ),
                    "items": {
                        "type": "string",
                    },
                    "minItems": 1,
                },
            },
            "required": [
                "applications",
            ],
        }

    def __init__(
        self,
        manager: ApplicationManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        applications = arguments.get(
            "applications"
        )

        if not isinstance(applications, list):
            return (
                "The applications argument must be a list."
            )

        if not applications:
            return (
                "No applications were provided."
            )

        results = []

        for application in applications:

            if not isinstance(application, str):
                results.append(
                    "Invalid application name."
                )
                continue

            application = application.strip()

            if not application:
                results.append(
                    "Empty application name."
                )
                continue

            result = self.manager.launch(
                application
            )

            results.append(result)

        return "\n".join(results)
    

class CloseApplicationTool(Tool):
    @property
    def name(self) -> str:
        return "close_applications"

    @property
    def description(self) -> str:
        return (
            "Close one or more running Windows applications "
            "by name. Use this when the user asks to close, "
            "quit, or exit applications. If the user asks to "
            "close multiple applications, include every "
            "requested application in the applications list."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "applications": {
                    "type": "array",
                    "description": (
                        "List of application names to close."
                    ),
                    "items": {
                        "type": "string",
                    },
                    "minItems": 1,
                },
            },
            "required": [
                "applications",
            ],
        }

    def __init__(
        self,
        manager: ApplicationManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        applications = arguments.get(
            "applications"
        )

        if not isinstance(applications, list):
            return (
                "The applications argument must be a list."
            )

        if not applications:
            return (
                "No applications were provided."
            )

        results = []

        for application in applications:

            if not isinstance(application, str):
                results.append(
                    "Invalid application name."
                )
                continue

            application = application.strip()

            if not application:
                results.append(
                    "Empty application name."
                )
                continue

            result = self.manager.close(
                application
            )

            results.append(result)

        return "\n".join(results)
    

class IsApplicationRunningTool(Tool):
    @property
    def name(self) -> str:
        return "is_application_running"

    @property
    def description(self) -> str:
        return (
            "Check whether one or more installed Windows "
            "applications are currently running. Use this "
            "when the user asks whether an application is "
            "open, running, active, or already started."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "applications": {
                    "type": "array",
                    "description": (
                        "List of application names to check."
                    ),
                    "items": {
                        "type": "string",
                    },
                    "minItems": 1,
                },
            },
            "required": [
                "applications",
            ],
        }

    def __init__(
        self,
        manager: ApplicationManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        applications = arguments.get(
            "applications"
        )

        if not isinstance(applications, list):
            return (
                "The applications argument must be a list."
            )

        if not applications:
            return (
                "No applications were provided."
            )

        results = []

        for application in applications:

            if not isinstance(application, str):
                results.append(
                    "Invalid application name."
                )
                continue

            application = application.strip()

            if not application:
                results.append(
                    "Empty application name."
                )
                continue

            result = self.manager.is_running(
                application
            )

            results.append(result)

        return "\n".join(results)

