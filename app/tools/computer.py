from typing import Any
import wmi
import subprocess
import asyncio
import urllib.request
import io
import win32clipboard
import pyperclip
from PIL import ImageGrab
from app.tools.base import Tool
from pathlib import Path
from datetime import datetime
from PIL import ImageGrab
from pycaw.pycaw import (AudioUtilities, IAudioEndpointVolume)
from winrt.windows.devices.enumeration import (DeviceInformation,DeviceInformationKind)
from winrt.windows.devices.radios import ( Radio, RadioAccessStatus, RadioKind, RadioState, )
WIFI_PIPE = r"\\.\pipe\JARVISWiFi"


#-------------------------------------------------------------------Brightness---------------------------------------------------------------------------------------------------


class BrightnessManager:
    """
    Controls the brightness of the Windows internal display.
    Uses the WMI monitor brightness interface provided by Windows.
    """

    def __init__(self):
        self._wmi = None
        self._connect()

    def _connect(self) -> None:
        self._wmi = wmi.WMI(
            namespace="root\\wmi"
        )

    def _get_monitor(self):
        monitors = (
            self._wmi.WmiMonitorBrightness()
        )

        if not monitors:
            raise RuntimeError(
                "No WMI-compatible display was found."
            )

        return monitors[0]

    def _get_methods(self):
        methods = (
            self._wmi.WmiMonitorBrightnessMethods()
        )

        if not methods:
            raise RuntimeError(
                "Brightness control is not available "
                "through Windows WMI."
            )

        return methods

    def get_brightness(self) -> int:
        """
        Return current display brightness as a percentage.
        """

        monitor = self._get_monitor()

        return int(
            monitor.CurrentBrightness
        )

    def set_brightness(
        self,
        percentage: int,
    ) -> str:
        """
        Set display brightness from 0 to 100 percent.
        """

        percentage = max(
            0,
            min(100, int(percentage)),
        )

        methods = self._get_methods()

        for method in methods:
            method.WmiSetBrightness(
                Timeout=1,
                Brightness=percentage,
            )

        return (
            f"Brightness set to {percentage}%."
        )

    def increase(
        self,
        amount: int = 10,
    ) -> str:
        """
        Increase brightness.
        """

        current = self.get_brightness()

        target = min(
            100,
            current + amount,
        )

        return self.set_brightness(
            target
        )

    def decrease(
        self,
        amount: int = 10,
    ) -> str:
        """
        Decrease brightness.
        """

        current = self.get_brightness()

        target = max(
            0,
            current - amount,
        )

        return self.set_brightness(
            target
        )
        

