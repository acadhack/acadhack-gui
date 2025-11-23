#!/usr/bin/env python3
"""
Build script for AcadHack GUI application on Windows.

This script:
1. Installs dependencies from requirements_windows.txt
2. Runs PyInstaller with the spec file
3. Validates the build output
4. Provides clear error messages
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """
    Execute a command and return success status.
    
    Args:
        cmd: List of command arguments
        description: Human-readable description of what we're doing
        cwd: Working directory (defaults to current)
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"[*] {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=False,
        )
        print(f"\n[✓] {description} - SUCCESS\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[✗] {description} - FAILED")
        print(f"Exit code: {e.returncode}\n")
        return False
    except FileNotFoundError as e:
        print(f"\n[✗] Command not found: {e}\n")
        return False


def validate_build_output(dist_dir, app_name):
    """
    Validate that the build output exists and contains the executable.
    
    Args:
        dist_dir: Path to dist directory
        app_name: Name of the application (folder name)
    
    Returns:
        bool: True if validation passes
    """
    print(f"\n{'='*70}")
    print("[*] Validating build output...")
    print(f"{'='*70}\n")
    
    app_dir = Path(dist_dir) / app_name
    exe_path = app_dir / f"{app_name}.exe"
    
    checks = [
        ("dist/ folder exists", (Path(dist_dir).exists(), Path(dist_dir))),
        (f"{app_name}/ folder exists", (app_dir.exists(), app_dir)),
        (f"{app_name}.exe exists", (exe_path.exists(), exe_path)),
        ("_internal/ folder exists", ((app_dir / "_internal").exists(), app_dir / "_internal")),
        ("PySide6 plugins bundled", ((app_dir / "_internal" / "PySide6" / "plugins").exists(), 
                                    app_dir / "_internal" / "PySide6" / "plugins")),
        ("web/ assets included", ((app_dir / "web").exists(), app_dir / "web")),
    ]
    
    all_passed = True
    for check_name, (passed, path) in checks:
        status = "[✓]" if passed else "[✗]"
        print(f"{status} {check_name}")
        if passed:
            print(f"    → {path}\n")
        else:
            print(f"    ✗ Expected at: {path}\n")
            all_passed = False
    
    if all_passed:
        print(f"[✓] Build validation PASSED")
        print(f"    Executable ready: {exe_path}\n")
    else:
        print(f"[✗] Build validation FAILED")
        print(f"    Check the build output above for errors.\n")
    
    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Build AcadHack GUI executable for Windows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_windows.py                    # Full build with validation
  python build_windows.py --no-validate      # Build without validation
  python build_windows.py --clean-first      # Remove old build artifacts first
        """,
    )
    parser.add_argument(
        "--clean-first",
        action="store_true",
        help="Remove build/ and dist/ directories before building",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation of build output",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use (default: current Python)",
    )
    
    args = parser.parse_args()
    
    # Determine paths
    base_dir = Path(__file__).parent.resolve()
    spec_file = base_dir / "app_webview.spec"
    requirements_file = base_dir / "requirements_windows.txt"
    dist_dir = base_dir / "dist"
    build_dir = base_dir / "build"
    
    print("\n" + "="*70)
    print("AcadHack GUI - Windows Build Script")
    print("="*70)
    print(f"Base directory: {base_dir}")
    print(f"Python: {args.python}")
    print("="*70)
    
    # Validate prerequisites
    if not spec_file.exists():
        print(f"\n[✗] ERROR: Spec file not found: {spec_file}")
        sys.exit(1)
    
    if not requirements_file.exists():
        print(f"\n[✗] ERROR: Requirements file not found: {requirements_file}")
        sys.exit(1)
    
    # Clean previous builds if requested
    if args.clean_first:
        print(f"\n[*] Cleaning previous build artifacts...")
        for path in [build_dir, dist_dir]:
            if path.exists():
                import shutil
                print(f"    Removing {path}")
                shutil.rmtree(path)
        print(f"[✓] Cleanup complete\n")
    
    # Step 1: Install dependencies
    if not run_command(
        [args.python, "-m", "pip", "install", "--upgrade", "pip"],
        "Upgrading pip",
        cwd=base_dir,
    ):
        print("[!] Warning: pip upgrade failed, continuing anyway...")
    
    if not run_command(
        [args.python, "-m", "pip", "install", "-r", str(requirements_file)],
        "Installing dependencies from requirements_windows.txt",
        cwd=base_dir,
    ):
        print("[✗] Failed to install dependencies")
        sys.exit(1)
    
    # Step 2: Run PyInstaller
    if not run_command(
        [args.python, "-m", "PyInstaller", str(spec_file), "--noconfirm", "--clean"],
        "Building executable with PyInstaller",
        cwd=base_dir,
    ):
        print("[✗] PyInstaller build failed")
        sys.exit(1)
    
    # Step 3: Validate (optional)
    if not args.no_validate:
        if not validate_build_output(dist_dir, "AcadHack"):
            print("\n[!] Build validation failed. Check the output above.")
            sys.exit(1)
    
    print("\n" + "="*70)
    print("[✓] BUILD COMPLETE")
    print("="*70)
    print(f"Output location: {dist_dir / 'AcadHack'}")
    print(f"To run: .\\dist\\AcadHack\\AcadHack.exe")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
