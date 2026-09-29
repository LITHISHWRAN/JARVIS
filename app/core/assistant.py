from collections.abc import Iterator
from typing import Any

from app.agent.executor import AgentExecutor
from app.config import CONFIG
from app.core.context import ContextManager
from app.core.state import ConversationState
from app.llm.llama_cpp import LocalLLM
from app.tools.registry import ToolRegistry
from app.security.policy import SecurityPolicy
from app.tools.system import GetTimeTool
from app.tools.applications import (ApplicationManager, LaunchApplicationTool, CloseApplicationTool, IsApplicationRunningTool)
from app.tools.web import ( WebSearchManager, WebSearchTool)

from app.tools.music import (
    LocalMusicManager,
    PlayMusicTool,
    PauseMusicTool,
    ResumeMusicTool,
    NextMusicTool,
    PreviousMusicTool,
    StopMusicTool,
    ListLocalSongsTool,
)

from app.tools.computer import (
    VolumeManager,
    GetVolumeTool,
    SetVolumeTool,
    IncreaseVolumeTool,
    DecreaseVolumeTool,
    MuteTool,
    UnmuteTool,


    BrightnessManager,
    GetBrightnessTool,
    SetBrightnessTool,
    IncreaseBrightnessTool,
    DecreaseBrightnessTool,

    WiFiManager,
    GetWiFiStatusTool,
    
    BluetoothManager,
    GetBluetoothStatusTool,
    BluetoothOnTool,
    BluetoothOffTool,
    
    ClipboardManager,
    GetClipboardTool,
    SetClipboardTool,
    ClearClipboardTool,
    
    ScreenshotManager,
    TakeScreenshotTool,
    
    )



class Assistant:

    def __init__(self):
        self.state = ConversationState()

        self.context = ContextManager()

        self.llm = LocalLLM(
            base_url=CONFIG.llm.base_url,
            model=CONFIG.llm.model,
        )

        self.tools = ToolRegistry()
        
        self.application_manager = ApplicationManager()
        self.volume_manager = VolumeManager()
        self.brightness_manager = BrightnessManager()
        self.wifi_manager = WiFiManager()
        self.bluetooth_manager = BluetoothManager()
        self.clipboard_manager = ClipboardManager()
        self.screenshot_manager = ScreenshotManager()
        self.web_search_manager = WebSearchManager()
        self.music_manager = LocalMusicManager()
        


        
        self.tools.register_many([
            GetTimeTool(),

            LaunchApplicationTool(self.application_manager),
            CloseApplicationTool(self.application_manager),
            IsApplicationRunningTool(self.application_manager),

            GetVolumeTool(self.volume_manager),
            SetVolumeTool(self.volume_manager),
            IncreaseVolumeTool(self.volume_manager),
            DecreaseVolumeTool(self.volume_manager),
            MuteTool(self.volume_manager),
            UnmuteTool(self.volume_manager),

            GetBrightnessTool(self.brightness_manager),
            SetBrightnessTool(self.brightness_manager),
            IncreaseBrightnessTool(self.brightness_manager),
            DecreaseBrightnessTool(self.brightness_manager),
            
            GetWiFiStatusTool(self.wifi_manager),
            
            GetBluetoothStatusTool(self.bluetooth_manager),
            BluetoothOnTool(self.bluetooth_manager),
            BluetoothOffTool(self.bluetooth_manager),
            
            GetClipboardTool( self.clipboard_manager ),
            SetClipboardTool( self.clipboard_manager ),
            ClearClipboardTool( self.clipboard_manager ),
            
            TakeScreenshotTool(self.screenshot_manager),
            
            WebSearchTool( self.web_search_manager ),
            
            PlayMusicTool(self.music_manager),
            PauseMusicTool(self.music_manager),
            ResumeMusicTool(self.music_manager),
            NextMusicTool(self.music_manager),
            PreviousMusicTool(self.music_manager),
            StopMusicTool(self.music_manager),
            ListLocalSongsTool(self.music_manager),


        ])
        self.security = SecurityPolicy()

        
        # self.security.block("get_current_time")

        self.agent = AgentExecutor(
            llm=self.llm,
            tools=self.tools,
            state=self.state,
            context=self.context,
            security=self.security,
        )

    def start(
        self,
        system_prompt: str,
    ) -> None:

        self.state.messages.clear()

        self.state.messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

        self.state.reset_task()

    def ask(
        self,
        user_input: str,
        enable_thinking: bool | None = None,
    ) -> str:

        user_input = user_input.strip()

        if not user_input:
            return ""

        self.state.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        return self.agent.run(
            enable_thinking=enable_thinking
        )

    def ask_stream(
        self,
        user_input: str,
        enable_thinking: bool | None = None,
    ) -> Iterator[str]:

        user_input = user_input.strip()

        if not user_input:
            return

        self.state.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        yield from self.agent.run_stream(
            enable_thinking=enable_thinking
        )


    def clear(self) -> None:
        self.state.messages.clear()
        self.state.reset_task()

    def history(self) -> list[dict[str, Any]]:
        return list(self.state.messages)

    def context_preview(
        self,
    ) -> list[dict[str, Any]]:
        return self.context.build(
            self.state.messages
        )


