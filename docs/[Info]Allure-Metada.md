## Allure Decorator Metadata — Best Practices

Yang kamu punya sudah cukup baik, tapi masih bisa diperkaya. Ini breakdown lengkapnya:

---

### 🔍 Decorator yang Tersedia di Allure Python

| Decorator | Fungsi | Scope |
|---|---|---|
| `@allure.epic()` | Business domain / product area | Tertinggi |
| `@allure.feature()` | Fitur spesifik dalam epic | Menengah |
| `@allure.story()` | User story / skenario | Bawah |
| `@allure.suite()` | Pengelompokan test (biasanya di class) | Struktural |
| `@allure.sub_suite()` | Sub-grup dalam suite | Struktural |
| `@allure.title()` | Nama test yang human-readable | Display |
| `@allure.description()` | Deskripsi detail test | Dokumentasi |
| `@allure.severity()` | Tingkat keparahan jika gagal | Prioritas |
| `@allure.tag()` | Label bebas untuk filter | Filtering |
| `@allure.label()` | Custom label key-value | Custom |
| `@allure.link()` | Link ke URL external | Traceability |
| `@allure.issue()` | Link ke issue tracker (Jira, dll) | Traceability |
| `@allure.testcase()` | Link ke test management (Kiwi TCMS) | Traceability |
| `@allure.id()` | ID unik test | Identification |

---

### ✅ Contoh Sangat Bagus untuk E2E Multi-Component

```python
import allure
from allure_commons.types import Severity

# ============================================================
# CLASS LEVEL — konteks besar
# ============================================================
@allure.epic("HSM Management System")          # product/domain level
@allure.feature("Key Ceremony")                # fitur utama
@allure.suite("E2E Tests")                     # grouping
@allure.sub_suite("Admin Panel - Windows UI")  # sub-group
class TestKeyCeremony:

    # ============================================================
    # METHOD LEVEL — konteks spesifik test
    # ============================================================
    @allure.story("Operator performs full key ceremony flow")
    @allure.title("[TC-001] Key Ceremony - Generate RSA 2048 with Quorum Approval")
    @allure.description("""
        Validates the complete key ceremony flow:
        - Admin initiates ceremony
        - Quorum members (3 of 5) approve
        - RSA-2048 key is generated and stored in HSM
        - Audit log is generated
    """)
    @allure.severity(Severity.CRITICAL)
    @allure.tag("e-admin", "windows", "ui", "hsm", "regression", "smoke")
    @allure.issue("https://jira.company.com/browse/HSM-142")
    @allure.testcase("https://kiwi.company.com/case/55/")
    @allure.link("https://confluence.company.com/hsm-key-ceremony", name="Docs")
    def test_key_ceremony_rsa2048_quorum_approval(self):
        with allure.step("1. Login as HSM Admin"):
            ...
        with allure.step("2. Navigate to Key Ceremony menu"):
            ...
        with allure.step("3. Select RSA-2048 and initiate ceremony"):
            ...
        with allure.step("4. Approve by 3 quorum members"):
            ...
        with allure.step("5. Verify key exists in HSM slot"):
            ...
        with allure.step("6. Verify audit log entry created"):
            ...
```

---

### 📐 Hierarki Epic → Feature → Story yang Ideal

```
Epic:    "HSM Management System"
  ├── Feature: "Key Ceremony"
  │     ├── Story: "Generate asymmetric key"
  │     ├── Story: "Generate symmetric key"
  │     └── Story: "Key backup and restore"
  ├── Feature: "User Management"
  │     ├── Story: "Add operator"
  │     └── Story: "Assign roles"
  └── Feature: "Audit & Compliance"
        └── Story: "Export audit log"
```

---

### 💡 Tips Tambahan

**Severity levels** — jangan semua `CRITICAL`:
```python
Severity.BLOCKER    # app tidak bisa jalan sama sekali
Severity.CRITICAL   # fitur utama rusak
Severity.NORMAL     # default, fitur penting
Severity.MINOR      # UI glitch, non-blocking
Severity.TRIVIAL    # kosmetik
```

**Tag yang informatif** — pisahkan berdasarkan dimensi:
```python
@allure.tag(
    "regression",   # test type
    "smoke",        # test tier  
    "hsm",          # component
    "windows",      # platform
    "ui",           # layer
    "quorum",       # feature flag
)
```

**Custom label untuk filter canggih:**
```python
@allure.label("owner", "team-security")
@allure.label("component", "key-management")
@allure.label("sprint", "sprint-42")
```

---

### Verdict