class GetBrightnessTool(Tool):
    @property
    def name(self) -> str:
        return "get_brightness"


    @property
    def description(self) -> str:
        return (
            "Get the current Windows display brightness "
            "as a percentage."
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
        manager: BrightnessManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        brightness = (
            self.manager.get_brightness()
        )

        return (
            f"Current brightness is {brightness}%."
        )


class SetBrightnessTool(Tool):
    @property
    def name(self) -> str:
        return "set_brightness"


    @property
    def description(self) -> str:
        return (
            "Set the Windows display brightness to an "
            "exact percentage from 0 to 100."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "percentage": {
                    "type": "integer",
                    "description": (
                        "Target brightness percentage "
                        "from 0 to 100."
                    ),
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": [
                "percentage",
            ],
        }

    def __init__(
        self,
        manager: BrightnessManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        percentage = arguments.get(
            "percentage"
        )

        if not isinstance(
            percentage,
            int,
        ):
            return (
                "Brightness percentage must be an integer."
            )

        if not 0 <= percentage <= 100:
            return (
                "Brightness percentage must be "
                "between 0 and 100."
            )

        return self.manager.set_brightness(
            percentage
        )

class IncreaseBrightnessTool(Tool):
    @property
    def name(self) -> str:
        return "increase_brightness"

    @property
    def description(self) -> str:
        return (
            "Increase Windows display brightness. "
            "If no amount is specified, increase it by "
            "10 percentage points."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "integer",
                    "description": (
                        "Number of percentage points "
                        "to increase."
                    ),
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": [],
        }

    def __init__(
        self,
        manager: BrightnessManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        amount = arguments.get(
            "amount",
            10,
        )

        if not isinstance(amount, int):
            return (
                "Brightness increase amount "
                "must be an integer."
            )

        if not 1 <= amount <= 100:
            return (
                "Brightness increase amount must be "
                "between 1 and 100."
            )

        return self.manager.increase(
            amount
        )
    
class DecreaseBrightnessTool(Tool):
    @property
    def name(self) -> str:
        return "decrease_brightness"

    @property
    def description(self) -> str:
        return (
            "Decrease Windows display brightness. "
            "If no amount is specified, decrease it by "
            "10 percentage points."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "integer",
                    "description": (
                        "Number of percentage points "
                        "to decrease."
                    ),
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": [],
        }

    def __init__(
        self,
        manager: BrightnessManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        amount = arguments.get(
            "amount",
            10,
        )

        if not isinstance(amount, int):
            return (
                "Brightness decrease amount "
                "must be an integer."
            )

        if not 1 <= amount <= 100:
            return (
                "Brightness decrease amount must be "
                "between 1 and 100."
            )

        return self.manager.decrease(
            amount
        )



#-------------------------------------------------------------------Volume---------------------------------------------------------------------------------------------------

class VolumeManager:
    """
    Controls the default Windows audio output device.
    """

    def __init__(self):
        self._volume = None
        self._connect()

    def _connect(self) -> None:
        """
        Connect to the current Windows default audio endpoint.
        """

        device = AudioUtilities.GetSpeakers()

        interface = device.EndpointVolume

        self._volume = interface

    def get_volume(self) -> int:
        """
        Return current volume as a percentage.
        """

        self._ensure_connection()

        scalar = self._volume.GetMasterVolumeLevelScalar()

        return round(scalar * 100)

    def set_volume(
        self,
        percentage: int,
    ) -> str:
        """
        Set master volume from 0 to 100 percent.
        """

        self._ensure_connection()

        percentage = max(
            0,
            min(100, int(percentage)),
        )

        scalar = percentage / 100.0

        self._volume.SetMasterVolumeLevelScalar(
            scalar,
            None,
        )

        return (
            f"Volume set to {percentage}%."
        )

    def increase(
        self,
        amount: int = 10,
    ) -> str:
        """
        Increase volume by the requested percentage.
        """

        current = self.get_volume()

        target = min(
            100,
            current + amount,
        )

        return self.set_volume(target)

    def decrease(
        self,
        amount: int = 10,
    ) -> str:
        """
        Decrease volume by the requested percentage.
        """

        current = self.get_volume()

        target = max(
            0,
            current - amount,
        )

        return self.set_volume(target)

    def mute(self) -> str:
        """
        Mute the default output device.
        """

        self._ensure_connection()

        self._volume.SetMute(
            1,
            None,
        )

        return "Audio is muted."

    def unmute(self) -> str:
        """
        Unmute the default output device.
        """

        self._ensure_connection()

        self._volume.SetMute(
            0,
            None,
        )

        return "Audio is unmuted."

    def is_muted(self) -> bool:
        """
        Return whether the audio output is muted.
        """

        self._ensure_connection()

        return bool(
            self._volume.GetMute()
        )

    def _ensure_connection(self) -> None:
        if self._volume is None:
            self._connect()
    
class GetVolumeTool(Tool):
    @property
    def name(self) -> str:
        return "get_volume"

    @property
    def description(self) -> str:
        return (
            "Get the current Windows master audio volume "
            "percentage and mute state."
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
        manager: VolumeManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        volume = self.manager.get_volume()
        muted = self.manager.is_muted()

        if muted:
            return (
                f"Current volume is {volume}%, "
                "but audio is muted."
            )

        return (
            f"Current volume is {volume}%."
        )

class SetVolumeTool(Tool):
    @property
    def name(self) -> str:
        return "set_volume"


    @property
    def description(self) -> str:
        return (
            "Set the Windows master audio volume to a "
            "specific percentage from 0 to 100."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "percentage": {
                    "type": "integer",
                    "description": (
                        "Target volume percentage from 0 to 100."
                    ),
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": [
                "percentage",
            ],
        }

    def __init__(
        self,
        manager: VolumeManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        percentage = arguments.get(
            "percentage"
        )

        if not isinstance(
            percentage,
            int,
        ):
            return (
                "Volume percentage must be an integer."
            )

        if not 0 <= percentage <= 100:
            return (
                "Volume percentage must be between "
                "0 and 100."
            )

        return self.manager.set_volume(
            percentage
        )

class IncreaseVolumeTool(Tool):
    @property
    def name(self) -> str:
        return "increase_volume"

    @property
    def description(self) -> str:
        return (
            "Increase the Windows master audio volume. "
            "If no amount is specified, increase it by 10 percentage points."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "integer",
                    "description": (
                        "Number of percentage points to increase."
                    ),
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": [],
        }

    def __init__(
        self,
        manager: VolumeManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        amount = arguments.get(
            "amount",
            10,
        )

        if not isinstance(amount, int):
            return (
                "Volume increase amount must be an integer."
            )

        if not 1 <= amount <= 100:
            return (
                "Volume increase amount must be "
                "between 1 and 100."
            )

        return self.manager.increase(
            amount
        )

class DecreaseVolumeTool(Tool):
    @property
    def name(self) -> str:
        return "decrease_volume"


    @property
    def description(self) -> str:
        return (
            "Decrease the Windows master audio volume. "
            "If no amount is specified, decrease it by 10 percentage points."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "integer",
                    "description": (
                        "Number of percentage points to decrease."
                    ),
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": [],
        }

    def __init__(
        self,
        manager: VolumeManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:

        amount = arguments.get(
            "amount",
            10,
        )

        if not isinstance(amount, int):
            return (
                "Volume decrease amount must be an integer."
            )

        if not 1 <= amount <= 100:
            return (
                "Volume decrease amount must be "
                "between 1 and 100."
            )

        return self.manager.decrease(
            amount
        )

class MuteTool(Tool):
    @property
    def name(self) -> str:
        return "mute_audio"


    @property
    def description(self) -> str:
        return "Mute the Windows master audio output."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        manager: VolumeManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.mute()

class UnmuteTool(Tool):
    @property
    def name(self) -> str:
        return "unmute_audio"


    @property
    def description(self) -> str:
        return "Unmute the Windows master audio output."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        manager: VolumeManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.unmute()



#-------------------------------------------------------------------Wi-Fi---------------------------------------------------------------------------------------------------
class WiFiManager:
    """
    Read-only Windows Wi-Fi and internet connectivity manager.
    This manager cannot enable, disable, or modify Wi-Fi.
    """

    def __init__(self):
        pass

    def _run(
        self,
        command: list[str],
        timeout: int = 10,
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def _get_wifi_interface(self) -> str | None:
        """
        Dynamically find the physical Wi-Fi adapter.
        """

        result = self._run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    "Get-NetAdapter -Physical | "
                    "Where-Object { "
                    "$_.InterfaceDescription -match "
                    "'Wi-Fi|Wireless|802.11|WLAN' "
                    "} | "
                    "Select-Object -First 1 "
                    "-ExpandProperty Name"
                ),
            ]
        )

        if result.returncode != 0:
            return None

        name = result.stdout.strip()

        return name or None

    def _get_adapter_status(self) -> str:
        """
        Get the current Wi-Fi adapter state.
        """

        interface = self._get_wifi_interface()

        if not interface:
            return "Unknown"

        result = self._run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    f"Get-NetAdapter -Name '{interface}' | "
                    "Select-Object -ExpandProperty Status"
                ),
            ]
        )

        if result.returncode != 0:
            return "Unknown"

        return result.stdout.strip()

    def is_enabled(self) -> bool | None:
        """
        Determine whether the Wi-Fi adapter is enabled.
        """

        status = self._get_adapter_status()

        if status.lower() == "disabled":
            return False

        if status.lower() in {
            "up",
            "disconnected",
            "dormant",
        }:
            return True

        return None

    def is_connected(self) -> bool:
        """
        Determine whether the Wi-Fi adapter is connected
        to a wireless network.
        """

        interface = self._get_wifi_interface()

        if not interface:
            return False

        result = self._run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    f"$adapter = Get-NetAdapter "
                    f"-Name '{interface}'; "
                    "if ($adapter.Status -ne 'Up') { "
                    "Write-Output 'False'; "
                    "exit "
                    "} "
                    "$config = Get-NetIPConfiguration "
                    f"-InterfaceAlias '{interface}'; "
                    "if ($config.NetProfile.Name) { "
                    "Write-Output 'True' "
                    "} else { "
                    "Write-Output 'False' "
                    "}"
                ),
            ]
        )

        if result.returncode != 0:
            return False

        return (
            result.stdout.strip().lower()
            == "true"
        )

    def has_internet(self) -> bool:
        """
        Determine whether the computer can reach the internet.

        This checks general internet connectivity, not specifically
        whether the Wi-Fi connection provides the internet.
        """

        test_urls = [
            "https://www.google.com/generate_204",
            "https://www.cloudflare.com/cdn-cgi/trace",
            "https://www.msftconnecttest.com/connecttest.txt",
        ]

        for url in test_urls:
            try:
                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "JARVIS-M3",
                    },
                )

                with urllib.request.urlopen(
                    request,
                    timeout=5,
                ) as response:

                    if 200 <= response.status < 400:
                        return True

            except Exception:
                continue

        return False

    def status(self) -> str:
        """
        Return a complete read-only connectivity status.
        """

        enabled = self.is_enabled()

        if enabled is False:
            return (
                "Wi-Fi is disabled."
            )

        if enabled is None:
            return (
                "I could not determine the Wi-Fi adapter state."
            )

        connected = self.is_connected()

        if not connected:
            internet = self.has_internet()

            if internet:
                return (
                    "Wi-Fi is enabled but not connected "
                    "to a wireless network. Internet is "
                    "reachable through another connection."
                )

            return (
                "Wi-Fi is enabled but not connected "
                "to a wireless network. Internet is "
                "not reachable."
            )

        internet = self.has_internet()

        if internet:
            return (
                "Wi-Fi is enabled and connected. "
                "Internet connectivity is reachable."
            )

        return (
            "Wi-Fi is enabled and connected to a "
            "wireless network, but internet connectivity "
            "is not reachable."
        )

