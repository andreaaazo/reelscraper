from typing import List, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from .db_base import Base, Account, Reel


class DBManager:
    """
    Provides a production-ready interface for database operations using SQLAlchemy.
    - Creates necessary tables if they do not exist.
    - Allows inserting and retrieving data with no duplicates (based on Reel.shortcode).
    """

    def __init__(
        self,
        db_url: str = "sqlite:///scraper.db",
        echo: bool = False,
    ) -> None:
        """
        :param db_url: Database URL (e.g. 'sqlite:///scraper.db').
                       Defaults to an in-memory SQLite for demo if not provided.
        :param echo: If True, SQLAlchemy will log all SQL statements.
        """

        # Create the engine. Using StaticPool is a typical approach for in-memory or small usage.
        # For production usage with Postgres or MySQL, remove `connect_args` and `poolclass`.
        self.engine = create_engine(
            db_url,
            echo=echo,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
            poolclass=StaticPool if "sqlite" in db_url else None,
        )
        Base.metadata.create_all(self.engine)

        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_or_create_account(self, session, username: str) -> Account:
        """
        Retrieves an account by username; creates one if it doesn't exist.
        """
        account = session.query(Account).filter_by(username=username).first()
        if account is None:
            account = Account(username=username)
            session.add(account)
            session.commit()
        return account

    def store_reels(self, username: str, reels_data: List[Dict]) -> None:
        """
        Stores a list of reels in the database, skipping duplicates based on `shortcode`.
        """
        with self.SessionLocal() as session:
            # 1) Find or create the Account row
            account = self.get_or_create_account(session, username)

            # 2) Insert reels, avoiding duplicates
            for reel_data in reels_data:
                shortcode = reel_data.get("shortcode")
                if not shortcode:
                    # Skip any incomplete data
                    continue

                existing_reel = (
                    session.query(Reel).filter_by(shortcode=shortcode).first()
                )
                if existing_reel:
                    # Already in DB, skip to avoid duplicates
                    continue

                # Create a new Reel
                new_reel = Reel(
                    url=reel_data.get("url", ""),
                    shortcode=shortcode,
                    username=reel_data.get("username", username),
                    likes=reel_data.get("likes", 0),
                    comments=reel_data.get("comments", 0),
                    views=reel_data.get("views", 0),
                    posted_time=reel_data.get("posted_time", 0),
                    video_duration=reel_data.get("video_duration", 0.0),
                    numbers_of_qualities=reel_data.get("numbers_of_qualities", 1),
                    width=reel_data.get("dimensions", {}).get("width", 0),
                    height=reel_data.get("dimensions", {}).get("height", 0),
                    account_id=account.id,
                )
                session.add(new_reel)

            try:
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise e
