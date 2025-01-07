from typing import List


class AccountManager:
    """
    Manages Instagrama account data retrieval from a file

    :param file_path: Path to the file containing Instagram usernames
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_accounts(self) -> List[str]:
        accounts = set()
        try:
            with open(self.file_path, "r") as file_data:
                for line in file_data:
                    stripped_line = line.strip()
                    if stripped_line:
                        accounts.add(stripped_line)
        except FileNotFoundError:
            raise Exception("File not found")
        if not accounts:
            raise Exception("Usernames not valid")

        return accounts
