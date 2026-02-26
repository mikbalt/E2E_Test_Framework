from pywinauto import Application

app = Application(backend="uia").start(r"C:\\SPHERE_HSM\\Admin Application\\AdminApp.exe")
dlg = app.top_window()
dlg.print_control_identifiers()