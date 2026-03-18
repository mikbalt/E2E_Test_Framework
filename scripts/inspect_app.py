"""
UI Inspector & Recorder — Discover element IDs and generate test code.

Run this BEFORE writing tests to understand your app's UI structure.
Shows exactly what auto_id / name / control_type to use in driver calls.

3 Modes:
    1. Inspect (default) — Dump full control tree + summary tables
    2. Interactive (-i)   — Hover mouse over elements, see live info
    3. Record (--record)  — Click elements in the app, generates YAML + Python stub

Inspect Mode (default):
    # Launch app and inspect
    python scripts/inspect_app.py "C:\\Program Files (x86)\\IDEMIA\\PCOM32\\PCOM32.exe"

    # Inspect an already running app by window title
    python scripts/inspect_app.py --title "PCOM32*"

    # Deeper tree (default depth=3)
    python scripts/inspect_app.py --title "PCOM32*" --depth 5

    # Save output to file
    python scripts/inspect_app.py --title "PCOM32*" --output controls.txt

Interactive Mode:
    # Hover mouse over elements — prints auto_id/name/type in real-time
    python scripts/inspect_app.py --title "PCOM32*" --interactive

Record Mode:
    # Click elements in the app — generates YAML flow + Python test stub
    python scripts/inspect_app.py --title "PCOM32*" --record

    # Custom output prefix (creates my_flow.yaml + my_flow.py)
    python scripts/inspect_app.py --title "PCOM32*" --record -r my_flow

    # For Edit/ComboBox elements, you'll be prompted to enter text values.
    # Press Ctrl+C to stop recording and save files.

Output (Record Mode):
    - <prefix>.yaml  — step-by-step flow (action, auto_id, name, control_type)
    - <prefix>.py    — ready-to-use test stub with tracked_step() + driver calls

Options:
    app_path          Path to .exe (launches the app)
    --title, -t       Window title pattern (connects to running app)
    --backend, -b     uia (default, WPF/modern) or win32 (WinForms/classic)
    --depth, -d       Control tree depth, default 3
    --output, -o      Save inspect output to file
    --wait, -w        Startup wait in seconds, default 3
    --interactive, -i Hover-to-identify mode
    --record          Click-to-record mode
    -r PREFIX         Output filename prefix for record mode
"""

import argparse
import ctypes
import logging
import os
import re
import sys
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class POINT(ctypes.Structure):
    """Cursor position structure for GetCursorPos."""
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def find_python_version():
    """Verify Python version."""
    if sys.version_info < (3, 9):
        logger.error(f"Python {sys.version} detected. Need 3.9+")
        sys.exit(1)


def _connect_to_app(app_path=None, title=None, backend="uia", startup_wait=3):
    """Connect to or start a Windows application and return (app, window).

    Shared by both inspect_app() and record_flow().
    """
    from pywinauto import Application

    app = None
    window = None

    if app_path:
        # Auto-detect work_dir so the app finds its relative resources
        work_dir = os.path.dirname(os.path.abspath(app_path))
        logger.info(f"Starting: {app_path} (work_dir={work_dir})")
        app = Application(backend=backend).start(app_path, timeout=30, work_dir=work_dir)
        time.sleep(startup_wait)
        window = app.top_window()
    elif title:
        logger.info(f"Connecting to: {title}")
        app = Application(backend=backend).connect(title_re=f".*{title}.*", timeout=15)
        window = app.window(title_re=f".*{title}.*")
    else:
        logger.error("Provide either app path or --title")
        sys.exit(1)

    window.wait("visible", timeout=10)
    window_title = window.window_text()
    logger.info(f"Connected to: {window_title}")
    return app, window


# ---------------------------------------------------------------------------
# Record-mode constants and helpers
# ---------------------------------------------------------------------------

# Maps control_type -> (driver_method, needs_input_prompt)
ACTION_MAP = {
    "Button":      ("click_button",    False),
    "CheckBox":    ("click_button",    False),
    "RadioButton": ("click_button",    False),
    "MenuItem":    ("click_element",   False),
    "Hyperlink":   ("click_element",   False),
    "TreeItem":    ("click_element",   False),
    "ListItem":    ("click_element",   False),
    "Edit":        ("type_text",       True),
    "ComboBox":    ("select_combobox", True),
    "TabItem":     ("select_tab",      False),
}

