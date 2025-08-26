# -*- coding: utf-8 -*-
"""
Obsidian Python Bridge Client Library (HTTP Version)
Provides a Python interface to interact with the Obsidian plugin via HTTP.
"""

import argparse
import json
import os
import sys
import traceback
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# --- Dependencies ---
try:
    import requests
except ImportError:
    print(
        "ERROR: Missing 'requests' library. Install with: pip install requests",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

# --- Logging Setup ---
import logging

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("obsidian_bridge")


# --- Global Context Class ---
class BridgeContext:
    """
    Encapsulates all shared state for the Obsidian bridge.
    Avoids scattered module-level globals.
    """

    def __init__(self) -> None:
        self.settings_definitions: List[Dict[str, Any]] = []
        self.is_handling_event: bool = False
        self.event_name: Optional[str] = None
        self.event_payload: Optional[Dict[str, Any]] = None
        self.http_port: int = int(os.environ.get("OBSIDIAN_HTTP_PORT", 27123))
        self.script_relative_path: Optional[str] = os.environ.get(
            "OBSIDIAN_SCRIPT_RELATIVE_PATH"
        )
        self.execution_mode: str = os.environ.get("OBSIDIAN_BRIDGE_MODE", "normal")

    def detect_event_from_env(self) -> None:
        """Detect if we're handling an Obsidian event from environment."""
        if self.is_handling_event:
            return
        name = os.environ.get("OBSIDIAN_EVENT_NAME")
        if not name:
            return
        payload_str = os.environ.get("OBSIDIAN_EVENT_PAYLOAD", "{}")
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            payload = {"error": "Invalid JSON", "raw": payload_str}
        self.event_name = name
        self.event_payload = payload
        self.is_handling_event = True


# --- Singleton Instance ---
_bridge_context = BridgeContext()


# --- Public API: Settings & Discovery ---
def define_settings(settings_list: List[Dict[str, Any]]) -> None:
    """
    Register settings definitions for the script.

    Args:
        settings_list: List of setting dicts with keys: key, type, label, description,
                       default, options (optional), min/max/step (for number/slider).
    """
    _bridge_context.settings_definitions = settings_list


def handle_discovery_mode() -> None:
    """
    Handle settings discovery (e.g. --get-settings-json).
    Must be called early in the script, before using the client.
    Exits the program if discovery flag is detected.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--get-settings-json", action="store_true")
    args, _ = parser.parse_known_args()

    if args.get_settings_json:
        _bridge_context.detect_event_from_env()
        try:
            print(json.dumps(_bridge_context.settings_definitions or []))
            sys.exit(0)
        except (TypeError, ValueError) as e:
            print(
                json.dumps({"status": "error", "error": str(e)}),
                file=sys.stderr,
            )
            sys.exit(1)

    # Always check for event after parsing args
    _bridge_context.detect_event_from_env()


# --- Exceptions ---
class ObsidianCommError(Exception):
    """Exception for HTTP communication failures with Obsidian."""

    def __init__(
        self,
        message: str,
        action: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        self.action = action
        self.status_code = status_code
        msg = f"Action '{action}': " if action else ""
        msg += f"HTTP {status_code}: " if status_code else ""
        msg += message
        super().__init__(msg)


# --- Main Client Class ---
class ObsidianPluginDevPythonToJS:
    """Client for interacting with Obsidian via HTTP."""

    __slots__ = (
        "http_port",
        "base_url",
        "connect_timeout",
        "request_timeout",
        "session",
        "script_relative_path",
    )

    def __init__(
        self,
        http_port: Optional[int] = None,
        connect_timeout: float = 2.0,
        request_timeout: float = 10.0,
    ):
        port = http_port if http_port is not None else _bridge_context.http_port
        if not (1024 <= port <= 65535):
            raise ValueError(f"Invalid port: {port}. Must be 1024–65535.")
        self.http_port = port
        self.base_url = f"http://127.0.0.1:{self.http_port}/"
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self.session = requests.Session()
        self.script_relative_path = _bridge_context.script_relative_path

        if not self.script_relative_path:
            warnings.warn(
                "Script path not set. get_script_settings() will fail.",
                category=UserWarning,
            )

        self._test_connection()

    def _test_connection(self) -> None:
        """Test connectivity to the Obsidian HTTP server."""
        try:
            resp = self.session.post(
                self.base_url,
                json={"action": "_ping", "payload": {}},
                timeout=self.connect_timeout,
            )
            # Accept 4xx/5xx as expected for unknown action
            if 400 <= resp.status_code < 600:
                return
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            raise ObsidianCommError(
                f"Connection timed out after {self.connect_timeout}s. Is Obsidian running?",
                action="_test_connection",
            ) from None
        except requests.exceptions.ConnectionError as e:
            raise ObsidianCommError(
                f"Failed to connect to {self.base_url}. Check plugin status or port.",
                action="_test_connection",
            ) from e
        except requests.exceptions.RequestException as e:
            raise ObsidianCommError(
                f"Connection test failed: {e}", action="_test_connection"
            ) from e

    def _send_receive(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Send a JSON request and return the 'data' field from a successful response."""
        if _bridge_context.execution_mode == "discovery":
            raise ObsidianCommError(
                "API calls disabled in discovery mode. Call handle_discovery_mode() first.",
                action=action,
            )

        data = {"action": action, "payload": payload or {}}
        timeout = timeout or self.request_timeout

        try:
            resp = self.session.post(self.base_url, json=data, timeout=timeout)
            resp.raise_for_status()
            result = resp.json()

            if result.get("status") == "success":
                return result.get("data")
            elif result.get("status") == "error":
                raise ObsidianCommError(
                    result.get("error", "Unknown error"),
                    action=action,
                    status_code=resp.status_code,
                )
            else:
                raise ObsidianCommError(
                    "Invalid response format",
                    action=action,
                    status_code=resp.status_code,
                )

        except requests.exceptions.Timeout:
            raise ObsidianCommError("Request timed out.", action=action) from None
        except requests.exceptions.ConnectionError as e:
            raise ObsidianCommError(f"Connection failed: {e}", action=action) from e
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            try:
                err = e.response.json().get("error", str(e))
            except Exception:
                err = e.response.text or str(e)
            raise ObsidianCommError(
                f"HTTP {status}: {err}", action=action, status_code=status
            ) from e
        except requests.exceptions.JSONDecodeError as e:
            raise ObsidianCommError(f"Invalid JSON response: {e}", action=action) from e
        except Exception as e:
            log.error(
                f"Unexpected error in _send_receive: {e}\n{traceback.format_exc()}"
            )
            raise ObsidianCommError(f"Unexpected error: {e}", action=action) from e

    # --- Public API: Core ---
    def get_script_settings(self) -> Dict[str, Any]:
        """Get current user-defined settings for this script."""
        if not self.script_relative_path:
            raise ObsidianCommError(
                "Cannot get settings: script path missing. Run via Obsidian plugin.",
                action="get_script_settings",
            )
        return (
            self._send_receive(
                "get_script_settings", {"scriptPath": self.script_relative_path}
            )
            or {}
        )

    def show_notification(self, content: str, duration: int = 4000) -> None:
        """Show a notification in Obsidian."""
        if not content:
            raise ValueError("Notification content cannot be empty.")
        self._send_receive(
            "show_notification", {"content": content, "duration": duration}
        )

    def get_active_note_content(
        self, return_format: str = "string"
    ) -> Union[str, List[str]]:
        """Get content of the active note."""
        if return_format not in ("string", "lines"):
            raise ValueError("return_format must be 'string' or 'lines'.")
        return self._send_receive(
            "get_active_note_content", {"return_format": return_format}
        )

    def get_active_note_frontmatter(self) -> Optional[Dict[str, Any]]:
        """Get frontmatter of the active note."""
        return self._send_receive("get_active_note_frontmatter")

    def modify_note_content(self, file_path: str, content: str) -> None:
        """Modify note content by absolute path."""
        if not Path(file_path).is_absolute():
            raise ValueError("file_path must be absolute.")
        self._send_receive(
            "modify_note_content", {"filePath": file_path, "content": content}
        )

    def request_user_input(
        self,
        script_name: str,
        input_type: str,
        message: str,
        validation_regex: Optional[str] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        step: Optional[Union[int, float]] = None,
        **kwargs,
    ) -> Any:
        """Prompt user for input via modal."""
        if not all([script_name, input_type, message]):
            raise ValueError("script_name, input_type, message are required.")
        payload = {
            "scriptName": script_name,
            "inputType": input_type,
            "message": message,
            **({"validationRegex": validation_regex} if validation_regex else {}),
            **({"minValue": min_value} if min_value is not None else {}),
            **({"maxValue": max_value} if max_value is not None else {}),
            **({"step": step} if step is not None else {}),
            **kwargs,
        }
        return self._send_receive("request_user_input", payload)

    def get_active_note_absolute_path(self) -> str:
        """Get absolute path of active note."""
        return self._send_receive("get_active_note_absolute_path")

    def get_active_note_relative_path(self) -> str:
        """Get relative path of active note."""
        return self._send_receive("get_active_note_relative_path")

    def get_active_note_title(self) -> str:
        """Get title of active note."""
        return self._send_receive("get_active_note_title")

    def get_current_vault_absolute_path(self) -> str:
        """Get vault root path."""
        return self._send_receive("get_current_vault_absolute_path")

    def get_all_note_paths(self, absolute: bool = False) -> List[str]:
        """Get all .md note paths."""
        return self._send_receive("get_all_note_paths", {"absolute": absolute})

    def get_all_note_titles(self) -> List[str]:
        """Get all note titles."""
        return [Path(p).stem for p in self.get_all_note_paths(False)]

    def get_note_content(self, path: str) -> str:
        """Get content of a note by relative path."""
        if not path:
            raise ValueError("Path cannot be empty.")
        return self._send_receive("get_note_content", {"path": path})

    def get_note_frontmatter(self, path: str) -> Optional[Dict[str, Any]]:
        """Get frontmatter of a note by relative path."""
        if not path:
            raise ValueError("Path cannot be empty.")
        return self._send_receive("get_note_frontmatter", {"path": path})

    def get_selected_text(self) -> str:
        """Get selected text in editor."""
        return self._send_receive("get_selected_text")

    def replace_selected_text(self, replacement: str) -> None:
        """Replace selected text."""
        self._send_receive("replace_selected_text", {"replacement": replacement})

    def open_note(self, path: str, new_leaf: bool = False) -> None:
        """Open a note by link path (without .md)."""
        if not path:
            raise ValueError("Path cannot be empty.")
        self._send_receive("open_note", {"path": path, "new_leaf": new_leaf})

    # --- Frontmatter Management (requires PyYAML) ---
    def manage_properties_key(
        self,
        file_path: str,
        action: str,
        key: Optional[str] = None,
        new_key: Optional[str] = None,
        use_vault_modify: bool = True,
    ) -> Dict[str, Any]:
        """Add, remove, or rename a top-level frontmatter key."""
        if yaml is None:
            raise ImportError("PyYAML required. Install with: pip install PyYAML")
        p = Path(file_path)
        if not p.is_file() or p.suffix != ".md":
            return {"success": False, "error": "Invalid .md file path."}
        if not p.is_absolute():
            return {"success": False, "error": "File path must be absolute."}
        if action not in ("add", "remove", "rename"):
            return {
                "success": False,
                "error": "Action must be 'add', 'remove', or 'rename'.",
            }
        if not key:
            return {"success": False, "error": "'key' is required."}
        if action == "rename" and not new_key:
            return {"success": False, "error": "'new_key' required for rename."}

        try:
            content = p.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) < 3 or parts[0].strip():
                if action == "add":
                    frontmatter, main_content = {}, content
                else:
                    return {"success": False, "error": "No frontmatter block found."}
            else:
                loaded = yaml.safe_load(parts[1]) or {}
                if not isinstance(loaded, dict):
                    return {
                        "success": False,
                        "error": "Frontmatter is not a dictionary.",
                    }
                frontmatter = loaded
                main_content = parts[2]

            original = frontmatter.copy()
            if action == "add":
                if key in frontmatter:
                    return {"success": False, "error": f"Key '{key}' already exists."}
                frontmatter[key] = None
            elif action == "remove":
                if key not in frontmatter:
                    return {"success": False, "error": f"Key '{key}' not found."}
                del frontmatter[key]
            elif action == "rename":
                if key not in frontmatter:
                    return {"success": False, "error": f"Key '{key}' not found."}
                if new_key == key:
                    return {"success": False, "error": "New key is same as old."}
                if new_key in frontmatter:
                    return {
                        "success": False,
                        "error": f"Key '{new_key}' already exists.",
                    }
                frontmatter[new_key] = frontmatter.pop(key)

            if frontmatter == original:
                return {"success": True, "message": "No changes made."}

            if not frontmatter:
                updated = main_content.lstrip()
            else:
                yaml_str = yaml.dump(
                    frontmatter,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                )
                sep = "\n" if main_content else ""
                updated = f"---\n{yaml_str.strip()}\n---{sep}{main_content}"

            if use_vault_modify:
                self.modify_note_content(str(p), updated)
            else:
                p.write_text(updated, encoding="utf-8")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def manage_properties_value(
        self,
        file_path: str,
        key: str,
        action: str,
        value: Any = None,
        new_value: Any = None,
        index: Optional[int] = None,
        use_vault_modify: bool = True,
    ) -> Dict[str, Any]:
        """Add, remove, or update a frontmatter value."""
        if yaml is None:
            raise ImportError("PyYAML required. Install with: pip install PyYAML")
        p = Path(file_path)
        if not p.is_file() or p.suffix != ".md":
            return {"success": False, "error": "Invalid .md file path."}
        if not p.is_absolute():
            return {"success": False, "error": "File path must be absolute."}
        if not key:
            return {"success": False, "error": "'key' is required."}
        if action not in ("add", "remove", "update"):
            return {"success": False, "error": "Invalid action."}

        try:
            content = p.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            frontmatter = {}
            main_content = content
            if len(parts) >= 3 and not parts[0].strip():
                loaded = yaml.safe_load(parts[1])
                if isinstance(loaded, dict):
                    frontmatter = loaded
                elif loaded is not None:
                    return {"success": False, "error": "Frontmatter is not a dict."}

            if key not in frontmatter and action != "add":
                return {"success": False, "error": f"Key '{key}' not found."}

            original = frontmatter.copy()
            val = frontmatter.get(key)

            if action == "add":
                if key not in frontmatter:
                    frontmatter[key] = value
                elif isinstance(val, list):
                    items = value if isinstance(value, list) else [value]
                    frontmatter[key].extend(items)
                elif val is None:
                    frontmatter[key] = value
                else:
                    return {
                        "success": False,
                        "error": f"Key '{key}' is not a list or null.",
                    }
            elif action == "remove":
                if isinstance(val, list):
                    items = value if isinstance(value, list) else [value]
                    new_list = [v for v in val if v not in items]
                    if len(new_list) == len(val):
                        return {"success": False, "error": "Values not found."}
                    frontmatter[key] = new_list
                elif val == value:
                    del frontmatter[key]
                else:
                    return {"success": False, "error": "Cannot remove value."}
            elif action == "update":
                if isinstance(val, list):
                    if index is not None:
                        try:
                            frontmatter[key][index] = new_value
                        except IndexError:
                            return {
                                "success": False,
                                "error": f"Index {index} out of bounds.",
                            }
                    elif value is not None:
                        try:
                            idx = val.index(value)
                            frontmatter[key][idx] = new_value
                        except ValueError:
                            return {
                                "success": False,
                                "error": f"Value '{value}' not found.",
                            }
                    else:
                        return {
                            "success": False,
                            "error": "Provide 'index' or 'value' to update list.",
                        }
                else:
                    frontmatter[key] = new_value

            if frontmatter == original:
                return {"success": True, "message": "No changes."}

            if not frontmatter:
                updated = main_content.lstrip()
            else:
                yaml_str = yaml.dump(
                    frontmatter,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                )
                sep = "\n" if main_content else ""
                updated = f"---\n{yaml_str.strip()}\n---{sep}{main_content}"

            if use_vault_modify:
                self.modify_note_content(str(p), updated)
            else:
                p.write_text(updated, encoding="utf-8")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Additional Methods ---
    def get_obsidian_language(self) -> str:
        return self._send_receive("get_obsidian_language")

    def create_note(self, path: str, content: str = "") -> None:
        if not path:
            raise ValueError("Path cannot be empty.")
        self._send_receive("create_note", {"path": path, "content": content})

    def check_path_exists(self, path: str) -> bool:
        if not path:
            raise ValueError("Path cannot be empty.")
        return self._send_receive("check_path_exists", {"path": path})

    def delete_path(self, path: str, permanently: bool = False) -> None:
        if not path:
            raise ValueError("Path cannot be empty.")
        self._send_receive("delete_path", {"path": path, "permanently": permanently})

    def rename_path(self, old_path: str, new_path: str) -> None:
        if not old_path or not new_path:
            raise ValueError("old_path and new_path cannot be empty.")
        self._send_receive("rename_path", {"old_path": old_path, "new_path": new_path})

    def run_obsidian_command(self, command_id: str) -> None:
        if not command_id:
            raise ValueError("command_id cannot be empty.")
        self._send_receive("run_obsidian_command", {"command_id": command_id})

    def get_all_tags(self) -> List[str]:
        return self._send_receive("get_all_tags")

    def get_vault_name(self) -> str:
        return self._send_receive("get_vault_name")

    def get_theme_mode(self) -> str:
        return self._send_receive("get_theme_mode")

    def set_theme_light(self) -> None:
        self._send_receive("set_theme_light")

    def set_theme_dark(self) -> None:
        self._send_receive("set_theme_dark")

    def toggle_theme(self) -> None:
        self._send_receive("toggle_theme")

    def create_folder(self, path: str) -> None:
        if not path:
            raise ValueError("Path cannot be empty.")
        self._send_receive("create_folder", {"path": path})

    def list_folder(self, path: str) -> Dict[str, List[str]]:
        if path is None:
            raise ValueError("Path cannot be None. Use '' for root.")
        return self._send_receive("list_folder", {"path": path})

    def get_links(self, path: str, type: str = "outgoing") -> List[str]:
        if not path:
            raise ValueError("Path cannot be empty.")
        if type not in ("outgoing", "incoming", "all"):
            type = "outgoing"
        return self._send_receive("get_links", {"path": path, "type": type})

    def get_editor_context(self) -> Dict[str, Any]:
        return self._send_receive("get_editor_context")

    def register_event_listener(self, event_name: str) -> None:
        if not event_name:
            raise ValueError("event_name cannot be empty.")
        if not self.script_relative_path:
            raise ObsidianCommError(
                "Script path not set.", action="register_event_listener"
            )
        self._send_receive(
            "register_event_listener",
            {"eventName": event_name, "scriptPath": self.script_relative_path},
        )

    def unregister_event_listener(self, event_name: str) -> None:
        if not event_name:
            raise ValueError("event_name cannot be empty.")
        if not self.script_relative_path:
            raise ObsidianCommError(
                "Script path not set.", action="unregister_event_listener"
            )
        self._send_receive(
            "unregister_event_listener",
            {"eventName": event_name, "scriptPath": self.script_relative_path},
        )

    def get_backlinks(
        self, path: str, use_cache_if_available: bool = True, cache_mode: str = "fast"
    ) -> Dict[str, List[Dict[str, Any]]]:
        if not path:
            raise ValueError("Path cannot be empty.")
        if cache_mode not in ("fast", "safe"):
            raise ValueError("cache_mode must be 'fast' or 'safe'.")
        return self._send_receive(
            "get_backlinks",
            {
                "path": path,
                "use_cache_if_available": use_cache_if_available,
                "cache_mode": cache_mode,
            },
        )
