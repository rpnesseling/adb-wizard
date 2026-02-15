# adb-wizard

Simple interactive Python CLI for common Android Debug Bridge (ADB) tasks.

## Features

- Detects connected Android devices with `adb devices -l`
- Lets you choose a device when multiple are connected
- Shows one-screen device summary (brand/model/Android/API/ABI/battery/IP)
- Installs APKs with `adb install -r`
- Installs split APK sets with `adb install-multiple -r`
- Transfers files with guided `adb push` and `adb pull` prompts
- Runs arbitrary `adb shell` commands
- Includes shell command history shortcuts (`!history`, `!<index>`)
- Tails `logcat`, supports filtered tailing, and saves timestamped log snapshots
- Supports package utilities (list/info/launch/uninstall/force-stop/clear data)
- Supports device actions (reboot modes, Wi-Fi adb connect/disconnect, switch target device)
- Collects diagnostics bundle (`logcat` + `bugreport`)
- Auto-installs project-local Android platform-tools in `./platform-tools` when `adb` is not found
- Prints which `adb` binary is active (project-local or global `PATH`)
- Runs startup preflight checks and retries transient adb failures
- Optional dry-run mode and debug logging

## Requirements

- Python 3.9+
- Either:
  - `adb` already available on your `PATH`, or
  - internet access on first run so the tool can download project-local platform-tools to `./platform-tools`
- Android device with:
  - Developer Options enabled
  - USB Debugging enabled
  - USB debugging authorization accepted on-device

## Quick Start

```powershell
python adb_wizard.py
```

If one device is connected, it is selected automatically.  
If multiple devices are connected, choose one from the prompt.

Settings file:

`adb_wizard.py` reads `.adb_wizard_settings.json` from the project root and updates it from the Settings menu.
If the file does not exist, it is created when a setting is toggled.

```json
{
  "prefer_project_local_platform_tools": false,
  "remember_last_device": true,
  "last_device_serial": "",
  "dry_run": false,
  "debug_logging": false,
  "debug_log_file": "adb_wizard_debug.log"
}
```

Settings:
- `prefer_project_local_platform_tools`: Prefer `./platform-tools/adb` over global `adb` on `PATH` when both exist.
- `remember_last_device`: Reuse last selected device automatically when multiple are connected.
- `last_device_serial`: Stored serial used when `remember_last_device` is enabled.
- `dry_run`: Print commands without executing them.
- `debug_logging`: Write command-level debug logs to file.
- `debug_log_file`: Debug log output path.

On startup, the tool prints which `adb` is being used (path + source label: project-local or global `PATH`).

## Menu Options

Top-level menu:
1. ADB menu
2. Platform tools
3. Settings
0. Exit

Platform tools:
1. Re-download and reinstall project-local platform-tools (`./platform-tools`, not system-wide)
0. Back

Settings:
1. Toggle `prefer_project_local_platform_tools`
2. Toggle `remember_last_device`
3. Toggle `dry_run`
4. Toggle `debug_logging`
5. Clear remembered device
0. Back

ADB menu:
1. Show device summary
2. Install APK  
   Prompts for a local APK path and installs with replace (`-r`)
3. Install split APKs  
   Prompts for comma-separated APK paths and installs via `install-multiple -r`
4. Run shell command  
   Supports history via `!history` and replay via `!<index>`
5. Tail logcat  
   Streams logs until `Ctrl+C`
6. Save logcat snapshot  
   Writes `logcat -d` output to a timestamped local file
7. Tail filtered logcat  
   Uses tag/priority filter
8. Push file to device  
   Prompts for local source path and device destination path, then runs `adb push`
9. Pull file from device  
   Prompts for device source path and local destination path, then runs `adb pull`
10. List packages  
11. Show package info  
12. Launch app  
13. Uninstall package (with confirmation)  
14. Force-stop app (with confirmation)  
15. Clear app data (with confirmation)  
16. Reboot device (system/recovery/bootloader)  
17. Connect over Wi-Fi (`tcpip` + `connect`)  
18. Disconnect Wi-Fi device (`disconnect`)  
19. Collect diagnostics bundle (`logcat` + `bugreport`)  
20. Switch device  
0. Exit

## Example Session

```text
ADB Wizard
Device: R58M123456A [device]
1) Show device summary
2) Install APK
3) Install split APKs
4) Run shell command (!history, !<index>)
5) Tail logcat (Ctrl+C to stop)
6) Save logcat snapshot
7) Tail filtered logcat
8) Push file to device
9) Pull file from device
10) List packages
...
0) Exit
> 1
```

## Troubleshooting

- `adb not found`
  - Install Android platform-tools system-wide, or place `adb` in `./platform-tools/` for project-local use (not system-wide)
- `No devices found`
  - Check cable/USB mode, enable USB debugging, run `adb devices`
- `Device is unauthorized`
  - Unlock the phone and accept the USB debugging prompt
- `Command failed ...`
  - Enable `debug_logging` in Settings and inspect `adb_wizard_debug.log`
- `Interrupted. Exiting.`
  - Printed when `Ctrl+C` is used to exit the app

## Project Structure

- `adb_wizard.py`: thin entrypoint.
- `adbw/app.py`: app orchestration and root menu flow.
- `adbw/config.py`: settings schema and settings file read/write.
- `adbw/adb.py`: adb discovery/install, command execution, retries, dry-run/debug runtime behavior.
- `adbw/devices.py`: device listing/selection and device summary/preflight helpers.
- `adbw/actions.py`: task-specific adb actions (install, packages, logs, Wi-Fi, diagnostics).
- `adbw/menus.py`: interactive submenus and user prompts.
- `adbw/ui_strings.py`: centralized menu/UI text constants.
- `adbw/errors.py`: app-specific exception type.

## Testing

Run the lightweight unit test scaffold:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes and test locally
4. Open a pull request with a clear description

For bug reports, include:
- OS version
- Python version
- `adb version` output
- Steps to reproduce

## License

This project is licensed under the MIT License. See `LICENSE` for details.
