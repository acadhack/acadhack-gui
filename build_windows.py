#!/usr/bin/env python3
"""
build_windows.py
Windows build script for PyInstaller

This script:
1. Verifies the environment
2. Installs dependencies from requirements_windows.txt
3. Runs PyInstaller with the spec file
4. Verifies the build was successful
5. Reports the output location

Usage:
    python build_windows.py
    
    Or with cleanup:
    python build_windows.py --clean
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


class WindowsBuilder:
    def __init__(self, clean=False):
        self.root_dir = Path.cwd()
        self.requirements_file = self.root_dir / 'requirements_windows.txt'
        self.spec_file = self.root_dir / 'app_webview.spec'
        self.runtime_hook = self.root_dir / 'rthook_pyside6_qtplugins.py'
        self.dist_dir = self.root_dir / 'dist'
        self.build_dir = self.root_dir / 'build'
        self.clean_dirs = clean
        
    def log(self, message, level='INFO'):
        """Print formatted log message"""
        print(f"[{level}] {message}")
    
    def verify_environment(self):
        """Check that all necessary files exist"""
        self.log("Verifying environment...")
        
        if not self.requirements_file.exists():
            self.log(f"ERROR: {self.requirements_file} not found", 'ERROR')
            return False
        
        if not self.spec_file.exists():
            self.log(f"ERROR: {self.spec_file} not found", 'ERROR')
            return False
        
        if not self.runtime_hook.exists():
            self.log(f"ERROR: {self.runtime_hook} not found", 'ERROR')
            return False
        
        if not (self.root_dir / 'app_webview.py').exists():
            self.log("ERROR: app_webview.py (entry point) not found", 'ERROR')
            return False
        
        if not (self.root_dir / 'web').is_dir():
            self.log("ERROR: web/ folder not found", 'ERROR')
            return False
        
        self.log("[+] All required files and folders found")
        return True
    
    def clean_previous_builds(self):
        """Remove previous build artifacts"""
        if self.clean_dirs:
            self.log("Cleaning previous builds...")
            for dir_path in [self.dist_dir, self.build_dir]:
                if dir_path.exists():
                    self.log(f"Removing {dir_path}")
                    shutil.rmtree(dir_path)
            self.log("[+] Clean complete")
    
    def install_dependencies(self):
        """Install Python dependencies from requirements file"""
        self.log("Installing dependencies from requirements_windows.txt...")
        
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                check=True,
                capture_output=False
            )
            
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(self.requirements_file)],
                check=True,
                capture_output=False
            )
            
            self.log("[+] Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"ERROR: Failed to install dependencies: {e}", 'ERROR')
            return False
    
    def run_pyinstaller(self):
        """Execute PyInstaller directly with explicit arguments"""
        self.log("Running PyInstaller...")
        
        import PyInstaller.__main__
        
        # Define paths
        web_source = self.root_dir / 'web'
        sep = ';' if os.name == 'nt' else ':'
        
        # Arguments for PyInstaller
        args = [
            str(self.root_dir / 'app_webview.py'),
            '--name=app_webview',
            '--onedir',
            '--windowed',
            '--clean',
            '--noconfirm',
            f'--add-data={web_source}{sep}web',
            f'--runtime-hook={self.runtime_hook}',
            # Force old onedir layout (no _internal folder)
            '--contents-directory=.',
            # Exclude unnecessary modules to save space/time
            '--exclude-module=tkinter',
            '--exclude-module=matplotlib',
            '--exclude-module=numpy',
        ]
        
        self.log(f"PyInstaller arguments: {args}")
        
        try:
            # Run PyInstaller directly
            PyInstaller.__main__.run(args)
            
            # MANUAL FALLBACK: Ensure web folder exists
            dist_web_path = self.dist_dir / 'app_webview' / 'web'
            if not dist_web_path.exists():
                self.log("[!] Web folder missing after build. Performing manual copy...", 'WARNING')
                shutil.copytree(web_source, dist_web_path)
                self.log("[+] Manual copy successful")
            
            self.log("[+] PyInstaller build completed")
            return True
        except Exception as e:
            self.log(f"ERROR: PyInstaller failed: {e}", 'ERROR')
            return False
    
    def verify_build(self):
        """Verify that the build was successful"""
        self.log("Verifying build output...")
        
        exe_path = self.dist_dir / 'app_webview' / 'app_webview.exe'
        if not exe_path.exists():
            self.log(f"ERROR: Expected executable not found at {exe_path}", 'ERROR')
            return False
        
        web_path = self.dist_dir / 'app_webview' / 'web'
        if not web_path.is_dir():
            self.log(f"ERROR: web/ folder not bundled correctly", 'ERROR')
            self.log(f"Contents of {self.dist_dir / 'app_webview'}:", 'ERROR')
            try:
                for item in (self.dist_dir / 'app_webview').iterdir():
                    self.log(f"  - {item.name}", 'ERROR')
            except Exception as e:
                self.log(f"  Failed to list directory: {e}", 'ERROR')
            return False
        
        # Check for critical Qt plugin
        plugins_dir = self.dist_dir / 'app_webview' / 'PySide6' / 'plugins' / 'platforms'
        if not plugins_dir.exists():
            self.log(f"WARNING: Qt plugins directory not found at expected location", 'WARNING')
            # PyInstaller onedir might put it elsewhere, so just warn
        
        self.log(f"[+] Executable found: {exe_path}")
        self.log(f"[+] Web folder found: {web_path}")
        return True
    
    def report_results(self):
        """Print build summary"""
        print("\n" + "="*70)
        print("BUILD SUMMARY")
        print("="*70)
        
        exe_path = self.dist_dir / 'app_webview' / 'app_webview.exe'
        app_dir = self.dist_dir / 'app_webview'
        
        if exe_path.exists():
            # Get file size
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"[+] SUCCESS! Executable built successfully")
            print(f"\nOutput location: {app_dir}")
            print(f"Executable: {exe_path}")
            print(f"Size: {size_mb:.2f} MB")
            print(f"\nTo run the application:")
            print(f"  cd {app_dir}")
            print(f"  .\\app_webview.exe")
            return True
        else:
            print(f"[!] FAILED: Build did not produce expected output")
            return False
    
    def build(self):
        """Execute the complete build process"""
        self.log("="*70)
        self.log("Windows Build Process Started")
        self.log("="*70)
        
        # Step 1: Verify
        if not self.verify_environment():
            self.log("BUILD FAILED: Environment verification failed", 'ERROR')
            return False
        
        # Step 2: Clean
        self.clean_previous_builds()
        
        # Step 3: Install dependencies
        if not self.install_dependencies():
            self.log("BUILD FAILED: Dependency installation failed", 'ERROR')
            return False
        
        # Step 4: Run PyInstaller
        if not self.run_pyinstaller():
            self.log("BUILD FAILED: PyInstaller execution failed", 'ERROR')
            return False
        
        # Step 5: Verify output
        if not self.verify_build():
            self.log("BUILD FAILED: Output verification failed", 'ERROR')
            return False
        
        # Step 6: Report
        self.report_results()
        return True


def main():
    """Main entry point"""
    clean = '--clean' in sys.argv
    
    builder = WindowsBuilder(clean=clean)
    success = builder.build()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