VK_LBUTTON = 0x01


def _map_action(control_type):
    """Return (method_name, needs_input) for a control type."""
    return ACTION_MAP.get(control_type, ("click_element", False))


def _build_step_description(seq, action, name, ctrl_type):
    """Build a human-readable step description for tracked_step."""
    verb_map = {
        "click_button":    "Click",
        "click_element":   "Click",
        "type_text":       "Type into",
        "select_combobox": "Select from",
        "select_tab":      "Select tab",
    }
    verb = verb_map.get(action, "Interact with")
    label = name if name else ctrl_type
    suffix = f" {ctrl_type.lower()}" if verb.startswith("Click") else ""
    return f"Step {seq}: {verb} '{label}'{suffix}"


def _build_driver_call(step):
    """Build the Python driver call string for a recorded step."""
    action = step["action"]
    auto_id = step.get("auto_id", "")
    name = step.get("name", "")
    text = step.get("text", "")
    class_name = step.get("class_name", "")

    # Determine the best locator
    if auto_id:
        locator = f'auto_id="{auto_id}"'
    elif name:
        locator = f'name="{name}"'
    else:
        locator = f'class_name="{class_name}"'

    if action == "click_button":
        return f"driver.click_button({locator})"
    elif action == "type_text":
        return f'driver.type_text("{text}", {locator})'
    elif action == "select_combobox":
        return f'driver.select_combobox({locator}, value="{text}")'
    elif action == "select_tab":
        tab_name = name or auto_id or class_name
        return f'driver.select_tab("{tab_name}")'
    else:
        ctrl_type = step.get("control_type", "")
        parts = [locator]
        if ctrl_type:
            parts.append(f'control_type="{ctrl_type}"')
        return f'driver.click_element({", ".join(parts)})'


