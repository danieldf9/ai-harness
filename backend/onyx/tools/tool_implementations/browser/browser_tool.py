import base64
import json
import os
import subprocess
import threading
from typing import Any
from typing import cast

from sqlalchemy.orm import Session

from onyx.chat.emitter import Emitter
from onyx.server.query_and_chat.placement import Placement
from onyx.server.query_and_chat.streaming_models import CustomToolDelta
from onyx.server.query_and_chat.streaming_models import CustomToolStart
from onyx.server.query_and_chat.streaming_models import Packet
from onyx.tools.interface import Tool
from onyx.tools.models import CustomToolCallSummary
from onyx.tools.models import ToolCallException
from onyx.tools.models import ToolResponse
from onyx.utils.logger import setup_logger

logger = setup_logger()

# Global Playwright state for the worker
_playwright_lock = threading.Lock()
_playwright_instance = None
_browser_context = None
_current_page = None

def _ensure_playwright_page():
    global _playwright_instance, _browser_context, _current_page
    with _playwright_lock:
        if _current_page is not None and not _current_page.is_closed():
            return _current_page
        
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ToolCallException(
                message="Playwright is not installed.",
                llm_facing_message="Playwright is not installed. Please add it to the environment."
            )

        try:
            if _playwright_instance is None:
                _playwright_instance = sync_playwright().start()
            
            # Use a temporary directory for persistent state
            user_data_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "onyx_playwright_state")
            _browser_context = _playwright_instance.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            if _browser_context.pages:
                _current_page = _browser_context.pages[0]
            else:
                _current_page = _browser_context.new_page()
                
            # Basic anti-bot mitigation
            _current_page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
            
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                logger.info("Playwright browsers not found. Installing Chromium...")
                subprocess.run(["playwright", "install", "chromium"], check=True)
                # Retry after installation
                if _browser_context is None:
                    _browser_context = _playwright_instance.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=True,
                        args=["--no-sandbox", "--disable-setuid-sandbox"]
                    )
                    if _browser_context.pages:
                        _current_page = _browser_context.pages[0]
                    else:
                        _current_page = _browser_context.new_page()
            else:
                raise ToolCallException(
                    message=f"Failed to launch browser: {str(e)}",
                    llm_facing_message=f"Could not launch the browser. Error: {str(e)}"
                )
                
        return _current_page


class BrowserToolOverrideKwargs:
    pass


class BrowserTool(Tool[BrowserToolOverrideKwargs]):
    NAME = "browser_interaction"
    DISPLAY_NAME = "Browser"
    DESCRIPTION = (
        "Interact with a web browser to navigate pages, click elements, fill forms, "
        "evaluate JavaScript, and take screenshots. The browser state is persistent. "
        "CRITICAL INSTRUCTION: You have full ability to interact with JavaScript-heavy "
        "dynamic content, click buttons, fill forms, handle authentication flows, "
        "execute scripts, and take screenshots using this tool. NEVER claim you cannot "
        "do these things. If a user asks you to interact with a website or login, USE THIS TOOL."
    )

    def __init__(
        self,
        tool_id: int,
        emitter: Emitter,
    ) -> None:
        super().__init__(emitter=emitter)
        self._id = tool_id

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def description(self) -> str:
        return self.DESCRIPTION

    @property
    def display_name(self) -> str:
        return self.DISPLAY_NAME

    @classmethod
    def is_available(cls, db_session: Session) -> bool:
        return True

    def tool_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.DESCRIPTION,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["navigate", "click", "type", "evaluate", "screenshot", "get_html", "get_text"],
                            "description": "The action to perform in the browser."
                        },
                        "url": {
                            "type": "string",
                            "description": "The URL to navigate to. Required if action is 'navigate'."
                        },
                        "selector": {
                            "type": "string",
                            "description": "The CSS selector for 'click' or 'type' actions."
                        },
                        "text": {
                            "type": "string",
                            "description": "The text to type. Required if action is 'type'."
                        },
                        "script": {
                            "type": "string",
                            "description": "The JavaScript to execute. Required if action is 'evaluate'."
                        }
                    },
                    "required": ["action"],
                },
            },
        }

    def emit_start(self, placement: Placement) -> None:
        self.emitter.emit(
            Packet(
                placement=placement,
                obj=CustomToolStart(tool_name=self.name),
            )
        )

    def run(
        self,
        placement: Placement,
        override_kwargs: BrowserToolOverrideKwargs,
        **llm_kwargs: Any,
    ) -> ToolResponse:
        action = llm_kwargs.get("action")
        if not action:
            raise ToolCallException(
                message="Missing 'action'",
                llm_facing_message="The 'action' parameter is required."
            )

        page = _ensure_playwright_page()
        result_data: dict[str, Any] = {"action": action}
        
        try:
            if action == "navigate":
                url = llm_kwargs.get("url")
                if not url:
                    raise ToolCallException(message="Missing url", llm_facing_message="URL is required for navigate.")
                response = page.goto(url, wait_until="networkidle")
                result_data["status"] = response.status if response else None
                result_data["url"] = page.url
                result_data["title"] = page.title()
                
            elif action == "click":
                selector = llm_kwargs.get("selector")
                if not selector:
                    raise ToolCallException(message="Missing selector", llm_facing_message="Selector is required for click.")
                page.click(selector)
                page.wait_for_load_state("networkidle")
                result_data["url"] = page.url
                result_data["success"] = True
                
            elif action == "type":
                selector = llm_kwargs.get("selector")
                text = llm_kwargs.get("text")
                if not selector or not text:
                    raise ToolCallException(message="Missing selector or text", llm_facing_message="Selector and text are required for type.")
                page.fill(selector, text)
                result_data["success"] = True
                
            elif action == "evaluate":
                script = llm_kwargs.get("script")
                if not script:
                    raise ToolCallException(message="Missing script", llm_facing_message="Script is required for evaluate.")
                eval_result = page.evaluate(script)
                result_data["result"] = eval_result
                
            elif action == "screenshot":
                screenshot_bytes = page.screenshot(full_page=True, type="jpeg", quality=70)
                b64_img = base64.b64encode(screenshot_bytes).decode("utf-8")
                result_data["screenshot_base64"] = b64_img
                result_data["message"] = "Screenshot captured successfully."
                
            elif action == "get_html":
                result_data["html"] = page.content()
                
            elif action == "get_text":
                result_data["text"] = page.evaluate("document.body.innerText")
                
            else:
                raise ToolCallException(
                    message=f"Unknown action {action}",
                    llm_facing_message=f"Unknown action '{action}'"
                )
                
        except Exception as e:
            if isinstance(e, ToolCallException):
                raise
            error_msg = str(e)
            logger.error("BrowserTool error: %s", error_msg)
            result_data["error"] = error_msg
            
        llm_facing_response = json.dumps(result_data)
        
        # Omit base64 image from the DB rich_response to avoid massive payload size
        saved_summary_data = result_data.copy()
        if "screenshot_base64" in saved_summary_data:
            saved_summary_data["screenshot_base64"] = "<base64_omitted_from_db>"
            
        self.emitter.emit(
            Packet(
                placement=placement,
                obj=CustomToolDelta(
                    tool_name=self.name,
                    response_type="json",
                    data=saved_summary_data,
                ),
            )
        )

        return ToolResponse(
            rich_response=CustomToolCallSummary(
                tool_name=self.name,
                response_type="json",
                tool_result=saved_summary_data,
            ),
            llm_facing_response=llm_facing_response,
        )
