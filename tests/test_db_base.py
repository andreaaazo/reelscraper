import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from reelscraper.utils.database import Base, Account, Reel


class TestDBBaseModels(unittest.TestCase):
    """
    Tests basic attributes and relationships of Account and Reel models.
    """

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_account_model_fields(self):
        # coverage test line
        account = Account(username="test_user")
        self.assertEqual(account.username, "test_user")

    def test_reel_model_fields(self):
        # coverage test line
        reel = Reel(
            url="http://example.com/reel",
            shortcode="ABC123",
            username="test_user",
            likes=100,
            comments=5,
            views=2000,
            posted_time=1234567890,
            video_duration=15.5,
            numbers_of_qualities=2,
            width=720,
            height=1280,
            account_id=1,
        )
        self.assertEqual(reel.url, "http://example.com/reel")
        self.assertEqual(reel.shortcode, "ABC123")
        self.assertEqual(reel.username, "test_user")
        self.assertEqual(reel.likes, 100)
        self.assertEqual(reel.comments, 5)
        self.assertEqual(reel.views, 2000)
        self.assertEqual(reel.posted_time, 1234567890)
        self.assertEqual(reel.video_duration, 15.5)
        self.assertEqual(reel.numbers_of_qualities, 2)
        self.assertEqual(reel.width, 720)
        self.assertEqual(reel.height, 1280)
        self.assertEqual(reel.account_id, 1)

    def test_relationship_account_to_reels(self):
        session = self.SessionLocal()
        account = Account(username="test_user")
        reel1 = Reel(shortcode="r1", url="dummy", username="test_user", account=account)
        reel2 = Reel(shortcode="r2", url="dummy", username="test_user", account=account)

        session.add(account)
        session.commit()

        self.assertEqual(len(account.reels), 2)
        self.assertIn(reel1, account.reels)
        self.assertIn(reel2, account.reels)

        session.close()