class GetWiFiStatusTool(Tool):
    @property
    def name(self) -> str:
        return "get_wifi_status"

    @property
    def description(self) -> str:
        return (
            "Check the current Wi-Fi and internet connectivity "
            "status. Use this when the user asks whether Wi-Fi "
            "is connected, whether the internet is working, "
            "or whether the computer is online."
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
        manager: WiFiManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.status()



#-------------------------------------------------------------------Bluetooth---------------------------------------------------------------------------------------------------

class BluetoothManager:
    """
    Windows Bluetooth radio and connection manager.

    Supported operations:
    - Check Bluetooth ON/OFF state
    - Turn Bluetooth ON
    - Turn Bluetooth OFF
    - Find currently connected Bluetooth devices

    This manager does not pair, unpair, or manually connect
    individual Bluetooth devices.
    """

    # def _run_async(
    #     self,
    #     coroutine,
    # ):
    #     """
    #     Run a WinRT async operation from normal synchronous
    #     JARVIS tool code.
    #     """
    #     try:
    #         return asyncio.run(coroutine)
    #     except RuntimeError:
    #         loop = asyncio.new_event_loop()

    #         try:
    #             return loop.run_until_complete(
    #                 coroutine
    #             )
    #         finally:
    #             loop.close()
    
    def _run_async(self, operation):
        """
        Run a WinRT async operation from normal synchronous
        JARVIS tool code.
        """
        async def wait_for_operation():
            return await operation

        return asyncio.run(wait_for_operation())

    def _get_bluetooth_radio(self):
        """
        Find the Bluetooth radio exposed by Windows.
        """

        radios = self._run_async(
            Radio.get_radios_async()
        )

        for radio in radios:
            if radio.kind == RadioKind.BLUETOOTH:
                return radio

        return None

    def is_enabled(self) -> bool | None:
        """
        Return:

        True  -> Bluetooth is ON
        False -> Bluetooth is OFF
        None  -> Bluetooth radio could not be found
        """

        radio = self._get_bluetooth_radio()

        if radio is None:
            return None

        if radio.state == RadioState.ON:
            return True

        if radio.state == RadioState.OFF:
            return False

        return None

    def set_enabled(
        self,
        enabled: bool,
    ) -> str:
        """
        Turn the Bluetooth radio ON or OFF.
        """

        radio = self._get_bluetooth_radio()

        if radio is None:
            return (
                "I could not find a Bluetooth radio "
                "on this computer."
            )

        current_state = radio.state

        if enabled and current_state == RadioState.ON:
            return "Bluetooth is already on."

        if (
            not enabled
            and current_state == RadioState.OFF
        ):
            return "Bluetooth is already off."

        access = self._run_async(
            Radio.request_access_async()
        )

        if access != RadioAccessStatus.ALLOWED:
            return (
                "Windows did not allow JARVIS to "
                "change the Bluetooth state."
            )

        target_state = (
            RadioState.ON
            if enabled
            else RadioState.OFF
        )

        result = self._run_async(
            radio.set_state_async(target_state)
        )

        if result != RadioAccessStatus.ALLOWED:
            return (
                "Windows rejected the request to "
                + (
                    "turn Bluetooth on."
                    if enabled
                    else "turn Bluetooth off."
                )
            )

        # Give Windows a moment to apply the state,
        # then verify the actual resulting state.
        import time

        time.sleep(0.5)

        verified = self._get_bluetooth_radio()

        if verified is None:
            return (
                "The Bluetooth radio disappeared while "
                "changing its state."
            )

        if enabled:
            if verified.state == RadioState.ON:
                return "Bluetooth is now on."

            return (
                "Windows accepted the request, but "
                "Bluetooth is not currently on."
            )

        if verified.state == RadioState.OFF:
            return "Bluetooth is now off."

        return (
            "Windows accepted the request, but "
            "Bluetooth is not currently off."
        )

    def turn_on(self) -> str:
        return self.set_enabled(True)

    def turn_off(self) -> str:
        return self.set_enabled(False)

    # def get_connected_devices(self) -> list[str]:
    #     """
    #     Return the names of currently connected Bluetooth
    #     devices.

    #     Windows exposes connection state through the
    #     DeviceInformation properties.
    #     """

    #     devices = self._run_async(
    #         DeviceInformation.find_all_async(
    #             "System.Devices.Aep.ProtocolId:=\""
    #             "{e0cbf06c-cd8b-4647-bb8a-263b43f0f974}\""
    #         )
    #     )

    #     connected = []

    #     for device in devices:
    #         try:
    #             is_connected = device.properties.get(
    #                 "System.Devices.Aep.IsConnected",
    #                 False,
    #             )

    #             if is_connected:
    #                 name = (
    #                     device.name
    #                     or "Unknown Bluetooth device"
    #                 )

    #                 if name not in connected:
    #                     connected.append(name)

    #         except Exception:
    #             continue

    #     return connected
    
    def get_connected_devices(self) -> list[str]:
        """
        Return the names of currently connected Bluetooth devices.
        """
        selector = (
            'System.Devices.Aep.ProtocolId:="'
            '{e0cbf06c-cd8b-4647-bb8a-263b43f0f974}"'
        )

        devices = self._run_async(
            DeviceInformation.find_all_async_with_kind_aqs_filter_and_additional_properties(
                selector,
                ["System.Devices.Aep.IsConnected"],
                DeviceInformationKind.ASSOCIATION_ENDPOINT,
            )
        )

        connected = []

        for device in devices:
            try:
                is_connected = device.properties.get(
                    "System.Devices.Aep.IsConnected",
                    False,
                )

                if is_connected:
                    name = device.name or "Unknown Bluetooth device"

                    if name not in connected:
                        connected.append(name)

            except Exception:
                continue

        return connected

    def status(self) -> str:
        """
        Return a human-readable Bluetooth status.
        """

        enabled = self.is_enabled()

        if enabled is None:
            return (
                "I could not determine the Bluetooth "
                "radio status."
            )

        if not enabled:
            return "Bluetooth is off."

        devices = self.get_connected_devices()

        if not devices:
            return (
                "Bluetooth is on, but no Bluetooth "
                "device is connected."
            )

        if len(devices) == 1:
            return (
                "Bluetooth is on and connected to "
                f"{devices[0]}."
            )

        lines = [
            "Bluetooth is on and connected to:"
        ]

        for device in devices:
            lines.append(
                f"- {device}"
            )

        return "\n".join(lines)

class GetBluetoothStatusTool(Tool):

    @property
    def name(self) -> str:
        return "get_bluetooth_status"

    @property
    def description(self) -> str:
        return (
            "Check whether Bluetooth is on or off and "
            "report which Bluetooth devices are currently "
            "connected."
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
        manager: BluetoothManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.status()


class BluetoothOnTool(Tool):

    @property
    def name(self) -> str:
        return "bluetooth_on"

    @property
    def description(self) -> str:
        return (
            "Turn the computer's Bluetooth radio on."
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
        manager: BluetoothManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.turn_on()


class BluetoothOffTool(Tool):

    @property
    def name(self) -> str:
        return "bluetooth_off"

    @property
    def description(self) -> str:
        return (
            "Turn the computer's Bluetooth radio off."
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
        manager: BluetoothManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.turn_off()



#-------------------------------------------------------------------Clipboard---------------------------------------------------------------------------------------------------


class ClipboardManager:
    """
    Windows text clipboard manager.

    Supported operations:
    - Read text from clipboard
    - Write text to clipboard
    - Clear clipboard

    This manager intentionally handles text only.
    """

    def get_text(self) -> str:
        try:
            # import pyperclip

            text = pyperclip.paste()

            if text is None:
                return ""

            return str(text)

        except Exception as exc:
            raise RuntimeError(
                f"Could not read the clipboard: {exc}"
            ) from exc

    def set_text(self, text: str) -> str:
        if not isinstance(text, str):
            text = str(text)

        try:
            # import pyperclip

            pyperclip.copy(text)

            return "Text copied to the clipboard."

        except Exception as exc:
            raise RuntimeError(
                f"Could not write to the clipboard: {exc}"
            ) from exc

    def clear(self) -> str:
        try:
            # import pyperclip

            pyperclip.copy("")

            return "Clipboard cleared."

        except Exception as exc:
            raise RuntimeError(
                f"Could not clear the clipboard: {exc}"
            ) from exc


class GetClipboardTool(Tool):

    @property
    def name(self) -> str:
        return "get_clipboard"

    @property
    def description(self) -> str:
        return (
            "Read the current text content of the system "
            "clipboard. Use this only when the user explicitly "
            "asks what is in their clipboard or asks to read it."
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
        manager: ClipboardManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        text = self.manager.get_text()

        if not text:
            return "The clipboard is empty."

        return text


class SetClipboardTool(Tool):

    @property
    def name(self) -> str:
        return "set_clipboard"

    @property
    def description(self) -> str:
        return (
            "Copy the specified text to the system clipboard."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": (
                        "The exact text to copy to the clipboard."
                    ),
                },
            },
            "required": [
                "text",
            ],
        }

    def __init__(
        self,
        manager: ClipboardManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        text = arguments.get("text")

        if text is None:
            raise ValueError(
                "The 'text' argument is required."
            )

        return self.manager.set_text(text)


class ClearClipboardTool(Tool):

    @property
    def name(self) -> str:
        return "clear_clipboard"

    @property
    def description(self) -> str:
        return "Clear the current system clipboard."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __init__(
        self,
        manager: ClipboardManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        return self.manager.clear()



#-------------------------------------------------------------------Screenshot---------------------------------------------------------------------------------------------------

class ScreenshotManager:
    """
    Windows screenshot manager.

    Captures the entire primary display and saves the
    screenshot to JARVIS's local screenshot directory.
    """

    def __init__(self):
        self.screenshot_dir = Path(r"D:\pics")

        self.screenshot_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def take_screenshot(self) -> str:
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = f"screenshot_{timestamp}.png"

        output_path = self.screenshot_dir / filename

        try:
            image = ImageGrab.grab()

            # 1. Save screenshot
            image.save(
                output_path,
                "PNG",
            )

            # 2. Copy screenshot to Windows clipboard
            self.copy_to_clipboard(image)

        except Exception as exc:
            raise RuntimeError(
                f"Could not capture screenshot: {exc}"
            ) from exc

        return str(output_path)
    
    def copy_to_clipboard(self, image):
        output = io.BytesIO()

        image.convert("RGB").save(
            output,
            "BMP",
        )

        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()

        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(
                win32clipboard.CF_DIB,
                data,
            )
        finally:
            win32clipboard.CloseClipboard()

class TakeScreenshotTool(Tool):

    @property
    def name(self) -> str:
        return "take_screenshot"

    @property
    def description(self) -> str:
        return (
            "Capture the current computer screen and save "
            "the screenshot locally. Use this when the user "
            "asks to take, capture, or save a screenshot."
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
        manager: ScreenshotManager,
    ):
        self.manager = manager

    def execute(
        self,
        arguments: dict[str, Any],
    ) -> str:
        path = self.manager.take_screenshot()

        return (
            f"Screenshot captured successfully. "
            f"Saved to: {path}"
        )