def _write_yaml(steps, app_name, recorded_ts, output_path):
    """Write recorded steps to a YAML flow file."""
    import yaml

    flow = {
        "app": app_name,
        "recorded": recorded_ts,
        "steps": [],
    }
    for s in steps:
        entry = {
            "seq": s["seq"],
            "action": s["action"],
            "auto_id": s.get("auto_id", ""),
            "name": s.get("name", ""),
            "control_type": s.get("control_type", ""),
        }
        if s.get("text"):
            entry["text"] = s["text"]
        if s.get("class_name") and not s.get("auto_id") and not s.get("name"):
            entry["class_name"] = s["class_name"]
        flow["steps"].append(entry)

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(flow, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    logger.info(f"YAML flow saved: {output_path}")


def _write_python_stub(steps, app_name, recorded_ts, yaml_filename, output_path):
    """Write a Python test stub with tracked_step() calls."""
    lines = [
        "# Auto-generated from UI Recorder",
        f"# App: {app_name} | Date: {recorded_ts}",
        f"# Flow: {yaml_filename}",
        "",
        "from sphere_e2e_test_framework import tracked_step",
        "",
        "",
        "def test_recorded_flow(self):",
        "    driver = self.driver",
        "    evidence = self.evidence",
        "",
    ]

    for s in steps:
        desc = _build_step_description(s["seq"], s["action"], s.get("name", ""), s.get("control_type", ""))
        call = _build_driver_call(s)
        warning = ""
        if not s.get("auto_id") and not s.get("name"):
            warning = "  # WARNING: no auto_id or name — using class_name fallback"
        lines.append(f'    with tracked_step(evidence, driver, "{desc}"):')
        lines.append(f"        {call}{warning}")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Python stub saved: {output_path}")


def record_flow(app_path=None, title=None, backend="uia",
                startup_wait=3, output_prefix=None):
    """Record mouse clicks on a running app and generate YAML + Python test stub."""
    from pywinauto import Desktop

    app, window = _connect_to_app(app_path, title, backend, startup_wait)
    app_name = window.window_text()
    target_pid = window.process_id()

    # Determine output filenames
    now = datetime.now()
    ts_str = now.strftime("%Y%m%d_%H%M%S")
    recorded_ts = now.strftime("%Y-%m-%d %H:%M:%S")

    if output_prefix:
        base = output_prefix
    else:
        slug = re.sub(r"[^a-z0-9]+", "_", app_name.lower()).strip("_")
        base = f"flow_{slug}_{ts_str}"

    yaml_path = f"{base}.yaml"
    py_path = f"{base}.py"

    desktop = Desktop(backend=backend)
    steps = []
    seq = 0
    prev_key = None
    prev_time = 0.0
    was_pressed = False

    header = "=" * 70
    logger.info("")
    logger.info(header)
    logger.info("RECORD MODE")
    logger.info(f"App: {app_name} (PID {target_pid})")
    logger.info("Click elements in the app to record them.")
    logger.info("Press Ctrl+C to stop and save.")
    logger.info(header)
    logger.info("")
    logger.info(f"  {'#':<5} {'Time':<10} {'Action':<17} {'Name':<25} {'AutomationId':<25} {'Extra'}")
    logger.info(f"  {'-'*5} {'-'*10} {'-'*17} {'-'*25} {'-'*25} {'-'*15}")

    try:
        while True:
            try:
                pressed = ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000
                # Rising-edge detection: only fire on transition
                if pressed and not was_pressed:
                    was_pressed = True

                    pt = POINT()
                    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))

                    try:
                        elem = desktop.from_point(pt.x, pt.y)
                    except Exception:
                        elem = None

                    if elem is None:
                        continue

                    # Console-click guard: skip clicks on our own terminal
                    try:
                        if elem.process_id() != target_pid:
                            continue
                    except Exception:
                        continue

                    # Read element properties
                    name = ""
                    try:
                        name = elem.window_text() or ""
                    except Exception:
                        pass

                    ctrl_type = ""
                    try:
                        ctrl_type = elem.element_info.control_type or ""
                    except Exception:
                        pass

                    auto_id = ""
                    try:
                        auto_id = elem.automation_id() or ""
                    except Exception:
                        pass

                    class_name = ""
                    try:
                        class_name = elem.class_name() if hasattr(elem, "class_name") else ""
                    except Exception:
                        pass

                    # Duplicate guard: same element within 500ms
                    now_t = time.time()
                    elem_key = (auto_id, name, ctrl_type)
                    if elem_key == prev_key and (now_t - prev_time) < 0.5:
                        continue
                    prev_key = elem_key
                    prev_time = now_t

                    action, needs_input = _map_action(ctrl_type)
                    text = ""

                    if needs_input:
                        if action == "type_text":
                            text = input(f"    >> Enter text for '{name or auto_id}': ")
                            if not text:
                                logger.warning("      (empty text accepted)")
                        elif action == "select_combobox":
                            text = input(f"    >> Enter value to select in '{name or auto_id}': ")
                            if not text:
                                logger.warning("      (empty value accepted)")

                    seq += 1
                    step = {
                        "seq": seq,
                        "action": action,
                        "auto_id": auto_id,
                        "name": name,
                        "control_type": ctrl_type,
                        "class_name": class_name,
                    }
                    if text:
                        step["text"] = text

                    steps.append(step)

                    # Live feedback
                    ts_display = datetime.now().strftime("%H:%M:%S")
                    extra = f'text="{text}"' if text else ""
                    logger.info(
                        f"  [{seq:<3}] {ts_display:<10} {action:<17} "
                        f'name="{name:<20}" auto_id="{auto_id:<20}" {extra}'
                    )

                elif not pressed:
                    was_pressed = False

            except Exception:
                # Element read error mid-loop — keep going
                pass

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass

    # Finalize
    logger.info("")
    logger.info(header)
    if not steps:
        logger.info("No steps recorded. No files written.")
        return

    logger.info(f"Recording complete — {len(steps)} step(s) captured.")
    yaml_filename = os.path.basename(yaml_path)
    _write_yaml(steps, app_name, recorded_ts, yaml_path)
    _write_python_stub(steps, app_name, recorded_ts, yaml_filename, py_path)
    logger.info(header)
    logger.info(f"  YAML : {yaml_path}")
    logger.info(f"  Python: {py_path}")
    logger.info(header)


