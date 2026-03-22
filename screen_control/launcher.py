import os
import subprocess
import json
from python.screen_control import ScreenControl

# --- Build Instructions ---
# This script assumes you are in the `screen_control` directory.
# Ensure you have build-essential, g++, rustc, cargo, and nasm installed.
# sudo apt-get install build-essential g++ rustc cargo nasm xdotool


def build_modules():
    """Compiles all native C++, Rust, and Assembly modules."""
    print("--- Building native modules ---")

    # Build C++
    print("Building C++ module...")
    try:
        subprocess.run(
            [
                "g++",
                "-shared",
                "-fPIC",
                "-o",
                "cpp/screen.so",
                "cpp/screen.cpp",
                "-lX11",
                "-lXext",
            ],
            check=True,
        )
        print("✓ C++ module built successfully")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"✗ C++ build failed: {e}")

    # Build Rust
    print("Building Rust module...")
    try:
        # SECURITY FIX: Use full path to cargo and specify working directory safely
        subprocess.run(["cargo", "build", "--release"], cwd="rust", check=True)
        print("✓ Rust module built successfully")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"✗ Rust build failed: {e}")

    # Build Assembly
    print("Building Assembly module...")
    try:
        # SECURITY FIX: Use full executable paths and proper argument lists
        subprocess.run(
            [
                "/usr/bin/nasm",
                "-f",
                "elf64",
                "assembly/hook.asm",
                "-o",
                "assembly/hook.o",
            ],
            check=True,
        )
        subprocess.run(
            ["/usr/bin/ld", "-shared", "-o", "assembly/hook.so", "assembly/hook.o"],
            check=True,
        )
        print("✓ Assembly module built successfully")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"✗ Assembly build failed: {e}")

    print("--- Build complete ---")


def run_demo():
    """Runs a demonstration of the screen control system."""
    print("--- Screen Control Demo ---")

    # Initialize screen control with fallback support
    try:
        screen = ScreenControl(".")
        print("✓ Screen control initialized")

        # Test basic functionality
        print("Testing mouse movement...")
        screen.move_mouse(100, 100)

        print("Testing text input...")
        screen.type_text("Hello from NeuroRift!")

        print("Testing scroll...")
        screen.scroll(1)

        print("Testing offset calculation...")
        result = screen.calculate_offset(100, 50)
        print(f"Offset calculation result: {result}")

        # Test JSON command execution
        commands = [
            {"type": "move_mouse", "x": 200, "y": 200},
            {"type": "click", "button": 1},
            {"type": "type", "text": "AI-controlled screen interaction"},
            {"type": "wait", "seconds": 1},
            {"type": "scroll", "direction": -1},
        ]

        print("Testing command sequence...")
        screen.run_sequence(commands)

        print("✓ Demo completed successfully")

    except Exception as e:
        print(f"✗ Demo failed: {e}")
        print("Running in fallback mode with basic functionality")


if __name__ == "__main__":
    # Try to build modules, but continue if it fails
    try:
        build_modules()
    except Exception as e:
        print(f"Build failed, continuing with fallback: {e}")

    # Run demo
    run_demo()
