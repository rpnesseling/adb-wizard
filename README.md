# adb-wizard

Feature-rich interactive Python CLI for Android Debug Bridge (ADB) workflows across device/session management, app/package tasks, file transfer, diagnostics, and automation.

## Features

### Device and session
- Detects connected Android devices with `adb devices -l`
- Supports device selection and switching when multiple devices are connected
- Shows one-screen device summary (brand/model/Android/API/ABI/battery/IP)
- Supports reboot actions (system, recovery, bootloader)
- Supports Wi-Fi adb connect/disconnect workflows

### App and package
- Installs APKs with `adb install -r`
- Installs split APK sets with `adb install-multiple -r`
- APK insight mode (reads metadata when `aapt` is available and warns on potential downgrade/signature issues)
- Supports package utilities (list/info/launch/uninstall/force-stop/clear data)

### File transfer
- Transfers files with guided `adb push` and `adb pull` prompts

### Logging and diagnostics
- Tails `logcat`, supports filtered tailing, and saves timestamped log snapshots
- Collects diagnostics bundle (`logcat` + `bugreport`)
- Exports device health report in JSON and TXT

### Utilities and runtime
- Runs arbitrary `adb shell` commands
- Includes shell command history shortcuts (`!history`, `!<index>`)
- Workflow manager for scripted action chains (create/list/run)
- Profile manager for app/package/log presets
- App dev loop mode (install + clear data + launch + filtered logcat)
- Multi-device broadcast actions (install APK or shell command across connected devices)
- Plugin hooks from `plugins/*.py`
- Port forward/reverse manager
- Screen capture tools (screenshot + screenrecord pull)
- Wireless pairing (`adb pair`)
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
  "active_profile": "",
  "dry_run": false,
  "debug_logging": false,
  "debug_log_file": "adb_wizard_debug.log"
}
```

Settings:
- `prefer_project_local_platform_tools`: Prefer `./platform-tools/adb` over global `adb` on `PATH` when both exist.
- `remember_last_device`: Reuse last selected device automatically when multiple are connected.
- `last_device_serial`: Stored serial used when `remember_last_device` is enabled.
- `active_profile`: Profile name to prefill app dev loop defaults.
- `dry_run`: Print commands without executing them.
- `debug_logging`: Write command-level debug logs to file.
- `debug_log_file`: Debug log output path.

On startup, the tool prints which `adb` is being used (path + source label: project-local or global `PATH`).

## ADB Workflows

Workflows let you define repeatable action chains and run them from:

- `ADB menu` -> `Utilities` -> `Workflow manager`

Workflow storage:
- Runtime file: `.adb_wizard_workflows.json` (local, ignored by git)
- Template: `.adb_wizard_workflows.example.json`

Supported workflow step actions:
- `install_apk` (requires `apk_path`)
- `clear_data` (requires `package`)
- `launch_app` (requires `package`, optional `activity`)
- `tail_filtered_logcat` (optional `tag`, `priority`)

Example workflow:

```json
[
  {
    "name": "sample-dev-loop",
    "steps": [
      { "action": "install_apk", "apk_path": "C:/path/to/app.apk" },
      { "action": "clear_data", "package": "com.example.app" },
      { "action": "launch_app", "package": "com.example.app", "activity": ".MainActivity" },
      { "action": "tail_filtered_logcat", "tag": "ExampleTag", "priority": "I" }
    ]
  }
]
```

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
1. Device and session  
   Submenu: show summary, switch device, reboot, connect/disconnect Wi-Fi (with confirmations for connect/disconnect)
2. App and package  
   Submenu: install APK, install split APKs, APK insight, list/info/launch package, uninstall/force-stop/clear data (with confirmations for destructive actions)
3. File transfer  
   Submenu: push/pull files
4. Logging and diagnostics  
   Submenu: tail logcat, save snapshot, filtered tail, collect bundle (`logcat` + `bugreport`, with confirmation), health report export
5. Utilities  
   Submenu: shell command, workflow manager, profile manager, app dev loop mode, plugin actions, multi-device broadcast
6. Advanced  
   Submenu: port forward/reverse manager, screen capture tools, wireless pairing
0. Exit

## Example Session

```text
ADB Wizard
Device: R58M123456A [device]
1) Device and session
2) App and package
3) File transfer
4) Logging and diagnostics
5) Utilities
6) Advanced
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
- `adbw/advanced.py`: workflows, profiles, dev loop, diagnostics export, pairing, broadcast, plugins.
- `adbw/menus.py`: interactive submenus and user prompts.
- `adbw/ui_strings.py`: centralized menu/UI text constants.
- `adbw/errors.py`: app-specific exception type.
- `plugins/example_plugin.py`: minimal plugin action example.

## Testing

Run the lightweight unit test scaffold:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

## Build Binaries

Build locally with PyInstaller:

- Windows:

```powershell
.\scripts\build.ps1
```

- Linux/macOS:

```bash
./scripts/build.sh
```

Output binaries:
- Windows: `dist/adb-wizard.exe`
- Linux/macOS: `dist/adb-wizard`

Automated multi-OS builds are configured in `.github/workflows/build.yml`:
- Builds on `windows-latest`, `ubuntu-latest`, and `macos-latest`
- Uploads build artifacts for each OS
- On tags like `v1.0.0`, creates a GitHub Release and attaches all artifacts

## Releases

Expected release assets:
- `adb-wizard-windows.exe`
- `adb-wizard-linux`
- `adb-wizard-macos`
- `SHA256SUMS.txt`

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