def _read_combobox_items(combo, backend="uia"):
    """Extract all items from a ComboBox using multiple strategies.

    WinForms ComboBoxes in UIA backend often create a separate popup List
    window when expanded. This function tries several approaches.
    """
    items = []

    # Strategy 1: expand → search descendants for ListItem
    try:
        combo.expand()
        time.sleep(0.5)

        # 1a: Direct ListItem children
        try:
            list_items = combo.descendants(control_type="ListItem")
            items = [li.window_text() for li in list_items if li.window_text()]
        except Exception:
            pass

        # 1b: If no ListItems, look for a child List control first
        if not items:
            try:
                child_list = combo.child_window(control_type="List")
                if child_list.exists(timeout=1):
                    list_items = child_list.children(control_type="ListItem")
                    items = [li.window_text() for li in list_items if li.window_text()]
            except Exception:
                pass

        # 1c: Search Desktop for popup List window (WinForms dropdown is a top-level window)
        if not items:
            try:
                from pywinauto import Desktop
                desktop = Desktop(backend=backend)
                for win in desktop.windows():
                    try:
                        if win.element_info.control_type == "List":
                            list_items = win.children(control_type="ListItem")
                            if list_items:
                                items = [li.window_text() for li in list_items if li.window_text()]
                                break
                    except Exception:
                        continue
            except Exception:
                pass

        try:
            combo.collapse()
        except Exception:
            pass
    except Exception:
        try:
            combo.collapse()
        except Exception:
            pass

    # Strategy 2: item_texts() (win32 style)
    if not items:
        try:
            items = list(combo.item_texts())
        except Exception:
            pass

    # Strategy 3: texts() fallback
    if not items:
        try:
            raw = combo.texts()
            items = [t for t in raw if t and t.strip()]
        except Exception:
            pass

    return items


