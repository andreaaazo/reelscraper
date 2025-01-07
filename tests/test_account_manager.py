import unittest
from unittest.mock import mock_open, patch
from reelscraper.utils import AccountManager


class TestAccountManager(unittest.TestCase):
    def test_get_accounts_normal_file(self):
        mock_file_content = "user1\nuser2\nuser3\nuser1\nuser2\n"
        with patch(
            "builtins.open", mock_open(read_data=mock_file_content)
        ) as mocked_file:
            manager = AccountManager("dummy_path.txt")
            accounts = manager.get_accounts()
            expected_accounts = ["user1", "user2", "user3"]
            self.assertCountEqual(accounts, expected_accounts)
            mocked_file.assert_called_once_with("dummy_path.txt", "r")

    def test_get_accounts_empty_file(self):
        mock_file_content = ""
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            manager = AccountManager("empty.txt")
            with self.assertRaises(Exception) as context:
                manager.get_accounts()
            self.assertEqual(str(context.exception), "Usernames not valid")

    def test_get_accounts_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            manager = AccountManager("non_existent.txt")
            with self.assertRaises(Exception) as context:
                manager.get_accounts()
            self.assertEqual(str(context.exception), "File not found")

    def test_get_accounts_with_whitespace(self):
        mock_file_content = " user1 \n\tuser2\nuser3\nuser1\n"
        with patch(
            "builtins.open", mock_open(read_data=mock_file_content)
        ) as mocked_file:
            manager = AccountManager("whitespace.txt")
            accounts = manager.get_accounts()
            expected_accounts = ["user1", "user2", "user3"]
            self.assertCountEqual(accounts, expected_accounts)
            mocked_file.assert_called_once_with("whitespace.txt", "r")

    def test_get_accounts_large_file(self):
        mock_file_content = "\n".join(
            [f"user{i}" for i in range(1000)] + ["user500", "user999"]
        )
        with patch(
            "builtins.open", mock_open(read_data=mock_file_content)
        ) as mocked_file:
            manager = AccountManager("large.txt")
            accounts = manager.get_accounts()
            expected_accounts = [f"user{i}" for i in range(1000)]
            self.assertCountEqual(accounts, expected_accounts)
            mocked_file.assert_called_once_with("large.txt", "r")

    def test_get_accounts_only_empty_lines(self):
        mock_file_content = "\n   \n\t\n"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            manager = AccountManager("only_empty_lines.txt")
            with self.assertRaises(Exception) as context:
                manager.get_accounts()
            self.assertEqual(str(context.exception), "Usernames not valid")
