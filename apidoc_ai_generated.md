# 📘 **Obsidian Python Bridge Client Library (HTTP Version) – API Documentation**

This document provides a complete reference for the `ObsidianPluginDevPythonToJS` class, a Python client that enables communication between external Python scripts and the **Obsidian** note-taking application via an HTTP plugin interface.

---

## 🔧 Overview

The **Obsidian Python Bridge** allows Python scripts to interact with Obsidian in real time by sending HTTP requests to a locally running Obsidian plugin. This enables automation of tasks such as reading/writing notes, modifying frontmatter, showing notifications, and responding to events.

> ✅ **Use Case Examples**:
> - Auto-tagging notes based on content
> - Bulk-editing YAML frontmatter
> - Creating templates or workflows
> - Integrating with external tools (e.g., calendars, databases)

---

## 🚀 Getting Started

### Prerequisites

- **Obsidian** installed and running
- **Obsidian Python Bridge Plugin** enabled in Obsidian
- Python 3.7+
- Required packages:
  ```bash
  pip install requests
  pip install PyYAML  # Optional: for frontmatter operations
  ```

### Import and Initialize

```python
from obsidian_python_bridge import ObsidianPluginDevPythonToJS

# Connect to Obsidian (default port: 27123)
obsidian = ObsidianPluginDevPythonToJS()
```

You can customize the HTTP port if needed:

```python
obsidian = ObsidianPluginDevPythonToJS(http_port=27124)
```

---

## 📚 Core Functions

### `define_settings(settings_list: List[Dict])`
Registers configuration settings for your script (used in Obsidian UI).

#### Parameters
| Parameter       | Type             | Description |
|----------------|------------------|-------------|
| `settings_list` | `List[Dict]`     | List of setting definitions |

#### Setting Definition Schema
Each setting dictionary supports these keys:

| Key           | Type     | Required | Description |
|---------------|----------|----------|-------------|
| `key`         | `str`    | Yes      | Unique identifier |
| `type`        | `str`    | Yes      | `"text"`, `"number"`, `"toggle"`, `"dropdown"` |
| `label`       | `str`    | Yes      | Human-readable name |
| `description` | `str`    | No       | Help text |
| `default`     | any      | No       | Default value |
| `options`     | `List[str]` | Only for `dropdown` | List of choices |
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

- If `absolute=True`, returns full system paths.
- Otherwise, returns relative paths.

#### `get_all_note_titles() → List[str]`
Returns list of all note titles (filename without `.md` extension).

#### `get_obsidian_language() → str`
Returns current UI language code (e.g., `"en"`, `"zh"`).

#### `get_theme_mode() → str`
Returns current theme: `"light"` or `"dark"`.

---

### 📄 Reading Content

#### `get_active_note_content(return_format: str = "string") → Union[str, List[str]]`
Gets content of the active note.

- `return_format="string"` → entire content as a single string
- `return_format="lines"` → list of lines

#### `get_note_content(path: str) → str`
Gets content of a note by its relative path.

> ❗ Path should not include `.md` if linking; but must match actual filename.

#### `get_selected_text() → str`
Returns currently selected text in the editor.

#### `get_editor_context() → Dict[str, Any]`
Returns detailed context about the editor:
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
Replaces the currently selected text with `replacement`.

#### `show_notification(content: str, duration: int = 4000)`
Displays a toast notification in Obsidian.

- `duration`: Time in milliseconds (default: 4 seconds)

---

### 🗂️ File & Folder Management

#### `create_note(path: str, content: str = "")`
Creates a new note at the given vault-relative path.

> Folders are created automatically if they don’t exist.

#### `create_folder(path: str)`
Creates a folder (and parent folders) at the specified path.

#### `check_path_exists(path: str) → bool`
Returns `True` if a file or folder exists at `path`.

#### `delete_path(path: str, permanently: bool = False)`
Deletes a file or folder.

- If `permanently=True`, bypasses trash.

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
Opens a note in the current or new pane.

- `path`: Link-style path (without `.md`)
- `new_leaf=True`: Opens in a new tab/split

#### `get_links(path: str, type: str = "outgoing") → List[str]`
Gets links in a note.

- `type`: `"outgoing"` (default), `"incoming"`, or `"all"`

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

- `cache_mode`: `"fast"` (default) or `"safe"` (re-parses all files)

---

### 🏷️ Tags

#### `get_all_tags() → List[str]`
Returns list of all unique tags used in the vault (e.g., `["work", "project/x"]`).

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

When your script is triggered by an event in Obsidian (like a button click or file save), environment variables are set:

- `OBSIDIAN_EVENT_NAME`: Name of the event
- `OBSIDIAN_EVENT_PAYLOAD`: JSON string with data

You can check for events:

```python
if obsidian.is_handling_event():
    print("Event:", obsidian.event_name)
    print("Payload:", obsidian.event_payload)
```

> ⚠️ These are internal globals; access via:
> ```python
> from obsidian_python_bridge import _is_handling_event, _event_name, _event_payload
> ```

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

## 🧪 Example: Simple Note Updater

```python
from obsidian_python_bridge import ObsidianPluginDevPythonToJS, define_settings

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

# Add tag to content
content = obsidian.get_active_note_content()
if "#todo" not in content:
    obsidian.modify_note_content(path, content + f"\n\n{obsidian.get_script_settings()['tag']}")

obsidian.show_notification(f"Updated '{title}'")
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

This library is intended to work with the **Obsidian Python Bridge Plugin**. It is not affiliated with the Obsidian team.

> Please respect Obsidian’s [Terms of Service](https://obsidian.md/terms).

---

## 🆘 Support & Feedback

For bug reports or feature requests, please open an issue on the associated GitHub repository (if available), or consult the plugin documentation.

---

✅ **You're now ready to automate your Obsidian vault with Python!**
