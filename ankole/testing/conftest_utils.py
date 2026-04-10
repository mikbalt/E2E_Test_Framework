"""Shared utility functions for conftest files."""

import datetime
import logging
import os
import zipfile

logger = logging.getLogger(__name__)


def get_tc_label(request):
    """Extract TC case_id from test markers for standardized naming.

    Returns 'TC-37509' if @pytest.mark.tcms(case_id=37509) is present,
    otherwise falls back to the test method name.
    """
    marker = request.node.get_closest_marker("tcms")
    if marker:
        case_id = marker.kwargs.get("case_id")
        if case_id:
            return f"TC-{case_id}"
    return request.node.name


def zip_app_logs(app_logs_dir, dest_dir, label):
    """Zip all files in app_logs_dir and return (zip_path, file_count).

    Returns (None, 0) if the directory is empty.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"AppLogs_{label}_{timestamp}.zip"
    zip_path = os.path.join(dest_dir, zip_name)

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(app_logs_dir):
            for fname in files:
                full_path = os.path.join(root, fname)
                arcname = os.path.relpath(full_path, app_logs_dir)
                zf.write(full_path, arcname)
                file_count += 1

    if file_count == 0:
        os.remove(zip_path)
        return None, 0

    return zip_path, file_count


def attach_zip_to_allure(zip_path, display_name):
    """Attach a zip file to the Allure report."""
    if not zip_path or not os.path.isfile(zip_path):
        return
    try:
        import allure
        with open(zip_path, "rb") as f:
            allure.attach(
                f.read(),
                name=display_name,
                attachment_type="application/zip",
                extension="zip",
            )
    except ImportError:
        pass
