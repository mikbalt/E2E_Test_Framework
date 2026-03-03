"""
UI Inspector — Discover element IDs, control types, and automation IDs.

Run this BEFORE writing tests to understand your app's UI structure.
This tool shows you exactly what names/IDs to use in your tests.

Usage:
    # Inspect an app by path
    python scripts/inspect_app.py "C:\Program Files\YourApp\App.exe"

    # Inspect an already running app by window title
    python scripts/inspect_app.py --title "My App*"

    # Deep inspection (more levels)
    python scripts/inspect_app.py --title "Calculator" --depth 5

    # Save output to file
    python scripts/inspect_app.py --title "Calculator" --output controls.txt

    # Interactive mode: click to identify elements
    python scripts/inspect_app.py --title "Calculator" --interactive

    # Record mode: capture clicks as a test flow
    python scripts/inspect_app.py --title "Calculator" --record
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
        "from hsm_test_framework import tracked_step",
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
