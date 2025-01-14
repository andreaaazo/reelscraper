#!/usr/bin/env python3
import sys
import subprocess
import shutil


def check_package_installed(package_name):
    """Check if a package is installed by trying to import it."""
    try:
        __import__(package_name)
    except ImportError:
        print(f"Error: The '{package_name}' package is not installed.")
        print(f"Please install it with:\n\n   pip install {package_name}\n")
        sys.exit(1)


def run_command(command, description):
    """Run a shell command, printing its description and handling errors."""
    print(f"\n==> {description}")
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running: {command}")
        print(f"Return code: {e.returncode}")
        sys.exit(e.returncode)


def main():

    check_package_installed("coverage")
    if shutil.which("coverage") is None:
        print(
            "Error: 'coverage' command not found in PATH. Please ensure that coverage is installed and accessible."
        )
        sys.exit(1)

    # Run the unit tests with coverage
    run_command("python -m pip install -e .", "Installing package in editable mode")

    run_command(
        "coverage run --source=src -m unittest discover -s tests",
        "Running tests with coverage",
    )

    # Generate the HTML coverage report
    run_command("coverage html", "Generating HTML coverage report")

    print("\nCoverage HTML report generated in the 'htmlcov' folder.")


if __name__ == "__main__":
    main()
