import subprocess
import shutil
import os
import sys


def run_command(command: str) -> None:
    """
    Executes the given shell command and exits the script if the command fails.

    :param command: Shell command to be executed.
    :raises SystemExit: If the command returns a non-zero exit code.
    """
    result = subprocess.run(command, shell=True, check=False)
    if result.returncode != 0:
        print(f"Error executing command: {command}", file=sys.stderr)
        sys.exit(result.returncode)


def main() -> None:
    run_command("python -m pip install -e .")
    run_command("python -m unittest discover -s tests")
    egg_info_dir = "src/reelscraper.egg-info"
    if os.path.isdir(egg_info_dir):
        shutil.rmtree(egg_info_dir)
        print(f"Removed directory: {egg_info_dir}")
    else:
        print(f"Directory {egg_info_dir} not found.")


if __name__ == "__main__":
    main()