Punya kamu itu **cukup untuk basic**, tapi untuk E2E yang kompleks seperti HSM testing, minimal tambahkan:
1. `@allure.epic()` — supaya hierarki lengkap
2. `@allure.title()` — dengan ID test case eksplisit
3. `@allure.severity()` — penting untuk triage failure
4. `@allure.testcase()` — link ke Kiwi TCMS kamu
5. `@allure.issue()` — link ke bug tracker


---
# Contoh code 

```python
import allure
import pytest
from allure_commons.types import Severity


@allure.epic("Mobile Phone")
@allure.feature("Camera")
@allure.suite("E2E Tests")
@allure.sub_suite("Camera - Android")
class TestCameraFeature:

    @allure.story("User takes a photo in auto mode")
    @allure.title("[TC-CAM-001] Camera - Take Photo in Auto Mode and Save to Gallery")
    @allure.description("""
        Validates the basic photo capture flow:
        - User opens Camera app
        - Camera initializes in Auto mode
        - User taps shutter button
        - Photo is saved to Gallery
        - Thumbnail appears in preview
    """)
    @allure.severity(Severity.CRITICAL)
    @allure.tag("camera", "android", "smoke", "regression", "gallery")
    @allure.label("owner", "team-mobile")
    @allure.label("component", "camera-core")
    @allure.testcase("https://kiwi.company.com/case/101/")
    @allure.issue("https://jira.company.com/browse/MOB-88")
    @allure.link("https://confluence.company.com/camera-spec", name="Camera Spec Docs")
    def test_take_photo_auto_mode(self, camera_app):
        with allure.step("1. Launch Camera app"):
            camera_app.launch()

        with allure.step("2. Verify camera opens in Auto mode"):
            assert camera_app.current_mode == "AUTO"

        with allure.step("3. Tap shutter button"):
            camera_app.tap_shutter()

        with allure.step("4. Verify photo saved to Gallery"):
            assert camera_app.last_photo_exists_in_gallery()

        with allure.step("5. Verify thumbnail appears in preview"):
            assert camera_app.thumbnail_visible()


    @allure.story("User switches to Portrait mode and takes photo")
    @allure.title("[TC-CAM-002] Camera - Switch to Portrait Mode and Capture with Bokeh Effect")
    @allure.description("""
        Validates portrait mode capture flow:
        - User opens Camera app
        - User switches to Portrait mode
        - Bokeh/blur effect is applied on preview
        - User taps shutter button
        - Photo saved with portrait metadata
        - Photo viewable in Gallery with depth effect
    """)
    @allure.severity(Severity.NORMAL)
    @allure.tag("camera", "android", "portrait", "regression", "bokeh")
    @allure.label("owner", "team-mobile")
    @allure.label("component", "camera-portrait")
    @allure.testcase("https://kiwi.company.com/case/102/")
    @allure.issue("https://jira.company.com/browse/MOB-91")
    @allure.link("https://confluence.company.com/camera-portrait-spec", name="Portrait Mode Docs")
    def test_take_photo_portrait_mode(self, camera_app):
        with allure.step("1. Launch Camera app"):
            camera_app.launch()

        with allure.step("2. Switch to Portrait mode"):
            camera_app.switch_mode("PORTRAIT")
            assert camera_app.current_mode == "PORTRAIT"

        with allure.step("3. Verify bokeh effect visible on preview"):
            assert camera_app.bokeh_effect_active()

        with allure.step("4. Tap shutter button"):
            camera_app.tap_shutter()

        with allure.step("5. Verify photo saved with portrait metadata"):
            assert camera_app.last_photo_has_metadata("portrait")

        with allure.step("6. Open photo in Gallery and verify depth effect"):
            gallery = camera_app.open_last_photo_in_gallery()
            assert gallery.depth_effect_visible()
```

---

### Kenapa strukturnya seperti ini?

```
Epic     → "Mobile Phone"          # domain produk
Feature  → "Camera"                # fitur besar
Suite    → "E2E Tests"             # jenis pengujian
Sub-suite→ "Camera - Android"      # platform spesifik

Story    → skenario dari sudut pandang user ("User takes...")
Title    → [ID] + nama eksplisit yang searchable
```

### Perbedaan severity di 2 case ini

| Test | Severity | Alasan |
|---|---|---|
| TC-CAM-001 | `CRITICAL` | Fungsi utama kamera — kalau gagal, app tidak berguna |
| TC-CAM-002 | `NORMAL` | Fitur tambahan — gagal tidak block user sepenuhnya |

### Tag strategy yang dipakai

