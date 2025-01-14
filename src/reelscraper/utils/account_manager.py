from typing import List


class AccountManager:
    """
    [AccountManager] loads Instagram account data from a text file.

    **Parameters:**
    - `[file_path]`: Path to a file containing Instagram usernames.
    """

    def __init__(self, file_path: str) -> None:
        """
        Initializes [AccountManager] with a file path for username retrieval.

        **Parameters:**
        - `[file_path]`: File path string where Instagram usernames are stored.
        """
        self.file_path: str = file_path

    def get_accounts(self) -> List[str]:
        """
        get_accounts reads the file at [file_path] line by line, collecting unique and non-empty usernames.

        **Returns:**
        - List of unique Instagram usernames.

        **Raises:**
        - `Exception`: If the file is not found or no valid usernames are present.
        """
        accounts = set()
        try:
            with open(self.file_path, "r", encoding="utf-8") as file_content:
                for line in file_content:
                    stripped_line = line.strip()
                    if stripped_line:
                        accounts.add(stripped_line)
        except FileNotFoundError:
            raise Exception(f"File not found: {self.file_path}")

        if not accounts:
            raise Exception("No valid usernames found in the file.")

        return list(accounts)
