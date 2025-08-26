# 📘 **Obsidian Python Bridge API Documentation**

> **Library**: `ObsidianPluginDevPythonToJS.py`  
> **Version**: 1.0 (HTTP-based)  
> **Purpose**: Enables Python scripts to interact with the Obsidian note-taking app via an HTTP plugin bridge.  
> **Communication**: Uses local HTTP server (default port `27123`) to send/receive JSON commands.

---

## 🔧 Prerequisites

Before using this library, ensure:

```bash
pip install requests          # Required
pip install PyYAML            # Optional: for frontmatter editing
```

Also make sure:
- The **Obsidian HTTP plugin** is installed and enabled.
- Obsidian is running.
- Your script is executed **from within Obsidian** (e.g., via command or event trigger).

---

## 📦 Module Structure

| Component | Description |
|--------|-----------|
| `ObsidianPluginDevPythonToJS` | Main client class for interacting with Obsidian |
| `define_settings()` | Define user-configurable settings for your script |
| `handle_discovery_mode()` | Handle `--get-settings-json` CLI flag (required at startup) |
| `ObsidianCommError` | Exception raised on communication or API errors |

---

## 🚀 Quick Start Example

```python
from ObsidianPluginDevPythonToJS import (
    define_settings,
    handle_discovery_mode,
    ObsidianPluginDevPythonToJS,
    ObsidianCommError,
)

# Step 1: Define settings (optional)
define_settings([
    { "key": "api_key", "type": "text", "label": "API Key", "default": "" },
    { "key": "enabled", "type": "toggle", "label": "Enable Feature", "default": True }
])

# Step 2: Handle discovery (MUST be called early)
handle_discovery_mode()

# Step 3: Use the client
try:
    client = ObsidianPluginDevPythonToJS()
    settings = client.get_script_settings()
    client.show_notification(settings.get("greeting", "Hi!"))
except ObsidianCommError as e:
    print(f"Error: {e}")
```

---

## 🛠️ Global Functions

### `define_settings(settings_list: List[Dict]) → None`

Registers script settings that appear in the Obsidian UI.

#### Parameters:
| Field | Type | Required | Description |
|------|------|----------|-------------|
| `key` | `str` | ✅ | Internal identifier |
| `type` | `str` | ✅ | One of: `text`, `number`, `slider`, `toggle`, `dropdown` |
| `label` | `str` | ✅ | Human-readable label |
| `description` | `str` | ❌ | Tooltip/help text |
| `default` | varies | ✅ | Default value based on type |
| `options` | `List[str]` | Only for `dropdown` | List of choices |
| `min`, `max`, `step` | `int`/`float` | For `number`/`slider` | Value constraints |

#### Example:
```python
define_settings([
    {
        "key": "delay",
        "type": "number",
        "label": "Delay (ms)",
        "description": "How long to wait before action",
        "default": 1000,
        "min": 100,
        "max": 5000,
        "step": 100
    },
    {
        "key": "theme",
        "type": "dropdown",
        "label": "Color Theme",
        "default": "dark",
        "options": ["light", "dark", "auto"]
    }
])
```

---

### `handle_discovery_mode() → None`

Handles the `--get-settings-json` argument used by Obsidian to fetch your script’s settings.

> ⚠️ **Must be called early**, before creating `ObsidianPluginDevPythonToJS()`.

If `--get-settings-json` is passed, it prints the registered settings as JSON and exits.

Also detects if the script was triggered by an **event** (e.g., file save).

---

## ❗ Exceptions

### `ObsidianCommError`

Raised when communication with Obsidian fails.

#### Attributes:
- `.action`: Name of the failed action
- `.status_code`: HTTP status code (if applicable)
- `.message`: Human-readable error message

#### Example:
```python
try:
    client.get_active_note_content()
except ObsidianCommError as e:
    print(f"Failed to get content: {e} (action: {e.action})")
```

---

## 🧰 `ObsidianPluginDevPythonToJS` Class

Main interface to control Obsidian.

### Constructor

```python
client = ObsidianPluginDevPythonToJS(
    http_port=None,           # Uses OBSIDIAN_HTTP_PORT or 27123
    connect_timeout=2.0,      # Timeout for connection (seconds)
    request_timeout=10.0      # Timeout for requests (seconds)
)
```

Automatically tests connection on init.

---

## 📚 API Reference

All methods may raise `ObsidianCommError`.

---

### 🔔 Notifications

#### `show_notification(content: str, duration: int = 4000) → None`
Displays a pop-up notification in Obsidian.

| Param | Type | Default | Description |
|------|------|--------|-------------|
| `content` | `str` | — | Message to show |
| `duration` | `int` | `4000` | Milliseconds to display (0 = persistent) |

