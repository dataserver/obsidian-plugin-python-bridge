# **Obsidian Python Bridge Client Library (HTTP Version)**  
## *API Documentation for `ObsidianPluginDevPythonToJS.py`*

> **Version**: 1.0  
> **File**: `ObsidianPluginDevPythonToJS.py`  
> **Class**: `ObsidianPluginDevPythonToJS`  
> **Communication**: HTTP (via Obsidian plugin)  

This document provides a complete reference for the Python client that enables external scripts to interact with **Obsidian** through a local HTTP plugin interface.

---

## 🔧 Overview

The `ObsidianPluginDevPythonToJS` class allows Python scripts to communicate with the **Obsidian** app by sending HTTP requests to a locally running plugin. This enables automation such as reading/writing notes, modifying frontmatter, showing notifications, and reacting to events.

> ✅ **Use Case Examples**:
> - Auto-generate metadata
> - Bulk-edit YAML frontmatter
> - Create smart templates
> - Integrate with calendars, AI tools, or databases

---

## 🚀 Getting Started

### Prerequisites

- **Obsidian** installed and running
- **Obsidian Python Bridge Plugin** enabled
- Python 3.7+
- Required packages:
  ```bash
  pip install requests
  pip install PyYAML  # Optional: for frontmatter operations
  ```

### Import and Initialize

Assuming `ObsidianPluginDevPythonToJS.py` is in your script’s directory (or in `PYTHONPATH`):

```python
from ObsidianPluginDevPythonToJS import ObsidianPluginDevPythonToJS

# Connect to Obsidian (default port: 27123)
obsidian = ObsidianPluginDevPythonToJS()
```

You can customize the HTTP port:

```python
obsidian = ObsidianPluginDevPythonToJS(http_port=27124)
```

> ⚠️ The plugin runs a local server at `http://127.0.0.1:<port>/`.

---

## 📚 Core Functions

### `define_settings(settings_list: List[Dict])`
Registers configuration settings for your script (used in Obsidian UI).

#### Parameters
| Parameter       | Type             | Description |
|----------------|------------------|-------------|
| `settings_list` | `List[Dict]`     | List of setting definitions |

#### Setting Definition Schema
Each setting dictionary supports:

| Key           | Type     | Required | Description |
|---------------|----------|----------|-------------|
| `key`         | `str`    | Yes      | Unique identifier |
| `type`        | `str`    | Yes      | `"text"`, `"number"`, `"toggle"`, `"dropdown"` |
| `label`       | `str`    | Yes      | Human-readable name |
| `description` | `str`    | No       | Help text |
| `default`     | any      | No       | Default value |
| `options`     | `List[str]` | Only for `dropdown` | Choices |
| `min`, `max`, `step` | `int/float` | For `number`/`slider` | Constraints |

#### Example
```python
define_settings([
    {
        "key": "greeting",
        "type": "text",
        "label": "Greeting Message",
        "default": "Hello",
        "description": "Custom message to show"
    },
    {
        "key": "theme",
        "type": "dropdown",
        "label": "Theme Style",
        "options": ["light", "dark"],
        "default": "dark"
    }
])
```

> ⚠️ Call this **before** using `get_script_settings()`.

---

## 🧭 Main API Reference

All methods may raise:
- `ObsidianCommError`: If communication with Obsidian fails
- `ValueError`: On invalid input

---

### 🔎 Note & Vault Info

#### `get_active_note_title() → str`
Returns the title of the currently open note.

#### `get_active_note_absolute_path() → str`
Returns full filesystem path to the active note.

#### `get_active_note_relative_path() → str`
Returns vault-relative path (e.g., `folder/note.md`).

#### `get_current_vault_absolute_path() → str`
Returns the root directory of the current vault.

#### `get_vault_name() → str`
Returns the name of the current vault.

#### `get_all_note_paths(absolute: bool = False) → List[str]`
Get list of all `.md` file paths.

- `absolute=True`: Full system paths
- `False`: Relative to vault

#### `get_all_note_titles() → List[str]`
Returns list of all note titles (filename without `.md`).

#### `get_obsidian_language() → str`
Returns current UI language code (e.g., `"en"`, `"zh"`).

#### `get_theme_mode() → str`
Returns current theme: `"light"` or `"dark"`.

---

### 📄 Reading Content

#### `get_active_note_content(return_format: str = "string") → Union[str, List[str]]`
Gets content of the active note.

