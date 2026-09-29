import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

LOG_DIR = ROOT / "logs"
MODELS_DIR = ROOT / "models"

CACHE_DIR = Path.home() / ".jarvis"


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

def _env(key: str, default: str) -> str:
    """
    Read an environment variable.

    Empty values are treated as missing and fall back to default.
    """
    value = os.environ.get(key, "").strip()
    return value or default


def _bool_env(key: str, default: bool = False) -> bool:
    """
    Parse a boolean environment variable.

    Accepted true values:
        1, true, yes, on

    Everything else is false.
    """
    value = _env(key, "1" if default else "0")

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LLMConfig:
    """
    Configuration for the local llama.cpp + Qwen3 inference server.
    """

    # llama.cpp OpenAI-compatible API
    base_url: str = _env(
        "LLAMA_SERVER_URL",
        "http://127.0.0.1:8080/v1",
    )

    # Model identifier exposed by llama-server
    model: str = _env(
        "LLAMA_MODEL",
        "assistant",
    )

    # Maximum time allowed for a single request
    request_timeout: float = float(
        _env(
            "LLAMA_TIMEOUT",
            "90",
        )
    )

    # llama-server context size.
    #
    # Must match the -c value used when starting llama-server.
    context_tokens: int = int(
        _env(
            "LLAMA_CONTEXT",
            "8192",
        )
    )

    # Maximum number of tool/action iterations allowed
    # during one agent task.
    max_agent_steps: int = int(
        _env(
            "MAX_AGENT_STEPS",
            "8",
        )
    )

    # Safety limit on conversational history.
    #
    # The actual history manager will also enforce a token budget.
    max_history_turns: int = int(
        _env(
            "MAX_HISTORY_TURNS",
            "12",
        )
    )

    # Approximate context occupied by:
    #
    # system prompt
    # tool schemas
    # fixed instructions
    #
    fixed_overhead_tokens: int = int(
        _env(
            "LLAMA_FIXED_OVERHEAD",
            "3400",
        )
    )

    # Reserve space for the model's generated response.
    response_reserve_tokens: int = int(
        _env(
            "LLAMA_RESPONSE_RESERVE",
            "1200",
        )
    )

    # Qwen3 thinking mode.
    #
    # Disabled by default because normal JARVIS commands
    # generally don't require extended reasoning.
    #
    # Complex planning can explicitly enable it per request.
    enable_thinking: bool = _bool_env(
        "LLAMA_THINKING",
        False,
    )

    @property
    def history_token_budget(self) -> int:
        """
        Calculate how much of the context window can safely
        be used for conversation history.
        """

        return max(
            512,
            self.context_tokens
            - self.fixed_overhead_tokens
            - self.response_reserve_tokens,
        )


# ---------------------------------------------------------------------------
# Tool Router Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RouterConfig:
    """
    Configuration for deterministic intent/tool routing.

    The router will eventually allow obvious commands to bypass
    unnecessary LLM reasoning.
    """

    # Score required for automatic execution.
    confident_threshold: float = 0.92

    # Difference between the top two candidates required
    # before treating a request as unambiguous.
    ambiguity_margin: float = 0.15

    # Below this score, the router should not attempt
    # direct execution.
    floor_threshold: float = 0.55


# ---------------------------------------------------------------------------
# Security Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SecurityConfig:
    """
    Configuration for actions that require confirmation.
    """

    # How long a confirmation remains valid.
    confirmation_ttl_seconds: float = float(
        _env(
            "CONFIRMATION_TTL",
            "60",
        )
    )

    # Moving more than this number of files requires confirmation.
    confirm_move_threshold: int = int(
        _env(
            "CONFIRM_MOVE_THRESHOLD",
            "3",
        )
    )


# ---------------------------------------------------------------------------
# Application Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Config:

    llm: LLMConfig = LLMConfig()

    router: RouterConfig = RouterConfig()

    security: SecurityConfig = SecurityConfig()

    # -----------------------------------------------------------------------
    # Caching
    # -----------------------------------------------------------------------

    apps_cache_ttl_seconds: int = int(
        _env(
            "APPS_CACHE_TTL",
            str(24 * 3600),
        )
    )

    # -----------------------------------------------------------------------
    # Filesystem indexing
    # -----------------------------------------------------------------------

    folder_index_ttl_seconds: int = int(
        _env(
            "FOLDER_INDEX_TTL",
            str(3600),
        )
    )

    folder_index_refresh_seconds: int = int(
        _env(
            "FOLDER_INDEX_REFRESH",
            "300",
        )
    )

    # -----------------------------------------------------------------------
    # Debugging
    # -----------------------------------------------------------------------

    trace_enabled: bool = _bool_env(
        "JARVIS_TRACE",
        True,
    )


# ---------------------------------------------------------------------------
# Global configuration instance
# ---------------------------------------------------------------------------

CONFIG = Config()
