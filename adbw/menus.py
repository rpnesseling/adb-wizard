import os
from typing import Callable, Dict, List, Optional

from .actions import (
    collect_bugreport_bundle,
    connect_over_wifi,
    disconnect_wifi,
    install_split_apks,
    launch_app,
    list_packages,
    save_logcat_snapshot,
    show_package_info,
    tail_filtered_logcat,
)
from .adb import adb_cmd, ensure_adb, run, run_streaming
from .config import SETTINGS_FILE, Settings, save_settings
from .devices import Device, list_devices, pick_device, show_device_summary
from .ui_strings import ADB_MENU_LINES, PLATFORM_TOOLS_MENU_LINES


def confirm(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def _print_menu(lines: List[str]) -> None:
    for line in lines:
        print(line)


def _non_empty_input(prompt: str) -> str:
    return input(prompt).strip().strip('"')


def _handle_shell_command(adb_path: str, serial: str, shell_history: List[str]) -> None:
    cmd = input("shell> ").strip()
    if cmd == "!history":
        if not shell_history:
            print("No shell command history.")
        else:
            for i, item in enumerate(shell_history, start=1):
                print(f"{i}) {item}")
        return
    if cmd.startswith("!"):
        idx = cmd[1:]
        if idx.isdigit() and 1 <= int(idx) <= len(shell_history):
            cmd = shell_history[int(idx) - 1]
            print(f"shell> {cmd}")
        else:
            print("Invalid history index.")
            return
    if not cmd:
        print("Shell command is required.")
        return
    shell_history.append(cmd)
    proc = run(adb_cmd(adb_path, serial, "shell", cmd), check=False)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)


def _handle_install_apk(adb_path: str, serial: str) -> None:
    apk = _non_empty_input("Path to APK: ")
    if not apk:
        print("APK path is required.")
        return
    if not os.path.exists(apk):
        print(f"APK path does not exist: {apk}")
        return
    run(adb_cmd(adb_path, serial, "install", "-r", apk))
    print("Installed.")


def _handle_push(adb_path: str, serial: str) -> None:
    src = _non_empty_input("Local source path: ")
    if not src:
        print("Source path is required.")
        return
    if not os.path.exists(src):
        print(f"Local source path does not exist: {src}")
        return
    dst = _non_empty_input("Device destination path: ")
    if not dst:
        print("Destination path is required.")
        return
    run(adb_cmd(adb_path, serial, "push", src, dst))
    print("Push complete.")


def _handle_pull(adb_path: str, serial: str) -> None:
    src = _non_empty_input("Device source path: ")
    if not src:
        print("Source path is required.")
        return
    dst = _non_empty_input("Local destination path (default: current directory): ") or "."
    run(adb_cmd(adb_path, serial, "pull", src, dst))
    print("Pull complete.")


def _handle_package_action(adb_path: str, serial: str, prompt: str, command: List[str], success: str) -> None:
    package = input(prompt).strip()
    if not package:
        print("Package name is required.")
        return
    if not confirm(command[0].format(package=package)):
        return
    run(adb_cmd(adb_path, serial, *command[1:], package))
    print(success)


def _handle_reboot_menu(adb_path: str, serial: str) -> None:
    print("1) Reboot system")
    print("2) Reboot recovery")
    print("3) Reboot bootloader")
    reboot_choice = input("> ").strip()
    if reboot_choice == "1":
        if confirm("Reboot device to system now?"):
            run(adb_cmd(adb_path, serial, "reboot"))
    elif reboot_choice == "2":
        if confirm("Reboot device to recovery now?"):
            run(adb_cmd(adb_path, serial, "reboot", "recovery"))
    elif reboot_choice == "3":
        if confirm("Reboot device to bootloader now?"):
            run(adb_cmd(adb_path, serial, "reboot", "bootloader"))
    else:
        print("Unknown option.")