```
"camera"     → component
"android"    → platform
"smoke"      → hanya TC-001 karena basic flow
"regression" → keduanya masuk regression suite
"portrait"   → feature-specific tag untuk TC-002
```

### Pytest Decorators — Complete Reference Table

| Decorator | Fungsi | Parameter Penting |
|---|---|---|
| `@pytest.mark.skip` | Skip test tanpa kondisi | `reason="..."` |
| `@pytest.mark.skipif` | Skip berdasarkan kondisi | `condition=`, `reason="..."` |
| `@pytest.mark.xfail` | Test diexpect gagal (known bug) | `reason="..."`, `strict=False/True`, `raises=ExceptionType` |
| `@pytest.mark.parametrize` | Jalankan test dengan multiple input | `argnames`, `argvalues`, `ids=[...]` |
| `@pytest.mark.usefixtures` | Attach fixture tanpa inject ke parameter | `*fixture_names` |
| `@pytest.mark.timeout` | Batas waktu maksimal test berjalan | `seconds` (butuh `pytest-timeout`) |
| `@pytest.mark.flaky` | Retry otomatis jika test flaky | `reruns=3`, `reruns_delay=1` (butuh `pytest-rerunfailures`) |
| `@pytest.mark.dependency` | Test ini bergantung pada test lain | `depends=["test_name"]` (butuh `pytest-dependency`) |
| `@pytest.mark.order` | Atur urutan eksekusi test | `1`, `2`, dst (butuh `pytest-order`) |
| `@pytest.mark.slow` | Custom mark — tandai test lambat | — (custom, daftar di `pytest.ini`) |
| `@pytest.mark.smoke` | Custom mark — tandai smoke test | — (custom, daftar di `pytest.ini`) |
| `@pytest.mark.regression` | Custom mark — tandai regression test | — (custom, daftar di `pytest.ini`) |

---

### Custom Marks — Wajib Daftar di `pytest.ini`

> ⚠️ Kalau tidak didaftarkan, pytest akan warning `PytestUnknownMarkWarning`

```ini
# pytest.ini
[pytest]
markers =
    slow:       Tests that take longer than 30s to complete
    smoke:      Quick sanity check tests
    regression: Full regression suite tests
    flaky:      Tests known to be intermittently unstable
    windows:    Tests that only run on Windows platform
    android:    Tests that only run on Android device
```

---

### Contoh Tiap Decorator

```python
import sys
import pytest

# ── SKIP ─────────────────────────────────────────────────────
@pytest.mark.skip(reason="UI not yet implemented")
def test_not_ready(): ...

# ── SKIPIF ───────────────────────────────────────────────────
@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_windows_dialog(): ...

# ── XFAIL ────────────────────────────────────────────────────
@pytest.mark.xfail(reason="MOB-99 night mode broken", strict=False)
def test_night_mode(): ...

# strict=True  → jika PASS malah dianggap FAIL (unexpected pass)
# strict=False → jika PASS ditandai XPASS, tidak fail build

# ── PARAMETRIZE ──────────────────────────────────────────────
@pytest.mark.parametrize("mode,label", [
    ("AUTO",     "Auto"),
    ("PORTRAIT", "Portrait"),
], ids=["auto-mode", "portrait-mode"])   # ids = nama di report
def test_mode_switch(mode, label): ...

# ── USEFIXTURES ──────────────────────────────────────────────
@pytest.mark.usefixtures("setup_device", "reset_app_state")
def test_camera_launch(): ...

# ── TIMEOUT ──────────────────────────────────────────────────
@pytest.mark.timeout(30)   # gagal jika lebih dari 30 detik
def test_long_upload(): ...

# ── FLAKY / RERUN ────────────────────────────────────────────
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_network_dependent(): ...

# ── DEPENDENCY ───────────────────────────────────────────────
@pytest.mark.dependency(name="test_login")
def test_login(): ...

@pytest.mark.dependency(depends=["test_login"])
def test_dashboard():   # skip otomatis jika test_login gagal
    ...

# ── ORDER ────────────────────────────────────────────────────
@pytest.mark.order(1)
def test_first(): ...

@pytest.mark.order(2)
def test_second(): ...

# ── CUSTOM MARKS ─────────────────────────────────────────────
@pytest.mark.slow
@pytest.mark.regression
def test_full_backup_restore(): ...
```

---

### Jalankan Berdasarkan Mark

```bash
# Hanya smoke test
pytest -m smoke

# Regression tapi bukan slow
pytest -m "regression and not slow"

# Windows atau android
pytest -m "windows or android"

# Skip semua xfail
pytest --runxfail
```