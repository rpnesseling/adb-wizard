import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Device:
    serial: str
    state: str
    description: str = ""


class AdbWizardError(Exception):
    pass


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AdbWizardError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def find_adb() -> Optional[str]:
    adb = shutil.which("adb")
    if adb:
        return adb

    local = os.path.join(os.getcwd(), "platform-tools", "adb")
    if platform.system() == "Windows":
        local += ".exe"
    if os.path.exists(local):
        return local

    return None


def adb_cmd(adb_path: str, serial: Optional[str], *args: str) -> List[str]:
    cmd = [adb_path]
    if serial:
        cmd += ["-s", serial]
    cmd += list(args)
    return cmd


def list_devices(adb_path: str) -> List[Device]:
    run([adb_path, "start-server"], check=False)
    out = run([adb_path, "devices", "-l"]).stdout.strip().splitlines()

    devices: List[Device] = []
    for line in out[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        serial = parts[0]
        state = parts[1] if len(parts) > 1 else "unknown"
        desc = " ".join(parts[2:]) if len(parts) > 2 else ""
        devices.append(Device(serial=serial, state=state, description=desc))
    return devices


def pick_device(devices: List[Device]) -> Device:
    if not devices:
        raise AdbWizardError("No devices found. Plug in device, enable USB debugging, and try again.")
    if len(devices) == 1:
        return devices[0]

    print("Multiple devices detected:")
    for i, d in enumerate(devices, start=1):
        print(f"{i}) {d.serial} [{d.state}] {d.description}")

    while True:
        choice = input("Select device number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(devices):
            return devices[int(choice) - 1]
        print("Invalid choice.")


def show_basic_menu(adb_path: str, device: Device) -> None:
    serial = device.serial
    while True:
        print("\nADB Wizard")
        print(f"Device: {serial} [{device.state}]")
        print("1) Show device props")
        print("2) Install APK")
        print("3) Run shell command")
        print("4) Tail logcat (Ctrl+C to stop)")
        print("0) Exit")
        choice = input("> ").strip()

        if choice == "0":
            return
        elif choice == "1":
            model = run(adb_cmd(adb_path, serial, "shell", "getprop", "ro.product.model")).stdout.strip()
            brand = run(adb_cmd(adb_path, serial, "shell", "getprop", "ro.product.brand")).stdout.strip()
            ver = run(adb_cmd(adb_path, serial, "shell", "getprop", "ro.build.version.release")).stdout.strip()
            print(f"Brand: {brand}\nModel: {model}\nAndroid: {ver}")
        elif choice == "2":
            apk = input("Path to APK: ").strip().strip('"')
            run(adb_cmd(adb_path, serial, "install", "-r", apk))
            print("Installed.")
        elif choice == "3":
            cmd = input("shell> ").strip()
            proc = run(adb_cmd(adb_path, serial, "shell", cmd), check=False)
            print(proc.stdout)
            if proc.stderr:
                print(proc.stderr)
        elif choice == "4":
            try:
                subprocess.run(adb_cmd(adb_path, serial, "logcat"))
            except KeyboardInterrupt:
                pass
        else:
            print("Unknown option.")


def main():
    adb_path = find_adb()
    if not adb_path:
        raise AdbWizardError(
            "adb not found.\n"
            "Install platform-tools (adb) or later add an auto-downloader into ./platform-tools."
        )

    devices = list_devices(adb_path)
    device = pick_device(devices)

    if device.state == "unauthorized":
        raise AdbWizardError(
            "Device is unauthorized. Unlock phone and accept the USB debugging prompt, then try again."
        )

    show_basic_menu(adb_path, device)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
    except AdbWizardError as e:
        print(f"\nError: {e}")