---

### 📄 Active Note Access

#### `get_active_note_content(return_format: str = "string") → Union[str, List[str]]`
Gets content of currently open note.

| `return_format` | Returns |
|----------------|---------|
| `"string"` | Full content as single string |
| `"lines"` | List of lines (split by `\n`) |

> Returns `None` if no active note.

---

#### `get_active_note_frontmatter() → Optional[Dict[str, Any]]`
Returns parsed YAML frontmatter of active note, or `None`.

---

#### `get_selected_text() → str`
Returns currently selected text in editor. Empty string if nothing selected.

---

#### `replace_selected_text(replacement: str) → None`
Replaces selected text with new content.

---

#### `get_active_note_absolute_path() → str`
Returns full OS path to active note (e.g., `/home/user/vault/Note.md`).

---

#### `get_active_note_relative_path() → str`
Returns path relative to vault root (e.g., `Folder/Note.md`).

---

#### `get_active_note_title() → str`
Returns title of active note (filename without `.md` extension).

---

### 🗂️ Vault & File System

#### `get_current_vault_absolute_path() → str`
Returns full path to the current vault directory.

---

#### `get_vault_name() → str`
Returns the name of the current vault.

---

#### `get_all_note_paths(absolute: bool = False) → List[str]`
Returns list of all `.md` file paths.

| Param | Description |
|------|-------------|
| `absolute=False` | Relative to vault root |
| `absolute=True` | Full OS paths |

---

#### `get_all_note_titles() → List[str]`
Returns list of all note **titles** (filenames without `.md`).

---

#### `get_note_content(path: str) → str`
Gets content of any note by **relative path**.

> Throws `ValueError` if path is empty.

---

#### `get_note_frontmatter(path: str) → Optional[Dict]`
Gets frontmatter of any note by **relative path**.

---

#### `check_path_exists(path: str) → bool`
Returns `True` if file/folder exists at given vault-relative path.

---

#### `create_note(path: str, content: str = "") → None`
Creates a new note at vault-relative `path`. Folders are auto-created.

---

#### `modify_note_content(file_path: str, content: str) → None`
Overwrites content of a note by **absolute path**.

> Use `get_note_content()` + edit + `modify_note_content()` for edits.

---

#### `delete_path(path: str, permanently: bool = False) → None`
Deletes a file or folder.

| Param | Behavior |
|------|----------|
| `permanently=False` | Moves to system trash |
| `permanently=True` | Deletes permanently |

---

#### `rename_path(old_path: str, new_path: str) → None`
Renames/moves a file or folder (vault-relative paths).

---

#### `create_folder(path: str) → None`
Creates a folder at vault-relative path. Intermediate folders are created.

---

#### `list_folder(path: str) → Dict[str, List[str]]`
Lists contents of a folder.

Returns:
```python
{
  "files": ["file1.md", "file2.md"],
  "folders": ["Subfolder"]
}
```
Use `""` or `"."` for root.

---

### 🔗 Linking & Backlinks

#### `get_links(path: str, type: str = "outgoing") → List[str]`
Gets links from/to a note.

| `type` | Links Retrieved |
|-------|------------------|
| `"outgoing"` | Links **from** the note |
| `"incoming"` | Links **to** the note |
| `"all"` | Both directions |

Returns list of **link paths** (without `.md`).

---

#### `get_backlinks(path: str, use_cache_if_available: bool = True, cache_mode: str = "fast") → Dict`
Returns detailed backlink info.

Result:
```python
{
  "backlinks": [
    {
      "sourcePath": "Referrer.md",
      "context": "This is where it was mentioned...",
      "highlight": "relevant phrase"
    }
  ]
}
```

| Param | Options | Default | Description |
|------|--------|--------|-------------|
| `use_cache_if_available` | `True`/`False` | `True` | Use faster cached data |
| `cache_mode` | `"fast"`, `"safe"` | `"fast"` | How aggressively to trust cache |

---

### 🎨 UI & Theme

#### `get_theme_mode() → str`
Returns current theme: `"light"`, `"dark"`, or `"unknown"`.

---

#### `set_theme_light() → None`
Switches to light mode.

---

#### `set_theme_dark() → None`
Switches to dark mode.

---

#### `toggle_theme() → None`
Toggles between light and dark.

---

### 🌐 Editor & Navigation

#### `open_note(path: str, new_leaf: bool = False) → None`
Opens a note by **link path** (without `.md`).

| Param | Description |
|------|-------------|
| `path` | e.g., `"Folder/My Note"` |
| `new_leaf=True` | Opens in new pane/tab |

---

#### `get_editor_context() → Dict[str, Any]`
Returns detailed editor state:

```python
{
  "selection": {"from": 10, "to": 25},
  "cursor": 25,
  "lineCount": 100,
  "wordCount": 542
}
```

Useful for advanced editing logic.

---

### ⚙️ Commands & Automation

#### `run_obsidian_command(command_id: str) → None`
Executes a built-in or plugin command by ID.

> Find command IDs in Obsidian settings → Keyboard shortcuts.

Example:
```python
client.run_obsidian_command("editor:toggle-bold")
```

---

#### `request_user_input(...) → Any`
Prompts user with a modal input.

##### Parameters:
| Field | Type | Required | Description |
|------|------|----------|-------------|
| `script_name` | `str` | ✅ | Name shown in modal |
| `input_type` | `str` | ✅ | One of: `text`, `number`, `slider`, `confirm`, `dropdown` |
| `message` | `str` | ✅ | Prompt message |
| `validationRegex` | `str` | ❌ | Regex to validate text input |
| `minValue`, `maxValue`, `step` | numbers | For `number`/`slider` | Value bounds |
| `options` | `List[str]` | For `dropdown` | Choices |

Returns user input or `None` if canceled.

---

### 🏷️ Tags

#### `get_all_tags() → List[str]`
Returns list of all tags used in the vault (e.g., `["#work", "#project/x"]`).

---

### 🌍 Environment Info

#### `get_obsidian_language() → str`
Returns current UI language code (e.g., `"en"`, `"zh"`).

---

## 🧩 Frontmatter Management (Requires PyYAML)

> Install: `pip install PyYAML`

These methods safely edit YAML frontmatter.

---

### `manage_properties_key(...) → Dict`
Add, remove, or rename a top-level frontmatter key.

| Param | Description |
|------|-------------|
| `file_path` | Absolute path to `.md` file |
| `action` | `"add"`, `"remove"`, `"rename"` |
| `key` | Key name |
| `new_key` | Required for `"rename"` |
| `use_vault_modify` | If `True`, uses Obsidian API; else edits file directly |

Returns:
```python
{"success": True}  # or {"success": False, "error": "..."}
```

---

### `manage_properties_value(...) → Dict`
Add, remove, or update a frontmatter value.

| Param | Description |
|------|-------------|
| `value` | Value to match (for remove/update) or add |
| `new_value` | New value (for update) |
| `index` | Index in list (for list updates) |

Supports scalar and list values.

---

## 🎯 Event System (Advanced)

### `register_event_listener(event_name: str) → None`
Registers your script to be triggered when a specific event occurs.

> Your script must be run **once** to register.

Supported events depend on plugin, e.g.:
- `"file-open"`
- `"file-save"`
- `"workspace-active-leaf-change"`

After registration, the script will be re-run with:
```bash
OBSIDIAN_EVENT_NAME="file-save"
OBSIDIAN_EVENT_PAYLOAD='{"path": "Note.md"}'
```

---

### `unregister_event_listener(event_name: str) → None`
Unregisters from an event.

---

## 🧪 Troubleshooting

| Issue | Solution |
|------|----------|
| `Connection timed out` | Is Obsidian running? Is HTTP plugin enabled? |
| `Script path not set` | Run script from inside Obsidian (not CLI) |
| `PyYAML not installed` | `pip install PyYAML` for frontmatter functions |
| Settings not showing | Make sure `define_settings()` is called before `handle_discovery_mode()` |

---

## 📎 Environment Variables (Advanced)

| Variable | Default | Description |
|--------|--------|-------------|
| `OBSIDIAN_HTTP_PORT` | `27123` | Custom HTTP server port |
| `OBSIDIAN_SCRIPT_RELATIVE_PATH` | — | Set by Obsidian (e.g., `Scripts/main.py`) |
| `OBSIDIAN_EVENT_NAME` | — | Name of triggering event |
| `OBSIDIAN_EVENT_PAYLOAD` | `{}` | JSON payload from event |
| `OBSIDIAN_BRIDGE_MODE` | `"normal"` | Internal use (`"discovery"`) |

---

## 📚 Summary: Best Practices

✅ Always call `handle_discovery_mode()` early  
✅ Wrap calls in `try/except ObsidianCommError`  
✅ Use absolute paths only with `modify_note_content()`  
✅ Prefer `use_vault_modify=True` in frontmatter functions  
✅ Test event listeners carefully  
✅ Keep scripts idempotent (safe to run multiple times)

---

## 📄 License & Attribution

This library is designed to work with the **Obsidian HTTP Plugin**.  
It is not affiliated with the official Obsidian app.

Use responsibly. Avoid excessive requests or background polling.

---

✅ **You're now ready to build powerful automation for Obsidian using Python!**



