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
"""

import argparse
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def find_python_version():
    """Verify Python version."""
    if sys.version_info < (3, 9):
        logger.error(f"Python {sys.version} detected. Need 3.9+")
        sys.exit(1)


def inspect_app(app_path=None, title=None, backend="uia", depth=3,
                output_file=None, interactive=False, startup_wait=3):
    """Main inspection routine."""
    from pywinauto import Application, Desktop

    app = None
    window = None

    # Connect or start
    if app_path:
        logger.info(f"Starting: {app_path}")
        app = Application(backend=backend).start(app_path, timeout=30)
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
                    import ctypes

                    class POINT(ctypes.Structure):
                        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

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
        """,
    )
    parser.add_argument("app_path", nargs="?", help="Path to application executable")
    parser.add_argument("--title", "-t", help="Window title pattern (connect to running app)")
    parser.add_argument("--backend", "-b", default="uia", choices=["uia", "win32"],
                        help="UI backend: uia (WPF/modern) or win32 (WinForms/classic)")
    parser.add_argument("--depth", "-d", type=int, default=3, help="Control tree depth (default: 3)")
    parser.add_argument("--output", "-o", help="Save output to file")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive mode: hover over elements to identify them")
    parser.add_argument("--wait", "-w", type=int, default=3, help="Startup wait seconds (default: 3)")

    args = parser.parse_args()

    if not args.app_path and not args.title:
        parser.error("Provide either an app path or --title")

    find_python_version()
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