- `"string"` → full content as string
- `"lines"` → list of lines

#### `get_note_content(path: str) → str`
Gets content of a note by relative path.

> ❗ Path should match actual filename (including `.md` if needed).

#### `get_selected_text() → str`
Returns currently selected text in the editor.

#### `get_editor_context() → Dict[str, Any]`
Returns detailed editor context:
```python
{
  "selection": {"start": 10, "end": 25},
  "cursor": 25,
  "line": 3,
  "content": "Full line text..."
}
```

---

### ✍️ Writing & Modifying Content

#### `modify_note_content(file_path: str, content: str)`
Overwrites the content of a note at the given **absolute** path.

> ❗ Only accepts absolute paths.

#### `replace_selected_text(replacement: str)`
Replaces the currently selected text.

#### `show_notification(content: str, duration: int = 4000)`
Displays a toast notification in Obsidian.

- `duration`: Time in milliseconds (default: 4 seconds)

---

### 🗂️ File & Folder Management

#### `create_note(path: str, content: str = "")`
Creates a new note at the given vault-relative path.

> Folders are created automatically.

#### `create_folder(path: str)`
Creates a folder (and parents) at the specified path.

#### `check_path_exists(path: str) → bool`
Returns `True` if a file or folder exists.

#### `delete_path(path: str, permanently: bool = False)`
Deletes a file or folder.

- `permanently=True`: Bypasses trash

#### `rename_path(old_path: str, new_path: str)`
Renames/moves a file or folder.

> Both paths are relative to the vault root.

#### `list_folder(path: str) → Dict[str, List[str]]`
Lists contents of a folder.

Returns:
```python
{
  "files": ["file1.md", "file2.md"],
  "folders": ["subfolder"]
}
```

> Use `path=""` for vault root.

---

### 🔗 Linking & Backlinks

#### `open_note(path: str, new_leaf: bool = False)`
Opens a note in current or new pane.

- `path`: Link-style path (without `.md`)
- `new_leaf=True`: Opens in a new tab

#### `get_links(path: str, type: str = "outgoing") → List[str]`
Gets links in a note.

- `type`: `"outgoing"` (default), `"incoming"`, `"all"`

Returns list of linked note paths.

#### `get_backlinks(path: str, use_cache_if_available: bool = True, cache_mode: str = "fast") → Dict`
Returns structured backlink data:
```python
{
  "backlinks": [
    {
      "source": "source-note.md",
      "context": "This is where it was linked...",
      "highlight": "relevant phrase"
    }
  ]
}
```

- `cache_mode`: `"fast"` (default) or `"safe"` (re-parses all)

---

### 🏷️ Tags

#### `get_all_tags() → List[str]`
Returns list of all unique tags in the vault (e.g., `["work", "project/x"]`).

---

### 🎨 Theme Control

#### `set_theme_light()`, `set_theme_dark()`, `toggle_theme()`
Switch Obsidian’s appearance.

---

### ⚙️ Frontmatter Management *(Requires PyYAML)*

> Install: `pip install PyYAML`

These methods safely read and modify YAML frontmatter.

#### `get_active_note_frontmatter() → Optional[Dict]`
Returns frontmatter of the active note.

#### `get_note_frontmatter(path: str) → Optional[Dict]`
Returns frontmatter of a note by relative path.

#### `manage_properties_key(...) → Dict`
Add, remove, or rename a top-level key.

| Parameter             | Type     | Description |
|-----------------------|----------|-------------|
| `file_path`           | `str`    | Absolute path to `.md` file |
| `action`              | `str`    | `"add"`, `"remove"`, `"rename"` |
| `key`                 | `str`    | Existing key |
| `new_key`             | `str`    | Required only for `rename` |
| `use_vault_modify`    | `bool`   | If `True`, uses Obsidian API; else direct file write |

> ❗ Only modifies top-level keys.

#### `manage_properties_value(...) → Dict`
Modify a frontmatter value.

| Parameter             | Type     | Description |
|-----------------------|----------|-------------|
| `file_path`           | `str`    | Absolute path |
| `key`                 | `str`    | Key to update |
| `action`              | `str`    | `"add"`, `"remove"`, `"update"` |
| `value`               | `Any`    | Value to add/remove |
| `new_value`           | `Any`    | New value (for `update`) |
| `index`               | `int`    | Index in list (optional) |
| `use_vault_modify`    | `bool`   | Use Obsidian API? |

