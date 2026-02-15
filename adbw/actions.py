import os
from datetime import datetime

from .adb import adb_cmd, run, run_streaming
from .devices import get_device_ip


def install_split_apks(adb_path: str, serial: str) -> None:
    raw = input("Paths to split APK files (comma-separated): ").strip()
    paths = [p.strip().strip('"') for p in raw.split(",") if p.strip()]
    if not paths:
        print("No APK paths provided.")
        return
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        print("These paths do not exist:")
        for path in missing:
            print(f"- {path}")
        return
    run(adb_cmd(adb_path, serial, "install-multiple", "-r", *paths))
    print("Split APK install complete.")


def list_packages(adb_path: str, serial: str) -> None:
    print("1) Third-party packages only")
    print("2) All packages")
    choice = input("> ").strip()
    args = ("pm", "list", "packages", "-3") if choice == "1" else ("pm", "list", "packages")
    out = run(adb_cmd(adb_path, serial, "shell", *args)).stdout.strip()
    print(out if out else "(no packages found)")


def show_package_info(adb_path: str, serial: str) -> None:
    package = input("Package name: ").strip()
    if not package:
        print("Package name is required.")
        return
    paths = run(adb_cmd(adb_path, serial, "shell", "pm", "path", package), check=False).stdout.strip()
    details = run(adb_cmd(adb_path, serial, "shell", "dumpsys", "package", package), check=False).stdout
    version_name = ""
    version_code = ""
    for line in details.splitlines():
        line = line.strip()
        if not version_name and line.startswith("versionName="):
            version_name = line.split("=", 1)[1].strip()
        if not version_code and line.startswith("versionCode="):
            version_code = line.split("=", 1)[1].strip().split()[0]
        if version_name and version_code:
            break
    print(f"Package: {package}")
    print(f"Version name: {version_name or 'unknown'}")
    print(f"Version code: {version_code or 'unknown'}")
    print(f"Path(s):\n{paths or 'not found'}")


def launch_app(adb_path: str, serial: str) -> None:
    package = input("Package name: ").strip()
    if not package:
        print("Package name is required.")
        return
    activity = input("Activity (optional, e.g. .MainActivity): ").strip()
    if activity:
        component = f"{package}/{activity}"
        run(adb_cmd(adb_path, serial, "shell", "am", "start", "-n", component))
    else:
        run(adb_cmd(adb_path, serial, "shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"))
    print("Launch command sent.")


def save_logcat_snapshot(adb_path: str, serial: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logcat_{serial}_{timestamp}.txt"
    out = run(adb_cmd(adb_path, serial, "logcat", "-d"), check=False).stdout
    with open(filename, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Saved logcat snapshot to: {filename}")


def tail_filtered_logcat(adb_path: str, serial: str) -> None:
    tag = input("Log tag (default: *): ").strip() or "*"
    priority = input("Priority [V/D/I/W/E/F/S] (default: I): ").strip().upper() or "I"
    if priority not in ("V", "D", "I", "W", "E", "F", "S"):
        print("Invalid priority.")
        return
    try:
        run_streaming(adb_cmd(adb_path, serial, "logcat", f"{tag}:{priority}", "*:S"))
    except KeyboardInterrupt:
        pass


def collect_bugreport_bundle(adb_path: str, serial: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_dir = f"adb_bundle_{serial}_{timestamp}"
    os.makedirs(bundle_dir, exist_ok=True)
    logcat_path = os.path.join(bundle_dir, "logcat.txt")
    with open(logcat_path, "w", encoding="utf-8") as f:
        f.write(run(adb_cmd(adb_path, serial, "logcat", "-d"), check=False).stdout)
    print("Collecting bugreport (this may take a while)...")
    run(adb_cmd(adb_path, serial, "bugreport", bundle_dir), check=False)
    print(f"Saved diagnostics bundle under: {bundle_dir}")


def connect_over_wifi(adb_path: str, serial: str) -> None:
    port = input("TCP port (default 5555): ").strip() or "5555"
    run(adb_cmd(adb_path, serial, "tcpip", port))
    default_ip = get_device_ip(adb_path, serial)
    ip_prompt = f"Device IP (default {default_ip}): " if default_ip else "Device IP: "
    ip = input(ip_prompt).strip() or default_ip
    if not ip:
        print("Device IP is required.")
        return
    endpoint = f"{ip}:{port}"
    run([adb_path, "connect", endpoint], check=False)
    print(f"Connect command sent for {endpoint}")


def disconnect_wifi(adb_path: str) -> None:
    endpoint = input("Device endpoint ip:port (blank = disconnect all): ").strip()
    if endpoint:
        run([adb_path, "disconnect", endpoint], check=False)
        print(f"Disconnected {endpoint}")
    else:
        run([adb_path, "disconnect"], check=False)
        print("Disconnected all Wi-Fi adb endpoints.")

