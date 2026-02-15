from dataclasses import dataclass
from typing import List

from .adb import adb_cmd, run
from .errors import AdbWizardError


@dataclass
class Device:
    serial: str
    state: str
    description: str = ""


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


def pick_device(devices: List[Device], preferred_serial: str = "") -> Device:
    if not devices:
        raise AdbWizardError("No devices found. Plug in device, enable USB debugging, and try again.")
    if len(devices) == 1:
        return devices[0]
    if preferred_serial:
        for device in devices:
            if device.serial == preferred_serial:
                print(f"Using remembered device: {device.serial}")
                return device

    print("Multiple devices detected:")
    for i, d in enumerate(devices, start=1):
        print(f"{i}) {d.serial} [{d.state}] {d.description}")

    while True:
        choice = input("Select device number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(devices):
            return devices[int(choice) - 1]
        print("Invalid choice.")


def get_device_ip(adb_path: str, serial: str) -> str:
    out = run(adb_cmd(adb_path, serial, "shell", "ip", "route"), check=False).stdout
    for line in out.splitlines():
        parts = line.strip().split()
        if "src" in parts:
            idx = parts.index("src")
            if idx + 1 < len(parts):
                return parts[idx + 1]
    return ""


def show_device_summary(adb_path: str, serial: str) -> None:
    model = run(adb_cmd(adb_path, serial, "shell", "getprop", "ro.product.model")).stdout.strip()
    brand = run(adb_cmd(adb_path, serial, "shell", "getprop", "ro.product.brand")).stdout.strip()
    android_ver = run(adb_cmd(adb_path, serial, "shell", "getprop", "ro.build.version.release")).stdout.strip()
    api_level = run(adb_cmd(adb_path, serial, "shell", "getprop", "ro.build.version.sdk")).stdout.strip()
    abi = run(adb_cmd(adb_path, serial, "shell", "getprop", "ro.product.cpu.abi")).stdout.strip()
    battery = run(adb_cmd(adb_path, serial, "shell", "dumpsys", "battery"), check=False).stdout
    level = "unknown"
    for line in battery.splitlines():
        line = line.strip()
        if line.startswith("level:"):
            level = line.split(":", 1)[1].strip()
            break
    ip = get_device_ip(adb_path, serial) or "unknown"
    print(
        f"Brand: {brand}\nModel: {model}\nAndroid: {android_ver} (API {api_level})\n"
        f"ABI: {abi}\nBattery: {level}%\nIP: {ip}"
    )


def show_preflight(adb_path: str) -> None:
    print("Running preflight checks...")
    run([adb_path, "start-server"], check=False)
    state = run([adb_path, "get-state"], check=False)
    device_count = len(list_devices(adb_path))
    if state.returncode == 0:
        print(f"Preflight: adb server OK, connected device entries: {device_count}")
    else:
        print("Preflight: adb server started, no active device selected yet.")

