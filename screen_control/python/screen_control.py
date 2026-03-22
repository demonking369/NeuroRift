import ctypes
import subprocess
import os
import platform
import json


class ScreenControl:
    """A multi-language, modular screen control system."""

    def __init__(self, base_path):
        self.base_path = base_path
        self._load_libraries()

    def _load_libraries(self):
        """Loads the C++, Rust, and Assembly shared libraries."""
        try:
            # C++ Library
            cpp_lib_path = os.path.join(self.base_path, "cpp/screen.so")
            if os.path.exists(cpp_lib_path):
                self.cpp_lib = ctypes.CDLL(cpp_lib_path)
                self.cpp_lib.move_mouse_cpp.argtypes = [ctypes.c_int, ctypes.c_int]
                self.cpp_lib.click_cpp.argtypes = [ctypes.c_int]
                self.cpp_available = True
            else:
                self.cpp_available = False
                print("C++ library not found, using fallback")

            # Rust Library
            rust_lib_path = os.path.join(
                self.base_path, "rust/target/release/librust_control.so"
            )
            if os.path.exists(rust_lib_path):
                self.rust_lib = ctypes.CDLL(rust_lib_path)
                self.rust_lib.type_text.argtypes = [ctypes.c_char_p]
                self.rust_lib.scroll.argtypes = [ctypes.c_int]
                self.rust_available = True
            else:
                self.rust_available = False
                print("Rust library not found, using fallback")

            # Assembly Library
            asm_lib_path = os.path.join(self.base_path, "assembly/hook.so")
            if os.path.exists(asm_lib_path):
                self.asm_lib = ctypes.CDLL(asm_lib_path)
                self.asm_lib.calculate_offset.argtypes = [ctypes.c_int, ctypes.c_int]
                self.asm_lib.calculate_offset.restype = ctypes.c_int
                self.asm_available = True
            else:
                self.asm_available = False
                print("Assembly library not found, using fallback")

        except Exception as e:
            print(f"Error loading libraries: {e}")
            self.cpp_available = False
            self.rust_available = False
            self.asm_available = False

    def move_mouse(self, x: int, y: int):
        """Move mouse to coordinates using C++ library or fallback."""
        if self.cpp_available:
            self.cpp_lib.move_mouse_cpp(x, y)
        else:
            # Fallback using xdotool
            subprocess.run(["xdotool", "mousemove", str(x), str(y)])

    def click(self, button: int = 1):
        """Click mouse button using C++ library or fallback."""
        if self.cpp_available:
            self.cpp_lib.click_cpp(button)
        else:
            # Fallback using xdotool
            subprocess.run(["xdotool", "click", str(button)])

    def type_text(self, text: str):
        """Type text using Rust library or fallback."""
        if self.rust_available:
            self.rust_lib.type_text(text.encode("utf-8"))
        else:
            # Fallback using xdotool
            subprocess.run(["xdotool", "type", text])

    def scroll(self, direction: int):
        """Scroll using Rust library or fallback."""
        if self.rust_available:
            self.rust_lib.scroll(direction)
        else:
            # Fallback using xdotool
            if direction > 0:
                subprocess.run(["xdotool", "key", "Down"])
            else:
                subprocess.run(["xdotool", "key", "Up"])

    def calculate_offset(self, base: int, offset: int) -> int:
        """Calculate offset using Assembly library or fallback."""
        if self.asm_available:
            return self.asm_lib.calculate_offset(base, offset)
        else:
            # Fallback using Python
            return base + offset

    def execute_command(self, command: dict):
        """Execute a command from the JSON schema."""
        try:
            cmd_type = command.get("type")
            if cmd_type == "move_mouse":
                self.move_mouse(command["x"], command["y"])
            elif cmd_type == "click":
                self.click(command.get("button", 1))
            elif cmd_type == "type":
                self.type_text(command["text"])
            elif cmd_type == "scroll":
                self.scroll(command["direction"])
            elif cmd_type == "wait":
                import time

                time.sleep(command["seconds"])
            else:
                print(f"Unknown command type: {cmd_type}")
        except Exception as e:
            print(f"Error executing command: {e}")

    def run_sequence(self, commands: list):
        """Run a sequence of commands."""
        for command in commands:
            self.execute_command(command)
            # Small delay between commands
            import time

            time.sleep(0.1)
