import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath("."))
from src.engine.utils.assets import AssetManifest

BUILD_LOG_FILE = "build.log"

def log_build(message: str) -> None:
    """Log build step output to console and build.log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(BUILD_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

def get_git_commit_hash() -> str:
    """Retrieve current Git commit hash or return default."""
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"

def clean_build_artifacts() -> None:
    """Remove previous build/ and dist/ directories."""
    log_build("Cleaning prior build artifacts (build/, dist/)...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                log_build(f"Removed '{folder}' directory.")
            except Exception as e:
                log_build(f"Warning: Failed removing '{folder}': {e}")

def run_pyinstaller_build(mode: str) -> bool:
    """Execute PyInstaller build process."""
    spec_file = "HeroEngine.spec"
    if not os.path.exists(spec_file):
        log_build(f"Error: Spec file '{spec_file}' not found.")
        return False

    cmd = [sys.executable, "-m", "PyInstaller", spec_file, "--noconfirm"]
    if mode == "clean":
        cmd.append("--clean")

    log_build(f"Executing PyInstaller command: {' '.join(cmd)}")
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        with open(BUILD_LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n--- PYINSTALLER STDOUT ---\n" + res.stdout)
            f.write("\n--- PYINSTALLER STDERR ---\n" + res.stderr + "\n")

        if res.returncode == 0:
            log_build("PyInstaller compilation completed successfully.")
            return True
        else:
            log_build(f"PyInstaller build failed with exit code {res.returncode}.")
            return False
    except Exception as e:
        log_build(f"Execution error running PyInstaller: {e}")
        return False

def generate_build_metadata(mode: str, output_dir: str) -> None:
    """Generate build_info.json metadata file inside compiled bundle."""
    metadata = {
        "name": "HeroEngine",
        "version": "1.0.0",
        "git_commit": get_git_commit_hash(),
        "build_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": sys.version.split()[0],
        "build_mode": mode
    }

    meta_file = os.path.join(output_dir, "build_info.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    log_build(f"Generated build metadata: {meta_file}")

def verify_compiled_bundle(bundle_dir: str) -> bool:
    """Run post-build runtime usability verification on the compiled bundle."""
    log_build(f"Running runtime usability verification on bundle: '{bundle_dir}'...")

    if not os.path.exists(bundle_dir):
        log_build(f"Verification FAILED: Bundle directory '{bundle_dir}' does not exist.")
        return False

    # Check build_info.json
    meta_path = os.path.join(bundle_dir, "build_info.json")
    if not os.path.exists(meta_path):
        log_build("Verification FAILED: Missing 'build_info.json'.")
        return False

    # Check asset dependencies in bundle or _internal directory
    internal_dir = os.path.join(bundle_dir, "_internal")
    target_base = internal_dir if os.path.exists(internal_dir) else bundle_dir

    all_valid = True
    for rel_src, rel_target in AssetManifest.get_asset_rules():
        check_path = os.path.join(target_base, rel_target)
        if os.path.exists(check_path):
            log_build(f"Verified bundled asset: '{rel_target}' -> OK")
        else:
            log_build(f"Verification FAILED: Missing bundled asset '{rel_target}' at '{check_path}'")
            all_valid = False

    if all_valid:
        log_build("Runtime usability verification PASSED cleanly.")
    return all_valid

def main():
    parser = argparse.ArgumentParser(description="HeroEngine Multi-Mode Packaging Build Runner")
    parser.add_argument("--clean", action="store_true", help="Remove prior build artifacts before compilation")
    parser.add_argument("--debug", action="store_true", help="Run debug build mode")
    parser.add_argument("--release", action="store_true", help="Run production release build mode")
    args = parser.parse_args()

    # Clear previous build log
    if os.path.exists(BUILD_LOG_FILE):
        os.remove(BUILD_LOG_FILE)

    build_mode = "debug" if args.debug else "release"
    log_build(f"--- Starting HeroEngine Build Pipeline (Mode: {build_mode}) ---")

    if args.clean:
        clean_build_artifacts()

    # Verify asset manifest readiness before building
    missing = AssetManifest.verify_all_assets()
    if missing:
        log_build(f"Build FAILED: Missing required source assets: {missing}")
        sys.exit(1)

    # Compile with PyInstaller
    success = run_pyinstaller_build(mode=build_mode)
    if not success:
        log_build("Build pipeline FAILED during PyInstaller compilation.")
        sys.exit(1)

    bundle_dir = os.path.join("dist", "HeroEngine")
    generate_build_metadata(mode=build_mode, output_dir=bundle_dir)

    # Run post-build verification
    if not verify_compiled_bundle(bundle_dir):
        log_build("Build pipeline FAILED post-build runtime usability verification.")
        sys.exit(1)

    log_build("--- HeroEngine Build Pipeline COMPLETED SUCCESSFULLY ---")
    sys.exit(0)

if __name__ == "__main__":
    main()
