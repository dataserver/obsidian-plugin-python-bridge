# Import the Python-Obsidian bridge module
# Make sure 'requests' is installed: pip install requests
import json
import sys
import traceback

from ObsidianPluginDevPythonToJS_Qwen import (
    ObsidianCommError,
    ObsidianPluginDevPythonToJS,
    define_settings,
    handle_discovery_mode,
)

# --- Define Settings (if any) & Handle Discovery ---
# Define your script settings here (empty for this example)
MY_SETTINGS = []
define_settings(MY_SETTINGS)

# This handles:
#   - --get-settings-json (exits with JSON if requested)
#   - Detects OBSIDIAN_EVENT_NAME and sets context
handle_discovery_mode()

# --- Main Script Logic ---
if __name__ == "__main__":
    try:
        # Create client instance
        obsidian = ObsidianPluginDevPythonToJS()

        # 1. Show test notification
        obsidian.show_notification(
            content="✅ Test notification: show_notification function", duration=5000
        )

        # 2. Get active note content
        note_content = obsidian.get_active_note_content(return_format="string")
        if note_content is not None:
            excerpt = (
                note_content.strip()[:50] + "..."
                if len(note_content) > 50
                else note_content
            )
            obsidian.show_notification(
                content=f"📄 Note content preview: {excerpt}", duration=5000
            )
        else:
            obsidian.show_notification(content="⚠️ No active note found.", duration=3000)

        # 3. Absolute path of active note
        absolute_path = obsidian.get_active_note_absolute_path()
        obsidian.show_notification(
            content=f"🔗 Absolute path: {absolute_path}", duration=5000
        )

        # 4. Relative path of active note
        relative_path = obsidian.get_active_note_relative_path()
        obsidian.show_notification(
            content=f"📌 Relative path: {relative_path}", duration=5000
        )

        # 5. Title of active note
        title = obsidian.get_active_note_title()
        obsidian.show_notification(content=f"📛 Title: {title}", duration=5000)

        # 6. Vault root path
        vault_path = obsidian.get_current_vault_absolute_path()
        obsidian.show_notification(
            content=f"🏠 Vault path: {vault_path}", duration=5000
        )

        # 7. Frontmatter of active note
        frontmatter = obsidian.get_active_note_frontmatter()
        fm_str = json.dumps(frontmatter, ensure_ascii=False) if frontmatter else "None"
        obsidian.show_notification(content=f"📊 Frontmatter: {fm_str}", duration=5000)

        # 8. List all note paths (relative)
        all_notes = obsidian.get_all_note_paths(absolute=False)
        obsidian.show_notification(
            content=f"📚 Found {len(all_notes)} notes in vault.", duration=3000
        )

    except ObsidianCommError as e:
        print(f"❌ Error communicating with Obsidian: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