def show_basic_menu(adb_path: str, device: Device, settings: Settings) -> Device:
    shell_history: List[str] = []

    def refresh_device(new_device: Device) -> Device:
        if settings.remember_last_device:
            settings.last_device_serial = new_device.serial
            save_settings(settings)
        return new_device

    def switch_device() -> Optional[Device]:
        devices = list_devices(adb_path)
        new_device = pick_device(devices)
        if new_device.state == "unauthorized":
            print("Selected device is unauthorized. Unlock and accept USB debugging, then retry.")
            return None
        return refresh_device(new_device)

    def action_show_summary() -> Optional[Device]:
        show_device_summary(adb_path, device.serial)
        return None

    def action_install_apk() -> Optional[Device]:
        _handle_install_apk(adb_path, device.serial)
        return None

    def action_install_split() -> Optional[Device]:
        install_split_apks(adb_path, device.serial)
        return None

    def action_shell() -> Optional[Device]:
        _handle_shell_command(adb_path, device.serial, shell_history)
        return None

    def action_logcat() -> Optional[Device]:
        run_streaming(adb_cmd(adb_path, device.serial, "logcat"))
        return None

    def action_save_logcat() -> Optional[Device]:
        save_logcat_snapshot(adb_path, device.serial)
        return None

    def action_filter_logcat() -> Optional[Device]:
        tail_filtered_logcat(adb_path, device.serial)
        return None

    def action_push() -> Optional[Device]:
        _handle_push(adb_path, device.serial)
        return None

    def action_pull() -> Optional[Device]:
        _handle_pull(adb_path, device.serial)
        return None

    def action_list_packages() -> Optional[Device]:
        list_packages(adb_path, device.serial)
        return None

    def action_show_package_info() -> Optional[Device]:
        show_package_info(adb_path, device.serial)
        return None

    def action_launch_app() -> Optional[Device]:
        launch_app(adb_path, device.serial)
        return None

    def action_uninstall() -> Optional[Device]:
        _handle_package_action(
            adb_path,
            device.serial,
            "Package name to uninstall: ",
            ["Uninstall {package}?", "uninstall"],
            "Uninstall command sent.",
        )
        return None

    def action_force_stop() -> Optional[Device]:
        _handle_package_action(
            adb_path,
            device.serial,
            "Package name to force-stop: ",
            ["Force-stop {package}?", "shell", "am", "force-stop"],
            "Force-stop command sent.",
        )
        return None

    def action_clear_data() -> Optional[Device]:
        _handle_package_action(
            adb_path,
            device.serial,
            "Package name to clear app data: ",
            ["Clear app data for {package}?", "shell", "pm", "clear"],
            "Clear data command sent.",
        )
        return None

    def action_reboot_menu() -> Optional[Device]:
        _handle_reboot_menu(adb_path, device.serial)
        return None

    def action_connect_wifi() -> Optional[Device]:
        connect_over_wifi(adb_path, device.serial)
        return None

    def action_disconnect_wifi() -> Optional[Device]:
        disconnect_wifi(adb_path)
        return None

    def action_collect_bundle() -> Optional[Device]:
        collect_bugreport_bundle(adb_path, device.serial)
        return None

    while True:
        print("\nADB Wizard")
        print(f"Device: {device.serial} [{device.state}]")
        _print_menu(ADB_MENU_LINES)
        choice = input("> ").strip()

        if choice == "0":
            return device

        handlers: Dict[str, Callable[[], Optional[Device]]] = {
            "1": action_show_summary,
            "2": action_install_apk,
            "3": action_install_split,
            "4": action_shell,
            "5": action_logcat,
            "6": action_save_logcat,
            "7": action_filter_logcat,
            "8": action_push,
            "9": action_pull,
            "10": action_list_packages,
            "11": action_show_package_info,
            "12": action_launch_app,
            "13": action_uninstall,
            "14": action_force_stop,
            "15": action_clear_data,
            "16": action_reboot_menu,
            "17": action_connect_wifi,
            "18": action_disconnect_wifi,
            "19": action_collect_bundle,
            "20": switch_device,
        }

        handler = handlers.get(choice)
        if handler is None:
            print("Unknown option.")
            continue
        try:
            result = handler()
        except KeyboardInterrupt:
            print()
            continue
        if isinstance(result, Device):
            device = result
            print(f"Switched to {device.serial}.")


def show_platform_tools_menu(prefer_project_local: bool) -> bool:
    while True:
        print("\nPlatform tools")
        _print_menu(PLATFORM_TOOLS_MENU_LINES)
        choice = input("> ").strip()

        if choice == "0":
            return False
        if choice == "1":
            ensure_adb(force_install=True, prefer_project_local=prefer_project_local)
            print("Project-local platform-tools installation complete (./platform-tools, not system-wide).")
            return True
        print("Unknown option.")


def show_settings_menu(settings: Settings) -> bool:
    while True:
        print("\nSettings")
        local_pref = "ON" if settings.prefer_project_local_platform_tools else "OFF"
        remember = "ON" if settings.remember_last_device else "OFF"
        dry_run = "ON" if settings.dry_run else "OFF"
        debug_log = "ON" if settings.debug_logging else "OFF"
        print(f"1) Prefer project-local platform-tools (currently: {local_pref})")
        print(f"2) Remember last selected device (currently: {remember})")
        print(f"3) Dry run mode (currently: {dry_run})")
        print(f"4) Debug logging to file (currently: {debug_log})")
        print(f"5) Clear remembered device (currently: {settings.last_device_serial or 'none'})")
        print("0) Back")
        choice = input("> ").strip()

        if choice == "0":
            return False
        if choice == "1":
            settings.prefer_project_local_platform_tools = not settings.prefer_project_local_platform_tools
            save_settings(settings)
            current = "ON" if settings.prefer_project_local_platform_tools else "OFF"
            print(f"Saved {SETTINGS_FILE}: prefer_project_local_platform_tools={current}")
            return True
        if choice == "2":
            settings.remember_last_device = not settings.remember_last_device
            if not settings.remember_last_device:
                settings.last_device_serial = ""
            save_settings(settings)
            current = "ON" if settings.remember_last_device else "OFF"
            print(f"Saved {SETTINGS_FILE}: remember_last_device={current}")
            return True
        if choice == "3":
            settings.dry_run = not settings.dry_run
            save_settings(settings)
            current = "ON" if settings.dry_run else "OFF"
            print(f"Saved {SETTINGS_FILE}: dry_run={current}")
            return True
        if choice == "4":
            settings.debug_logging = not settings.debug_logging
            save_settings(settings)
            current = "ON" if settings.debug_logging else "OFF"
            print(f"Saved {SETTINGS_FILE}: debug_logging={current}")
            return True
        if choice == "5":
            settings.last_device_serial = ""
            save_settings(settings)
            print(f"Saved {SETTINGS_FILE}: last_device_serial cleared.")
            return True
        print("Unknown option.")
