import os
import sys
import platform
import subprocess
import shutil

def build():
    print("🚀 Starting ProjectX Enterprise Build...")
    
    # 1. Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('ProjectX.spec'):
        os.remove('ProjectX.spec')
        
    system = platform.system()
    sep = ';' if system == 'Windows' else ':'
    
    # 2. Define Assets to Include
    # Format: "source_path{sep}dest_path"
    # We need templates, static, and schema.sql
    add_data = [
        f"templates{sep}templates",
        f"schema.sql{sep}."
    ]
    
    # Construct PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=ProjectX",
        "--onefile",  # Single executable
        "--clean",
        "--noconfirm",
        # "--windowed", # Uncomment if we don't want a console window (keep console for now to see logs)
        "--icon=NONE", # Can add icon later
        "api_app.py"
    ]
    
    # Add data arguments
    for item in add_data:
        cmd.extend(["--add-data", item])
        
    # Add hidden imports if necessary (Flask usually needs these)
    hidden_imports = [
        "engineio.async_drivers.threading",
        "jinja2.ext"
    ]
    for hidden in hidden_imports:
        cmd.extend(["--hidden-import", hidden])

    print(f"📦 Packaging for {system}...")
    print(f"   Command: {' '.join(cmd)}")
    
    # 3. Run PyInstaller
    try:
        if system == 'Windows':
            # On Windows, we might need to call it via python -m PyInstaller if not in path, 
            # but usually 'pyinstaller' works if venv is active.
            subprocess.check_call(cmd)
        else:
            # On Mac/Linux, calling the binary directly from venv
            pyinstaller_path = os.path.join("venv", "bin", "pyinstaller")
            if not os.path.exists(pyinstaller_path):
                # Fallback to just "pyinstaller" if venv path structure differs
                pyinstaller_path = "pyinstaller"
            
            cmd[0] = pyinstaller_path
            subprocess.check_call(cmd)
            
        print("\n✅ Build Successful!")
        print(f"   Executable is located in: {os.path.abspath('dist')}")
        print("   You can zip this 'dist' folder and send it to the client.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
