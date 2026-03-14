import subprocess
class CommandRunner:
    def run(self, cmd: list[str]):
        p=subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {"success": p.returncode==0, "stdout": p.stdout, "stderr": p.stderr, "exit_code": p.returncode}
