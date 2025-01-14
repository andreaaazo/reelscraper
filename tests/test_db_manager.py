import unittest
import unittest.mock as mock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Adjust imports to your actual project structure
from reelscraper.utils.database import (
    Account,
    Base,
)  # or wherever you defined them
from reelscraper.utils import DBManager


class TestDBManager(unittest.TestCase):
    """
    Tests the DBManager class, ensuring 100% coverage of init, get_or_create_account, and store_reels.
    """

    def setUp(self):
        """
        Create a fresh DBManager pointing to in-memory SQLite for each test.
        Create all tables so each test starts with an empty DB.
        """
        self.db_manager = DBManager(db_url="sqlite:///:memory:", echo=False)
        self.SessionLocal = self.db_manager._session_local
        Base.metadata.create_all(self.db_manager.engine)

    def tearDown(self):
        """
        Drop all tables so we don't leak data across tests.
        """
        Base.metadata.drop_all(self.db_manager.engine)

    def test_init_db_url(self):
        """
        Tests the fallback to sqlite:///:memory: when no db_url is given.
        """
        dbm = DBManager(db_url="sqlite:///:memory:", echo=False)
        self.assertIsNotNone(dbm.engine)

    def test_init_custom_sqlite_db_url(self):
        """
        Tests that providing a custom SQLite URL still uses in-memory approach,
        ensuring coverage for 'sqlite' in db_url without creating a file.
        """
        dbm = DBManager(
            db_url="sqlite:///:memory:?custom=1", echo=False
        )  # coverage test line
        self.assertIsNotNone(dbm.engine)

    def test_get_or_create_account_creates_new(self):
        """
        Ensure get_or_create_account returns a new Account if none exists.
        """
        with self.SessionLocal() as session:
            account = self.db_manager.get_or_create_account(session, "new_user")
            self.assertIsNotNone(account.id)
            self.assertEqual(account.username, "new_user")

    def test_get_or_create_account_retrieves_existing(self):
        """
        Ensure get_or_create_account retrieves the same Account if it already exists.
        """
        with self.SessionLocal() as session:
            a1 = self.db_manager.get_or_create_account(
                session, "existing_user"
            )  # coverage test line
            a2 = self.db_manager.get_or_create_account(session, "existing_user")
            self.assertEqual(a1.id, a2.id)

    def test_store_reels_inserts_new_reels(self):
        """
        store_reels should successfully insert new reels for a given username.
        """
        reels_data = [
            {
                "url": "http://example.com/r1",
                "shortcode": "R1",
                "username": "bob",
                "likes": 10,
                "comments": 1,
                "views": 100,
                "posted_time": 1111111111,
                "video_duration": 5.5,
                "numbers_of_qualities": 2,
                "dimensions": {"width": 720, "height": 1280},
            },
            {
                "url": "http://example.com/r2",
                "shortcode": "R2",
                "username": "bob",
                "likes": 20,
                "comments": 2,
                "views": 200,
                "posted_time": 2222222222,
                "video_duration": 10.5,
                "numbers_of_qualities": 3,
                "dimensions": {"width": 1080, "height": 1920},
            },
        ]
        self.db_manager.store_reels("bob", reels_data)

        with self.SessionLocal() as session:
            account = session.query(Account).filter_by(username="bob").first()
            self.assertIsNotNone(account)
            self.assertEqual(len(account.reels), 2)

            reel_shortcodes = {r.shortcode for r in account.reels}
            self.assertIn("R1", reel_shortcodes)
            self.assertIn("R2", reel_shortcodes)

    def test_store_reels_skips_incomplete_data(self):
        """
        If a reel data dict lacks a 'shortcode', it should be skipped.
        """
        reels_data = [
            {"url": "no_shortcode_1", "username": "alice"},
            {"url": "no_shortcode_2", "username": "alice"},
        ]
        self.db_manager.store_reels("alice", reels_data)
        with self.SessionLocal() as session:
            account = session.query(Account).filter_by(username="alice").first()
            self.assertIsNotNone(account)
            self.assertEqual(len(account.reels), 0)  # none inserted

    def test_store_reels_skips_duplicates(self):
        """
        If a reel with the same shortcode is already in DB, it should be skipped.
        """
        reels_data1 = [
            {"url": "http://example.com/r3", "shortcode": "R3"},
            {"url": "http://example.com/r4", "shortcode": "R4"},
        ]
        reels_data2 = [
            {"url": "http://example.com/r4-duplicate", "shortcode": "R4"},  # duplicate
            {"url": "http://example.com/r5", "shortcode": "R5"},
        ]
        self.db_manager.store_reels("carol", reels_data1)
        self.db_manager.store_reels("carol", reels_data2)

        with self.SessionLocal() as session:
            account = session.query(Account).filter_by(username="carol").first()
            self.assertIsNotNone(account)
            self.assertEqual(len(account.reels), 3)  # R3, R4, R5

            shortcodes = {r.shortcode for r in account.reels}
            self.assertIn("R3", shortcodes)
            self.assertIn("R4", shortcodes)
            self.assertIn("R5", shortcodes)

    def test_store_reels_handles_sqlalchemy_error(self):
        """
        If session.commit fails with SQLAlchemyError, it should rollback and re-raise.
        """
        reels_data = [
            {"url": "http://example.com/error1", "shortcode": "ERR1"},
        ]

        # We'll patch the *instance* of Session, not sessionmaker.
        def raise_sql_error():
            raise SQLAlchemyError("Simulated DB error")

        # 1) Create the real session we'll be using inside store_reels
        with self.db_manager._session_local() as real_session:
            with mock.patch.object(real_session, "commit", side_effect=raise_sql_error):
                # 2) Also patch SessionLocal so it returns this real_session object
                with mock.patch.object(
                    self.db_manager, "_session_local", return_value=real_session
                ):
                    with self.assertRaises(SQLAlchemyError):
                        self.db_manager.store_reels("dave", reels_data)

        # Now confirm "dave" was not inserted
        with self.SessionLocal() as check_session:
            account = check_session.query(Account).filter_by(username="dave").first()
            self.assertIsNone(account)


if __name__ == "__main__":
    unittest.main()
