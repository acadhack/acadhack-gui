import os
import subprocess
import sys
from pathlib import Path
import PyInstaller.__main__

def build():
    """Build Windows executable using spec file."""
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    spec_file = os.path.join(base_dir, 'app_webview.spec')
    
    if not os.path.exists(spec_file):
        print(f"Error: Spec file not found at {spec_file}")
        return False
    
    print(f"Building from spec file: {spec_file}")
    
    try:
        PyInstaller.__main__.run([
            spec_file,
            '--distpath', os.path.join(base_dir, 'dist'),
            '--workpath', os.path.join(base_dir, 'build'),
            '--specpath', base_dir,
            '--clean',
            '--noconfirm',
        ])
        print("Build completed successfully!")
        return True
    except Exception as e:
        print(f"Build failed: {e}")
        return False

if __name__ == "__main__":
    success = build()
    if not success:
        sys.exit(1)
