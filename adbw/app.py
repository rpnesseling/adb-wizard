from .adb import adb_source_label, ensure_adb, set_runtime_options
from .config import load_settings, save_settings
from .devices import list_devices, pick_device, show_preflight
from .errors import AdbWizardError
from .menus import show_basic_menu, show_platform_tools_menu, show_settings_menu


def main() -> None:
    settings = load_settings()
    set_runtime_options(settings)
    prefer_project_local = settings.prefer_project_local_platform_tools

    adb_path = ensure_adb(
        force_install=False,
        prefer_project_local=prefer_project_local,
    )
    print(f"Using adb: {adb_path} [{adb_source_label(adb_path)}]")
    show_preflight(adb_path)

    while True:
        print("\nMain")
        print("1) ADB menu")
        print("2) Platform tools")
        print("3) Settings")
        print("0) Exit")
        choice = input("> ").strip()

        if choice == "0":
            return
        if choice == "1":
            devices = list_devices(adb_path)
            preferred_serial = settings.last_device_serial if settings.remember_last_device else ""
            device = pick_device(devices, preferred_serial=preferred_serial)
            if device.state == "unauthorized":
                raise AdbWizardError(
                    "Device is unauthorized. Unlock phone and accept the USB debugging prompt, then try again."
                )
            if settings.remember_last_device and settings.last_device_serial != device.serial:
                settings.last_device_serial = device.serial
                save_settings(settings)
            show_basic_menu(adb_path, device, settings)
            continue
        if choice == "2":
            if show_platform_tools_menu(prefer_project_local=prefer_project_local):
                adb_path = ensure_adb(force_install=False, prefer_project_local=prefer_project_local)
                print(f"Using adb: {adb_path} [{adb_source_label(adb_path)}]")
            continue
        if choice == "3":
            if show_settings_menu(settings):
                set_runtime_options(settings)
                prefer_project_local = settings.prefer_project_local_platform_tools
                adb_path = ensure_adb(force_install=False, prefer_project_local=prefer_project_local)
                print(f"Using adb: {adb_path} [{adb_source_label(adb_path)}]")
            continue
        print("Unknown option.")

