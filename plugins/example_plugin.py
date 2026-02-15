def register():
    def hello_action(adb_path, serial, run, adb_cmd):
        proc = run(adb_cmd(adb_path, serial, "shell", "echo", "hello-from-plugin"), check=False)
        if proc.stdout:
            print(proc.stdout.strip())
        if proc.stderr:
            print(proc.stderr.strip())

    return [
        {
            "name": "Echo hello on device",
            "run": hello_action,
        }
    ]