##### Behavior by Type
- **Scalar (string/number)**: Direct assignment on `update`
- **List**:
  - `add`: Append one or more items
  - `remove`: Remove specific values
  - `update`: Replace by index or by matching value

---

### 🎯 Commands & Events

#### `run_obsidian_command(command_id: str)`
Executes a registered Obsidian command by its ID.

> Find IDs in Obsidian Settings → Commands.

#### `register_event_listener(event_name: str)`
Registers your script to listen for a specific event (e.g., `file-open`, `vault-open`).

> Script must be launched via Obsidian to receive events.

#### `unregister_event_listener(event_name: str)`
Unregisters from an event.

---

## 📡 Event Handling

When triggered by an event in Obsidian (like a button click or file save), environment variables are set:

- `OBSIDIAN_EVENT_NAME`: Name of the event
- `OBSIDIAN_EVENT_PAYLOAD`: JSON string with data

Check at runtime:

```python
from ObsidianPluginDevPythonToJS import _is_handling_event, _event_name, _event_payload

if _is_handling_event:
    print("Event:", _event_name)
    print("Payload:", _event_payload)
```

> These are **module-level globals** set at import time.

---

## 🛠️ Utility Methods

### `get_script_settings() → Dict[str, Any]`
Returns user-defined settings configured via `define_settings()`.

> ❗ Only works if script is launched through Obsidian.

### `request_user_input(...) → Any`
Prompts the user with a modal.

| Parameter         | Description |
|-------------------|-----------|
| `script_name`     | Display name |
| `input_type`      | `"text"`, `"number"`, `"toggle"`, `"dropdown"` |
| `message`         | Prompt text |
| `validationRegex` | Regex to validate text input |
| `minValue`, `maxValue`, `step` | For number inputs |

Returns the user's input.

---

## 🧱 Exceptions

### `ObsidianCommError`
Raised when:
- Obsidian is not running
- Plugin is disabled
- Request times out
- Invalid response

Includes:
- `.action`: Failed action name
- `.status_code`: HTTP status (if available)

---

## 🧪 Example: Add Tag to Current Note

```python
# my_script.py

from ObsidianPluginDevPythonToJS import ObsidianPluginDevPythonToJS, define_settings

# Define settings
define_settings([
    {
        "key": "tag",
        "type": "text",
        "label": "Tag to Add",
        "default": "#todo"
    }
])

obsidian = ObsidianPluginDevPythonToJS()

# Get current note
path = obsidian.get_active_note_absolute_path()
title = obsidian.get_active_note_title()

# Add tag if not present
content = obsidian.get_active_note_content()
tag = obsidian.get_script_settings().get("tag", "#todo")

if tag not in content:
    obsidian.modify_note_content(path, content + f"\n\n{tag}")
    obsidian.show_notification(f"Tag '{tag}' added to '{title}'")
else:
    obsidian.show_notification(f"Note already has '{tag}'")
```

---

## 📎 Environment Variables

| Variable                        | Purpose |
|-------------------------------|--------|
| `OBSIDIAN_HTTP_PORT`          | Override default port (27123) |
| `OBSIDIAN_EVENT_NAME`         | Current event name |
| `OBSIDIAN_EVENT_PAYLOAD`      | JSON payload for event |
| `OBSIDIAN_SCRIPT_RELATIVE_PATH` | Path to script (for settings) |
| `OBSIDIAN_BRIDGE_MODE`        | Internal mode (e.g., `"discovery"`) |

---

## 📦 Requirements

| Dependency   | Purpose |
|------------|--------|
| `requests` | HTTP communication |
| `PyYAML`   | Optional: frontmatter editing |

Install:
```bash
pip install requests pyyaml
```

---

## 📚 License & Attribution

This library is designed to work with the **Obsidian Python Bridge Plugin**. It is not affiliated with the Obsidian team.

> Please respect Obsidian’s [Terms of Service](https://obsidian.md/terms).

---

## 🆘 Support & Feedback

For bug reports or feature requests:
- Check the plugin’s documentation or GitHub repository
- Ensure the plugin is running and port is correct
- Enable debug logging if available

---

✅ **You're now ready to automate your Obsidian vault with `ObsidianPluginDevPythonToJS.py`!**  
📁 Place the script in your project and start building powerful workflows.