def inspect_app(app_path=None, title=None, backend="uia", depth=3,
                output_file=None, interactive=False, startup_wait=3):
    """Main inspection routine."""
    app, window = _connect_to_app(app_path, title, backend, startup_wait)
    window_title = window.window_text()
    logger.info("")

    # --- Full Control Tree ---
    header = "=" * 70
    tree_output = []
    tree_output.append(header)
    tree_output.append(f"CONTROL TREE: {window_title}")
    tree_output.append(f"Backend: {backend} | Depth: {depth}")
    tree_output.append(header)

    # Capture print_control_identifiers output
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        window.print_control_identifiers(depth=depth)
    tree_str = f.getvalue()
    tree_output.append(tree_str)

    # --- Clickable Elements Summary ---
    tree_output.append(header)
    tree_output.append("CLICKABLE ELEMENTS (buttons, menu items, links)")
    tree_output.append(header)
    tree_output.append("")
    tree_output.append(f"{'Type':<20} {'Name/Title':<30} {'AutomationId':<30} {'How to Use in Test'}")
    tree_output.append("-" * 110)

    clickable_types = ["Button", "MenuItem", "Hyperlink", "TabItem", "ListItem",
                       "TreeItem", "CheckBox", "RadioButton"]
    try:
        for ctrl_type in clickable_types:
            elements = window.descendants(control_type=ctrl_type)
            for elem in elements:
                name = elem.window_text() or "(no name)"
                auto_id = elem.automation_id() if hasattr(elem, 'automation_id') else ""
                auto_id = auto_id or "(no id)"

                # Generate test code suggestion
                if auto_id and auto_id != "(no id)":
                    suggestion = f'driver.click_button(auto_id="{auto_id}")'
                elif name and name != "(no name)":
                    suggestion = f'driver.click_button(name="{name}")'
                else:
                    suggestion = "# use click_element() with other criteria"

                tree_output.append(
                    f"{ctrl_type:<20} {name:<30} {auto_id:<30} {suggestion}"
                )
    except Exception as e:
        tree_output.append(f"  Error scanning clickable elements: {e}")

    # --- Input Fields Summary ---
    tree_output.append("")
    tree_output.append(header)
    tree_output.append("INPUT FIELDS (text boxes, dropdowns, sliders)")
    tree_output.append(header)
    tree_output.append("")
    tree_output.append(f"{'Type':<20} {'Name/Title':<30} {'AutomationId':<30} {'How to Use in Test'}")
    tree_output.append("-" * 110)

    input_types = ["Edit", "ComboBox", "Slider", "Spinner"]
    try:
        for ctrl_type in input_types:
            elements = window.descendants(control_type=ctrl_type)
            for elem in elements:
                name = elem.window_text() or "(no name)"
                auto_id = elem.automation_id() if hasattr(elem, 'automation_id') else ""
                auto_id = auto_id or "(no id)"

                if ctrl_type == "Edit":
                    if auto_id and auto_id != "(no id)":
                        suggestion = f'driver.type_text("value", auto_id="{auto_id}")'
                    else:
                        suggestion = f'driver.type_text("value", name="{name}")'
                elif ctrl_type == "ComboBox":
                    if auto_id and auto_id != "(no id)":
                        suggestion = f'driver.select_combobox(auto_id="{auto_id}", value="option")'
                    else:
                        suggestion = f'driver.select_combobox(name="{name}", value="option")'
                else:
                    suggestion = f'driver.click_element(control_type="{ctrl_type}")'

                tree_output.append(
                    f"{ctrl_type:<20} {name:<30} {auto_id:<30} {suggestion}"
                )
    except Exception as e:
        tree_output.append(f"  Error scanning input fields: {e}")

    # --- Data Elements (Lists, Tables, Dropdowns) ---
    tree_output.append("")
    tree_output.append(header)
    tree_output.append("DATA ELEMENTS (lists, tables, dropdowns)")
    tree_output.append(header)
    tree_output.append("")

    data_types = ["List", "DataGrid", "Table"]
    try:
        for ctrl_type in data_types:
            elements = window.descendants(control_type=ctrl_type)
            for elem in elements:
                name = elem.window_text() or "(no name)"
                auto_id = elem.automation_id() if hasattr(elem, 'automation_id') else ""
                auto_id_display = auto_id or "(no id)"
                locator = f'auto_id="{auto_id}"' if auto_id else f'name="{name}"'

                tree_output.append(f"  [{ctrl_type}] name=\"{name}\" auto_id=\"{auto_id_display}\"")

                # --- Headers ---
                headers = []
                try:
                    # Strategy 1: direct HeaderItem children
                    header_items = elem.children(control_type="HeaderItem")
                    # Strategy 2: Header → HeaderItem
                    if not header_items:
                        header_row = elem.child_window(control_type="Header")
                        header_items = header_row.children(control_type="HeaderItem")
                    headers = [h.window_text() for h in header_items]
                except Exception:
                    pass

                # Strategy 3: parse column names from Edit child names (WinForms DataGridView)
                # e.g. "Profile Name Row 0, Not sorted." → column = "Profile Name"
                if not headers:
                    try:
                        edits = elem.descendants(control_type="Edit")
                        col_names = set()
                        for e in edits:
                            edit_name = e.window_text() or ""
                            if " Row " in edit_name:
                                col_part = edit_name.split(" Row ")[0]
                                col_names.add(col_part)
                        if col_names:
                            headers = sorted(col_names)
                    except Exception:
                        pass

                if headers:
                    tree_output.append(f"    Headers: {headers}")

                # --- Rows ---
                rows_found = False

                # Strategy 1: DataItem or ListItem children
                for child_type in ("DataItem", "ListItem"):
                    try:
                        data_items = elem.children(control_type=child_type)
                        if data_items:
                            tree_output.append(f"    Rows ({len(data_items)}):")
                            for j, row_elem in enumerate(data_items[:10]):
                                cells = row_elem.children()
                                row_data = [c.window_text() for c in cells]
                                if not row_data:
                                    row_data = [row_elem.window_text()]
                                tree_output.append(f"      [{j}] {row_data}")
                            if len(data_items) > 10:
                                tree_output.append(f"      ... and {len(data_items) - 10} more rows")
                            rows_found = True
                            break
                    except Exception:
                        continue

                # Strategy 2: Custom children (WinForms DataGridView rows)
                if not rows_found:
                    try:
                        custom_rows = elem.children(control_type="Custom")
                        if custom_rows:
                            tree_output.append(f"    Rows ({len(custom_rows)}):")
                            for j, row_elem in enumerate(custom_rows[:10]):
                                cells = row_elem.children()
                                row_data = []
                                for c in cells:
                                    val = ""
                                    # For Edit cells, read actual value not accessibility name
                                    try:
                                        val = c.iface_value.CurrentValue
                                    except Exception:
                                        try:
                                            val = c.legacy_properties().get("Value", "")
                                        except Exception:
                                            val = c.window_text() or ""
                                    if val:
                                        row_data.append(val)
                                if not row_data:
                                    row_data = [row_elem.window_text()]
                                tree_output.append(f"      [{j}] {row_data}")
                            if len(custom_rows) > 10:
                                tree_output.append(f"      ... and {len(custom_rows) - 10} more rows")
                            rows_found = True
                    except Exception:
                        pass

                # Strategy 3: Parse Edit children by row number (WinForms DataGridView)
                # Groups "Column Row N, ..." edits into rows
                if not rows_found:
                    try:
                        import re as _re
                        edits = elem.descendants(control_type="Edit")
                        row_map = {}  # row_num -> {col_name: value}
                        for e in edits:
                            edit_name = e.window_text() or ""
                            match = _re.match(r"(.+?) Row (\d+)", edit_name)
                            if match:
                                col_name = match.group(1)
                                row_num = int(match.group(2))
                                if row_num not in row_map:
                                    row_map[row_num] = {}
                                # Read actual cell value via legacy_properties or value
                                cell_val = ""
                                try:
                                    cell_val = e.iface_value.CurrentValue
                                except Exception:
                                    try:
                                        cell_val = e.legacy_properties().get("Value", "")
                                    except Exception:
                                        pass
                                row_map[row_num][col_name] = cell_val

                        if row_map:
                            sorted_rows = sorted(row_map.keys())
                            tree_output.append(f"    Rows ({len(sorted_rows)}):")
                            for j in sorted_rows[:10]:
                                row_dict = row_map[j]
                                row_vals = [f"{k}={v}" for k, v in row_dict.items()]
                                tree_output.append(f"      [{j}] {{{', '.join(row_vals)}}}")
                            if len(sorted_rows) > 10:
                                tree_output.append(f"      ... and {len(sorted_rows) - 10} more rows")
                            rows_found = True
                    except Exception:
                        pass

                if not rows_found:
                    tree_output.append("    Rows: (empty or unable to read)")

                tree_output.append(f"    Usage: driver.get_list_items({locator})")
                if ctrl_type in ("DataGrid", "Table"):
                    tree_output.append(f"           driver.get_table_data({locator})")
                tree_output.append(f"           driver.select_list_item(\"item_text\", {locator})")
                tree_output.append("")
    except Exception as e:
        tree_output.append(f"  Error scanning data elements: {e}")

    # ComboBox items detail
    tree_output.append("")
    tree_output.append(header)
    tree_output.append("COMBOBOX / DROPDOWN DETAILS")
    tree_output.append(header)
    tree_output.append("")
    try:
        combos = window.descendants(control_type="ComboBox")
        if not combos:
            tree_output.append("  (no ComboBox elements found)")
        for elem in combos:
            name = elem.window_text() or "(no name)"
            auto_id = elem.automation_id() if hasattr(elem, 'automation_id') else ""
            auto_id_display = auto_id or "(no id)"
            locator = f'auto_id="{auto_id}"' if auto_id else f'name="{name}"'

            tree_output.append(f"  [{name}] auto_id=\"{auto_id_display}\"")

            # Try to read items via multiple strategies
            options = _read_combobox_items(elem, backend)

            if options:
                tree_output.append(f"    Options ({len(options)}):")
                for j, opt in enumerate(options[:15]):
                    tree_output.append(f"      [{j}] {opt}")
                if len(options) > 15:
                    tree_output.append(f"      ... and {len(options) - 15} more")
            else:
                tree_output.append("    Options: (empty or cannot expand)")

            selected = elem.window_text() or "(none)"
            tree_output.append(f"    Selected: {selected}")
            tree_output.append(f"    Usage: driver.select_combobox({locator}, value=\"option\")")
            tree_output.append(f"           driver.get_combobox_items({locator})")
            tree_output.append("")
    except Exception as e:
        tree_output.append(f"  Error scanning combobox elements: {e}")

    # --- Text/Status Elements ---
    tree_output.append("")
    tree_output.append(header)
    tree_output.append("TEXT / STATUS ELEMENTS (labels, status bars)")
    tree_output.append(header)
    tree_output.append("")
    tree_output.append(f"{'Type':<20} {'Text Content':<40} {'AutomationId':<30} {'How to Read in Test'}")
    tree_output.append("-" * 120)

    text_types = ["Text", "StatusBar"]
    try:
        for ctrl_type in text_types:
            elements = window.descendants(control_type=ctrl_type)
            for elem in elements:
                text = elem.window_text() or "(empty)"
                text_display = text[:37] + "..." if len(text) > 40 else text
                auto_id = elem.automation_id() if hasattr(elem, 'automation_id') else ""
                auto_id = auto_id or "(no id)"

                if auto_id and auto_id != "(no id)":
                    suggestion = f'driver.get_text(auto_id="{auto_id}")'
                else:
                    suggestion = f'driver.get_text(name="{text[:20]}")'

                tree_output.append(
                    f"{ctrl_type:<20} {text_display:<40} {auto_id:<30} {suggestion}"
                )
    except Exception as e:
        tree_output.append(f"  Error scanning text elements: {e}")

    # Print or save
    full_output = "\n".join(tree_output)
    print(full_output)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_output)
        logger.info(f"\nSaved to: {output_file}")

    # --- Interactive Mode ---
    if interactive:
        logger.info("")
        logger.info(header)
        logger.info("INTERACTIVE MODE")
        logger.info("Move your mouse over elements in the app.")
        logger.info("Press Ctrl+C to stop.")
        logger.info(header)
        logger.info("")

        try:
            from pywinauto import Desktop
            desktop = Desktop(backend=backend)
            last_info = ""

            while True:
                try:
                    pt = POINT()
                    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))

                    from pywinauto.controls.uiawrapper import UIAWrapper
                    from pywinauto import uia_element_info

                    elem = desktop.from_point(pt.x, pt.y)
                    if elem is not None:
                        name = elem.window_text() or "(no name)"
                        ctrl_type = elem.element_info.control_type or "Unknown"
                        auto_id = ""
                        try:
                            auto_id = elem.automation_id() or ""
                        except Exception:
                            pass

                        info = f"[{ctrl_type}] name=\"{name}\" auto_id=\"{auto_id}\""
                        if info != last_info:
                            logger.info(f"  >>> {info}")
                            last_info = info

                except Exception:
                    pass

                time.sleep(0.3)

        except KeyboardInterrupt:
            logger.info("\nInteractive mode stopped.")

    # Cleanup
    if app_path and app:
        logger.info("")
        response = input("Close the app? (y/n): ").strip().lower()
        if response == "y":
            try:
                window.close()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="UI Inspector — Discover element IDs for test automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/inspect_app.py "calc.exe"
  python scripts/inspect_app.py --title "Calculator"
  python scripts/inspect_app.py --title "My App*" --depth 5 --output controls.txt
  python scripts/inspect_app.py --title "Calculator" --interactive
  python scripts/inspect_app.py --title "Calculator" --record
  python scripts/inspect_app.py --title "Calculator" --record -r my_flow
        """,
    )
    parser.add_argument("app_path", nargs="?", help="Path to application executable")
    parser.add_argument("--title", "-t", help="Window title pattern (connect to running app)")
    parser.add_argument("--backend", "-b", default="uia", choices=["uia", "win32"],
                        help="UI backend: uia (WPF/modern) or win32 (WinForms/classic)")
    parser.add_argument("--depth", "-d", type=int, default=3, help="Control tree depth (default: 3)")
    parser.add_argument("--output", "-o", help="Save output to file")
    parser.add_argument("--wait", "-w", type=int, default=3, help="Startup wait seconds (default: 3)")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--interactive", "-i", action="store_true",
                            help="Interactive mode: hover over elements to identify them")
    mode_group.add_argument("--record", action="store_true",
                            help="Record mode: capture clicks as a test flow (YAML + Python)")
    parser.add_argument("--record-output", "-r", metavar="PREFIX",
                        help="Output filename prefix for --record (default: flow_<app>_<timestamp>)")

    args = parser.parse_args()

    if not args.app_path and not args.title:
        parser.error("Provide either an app path or --title")

    find_python_version()

    if args.record:
        record_flow(
            app_path=args.app_path,
            title=args.title,
            backend=args.backend,
            startup_wait=args.wait,
            output_prefix=args.record_output,
        )
    else:
        inspect_app(
            app_path=args.app_path,
            title=args.title,
            backend=args.backend,
            depth=args.depth,
            output_file=args.output,
            interactive=args.interactive,
            startup_wait=args.wait,
        )


if __name__ == "__main__":
    main()
