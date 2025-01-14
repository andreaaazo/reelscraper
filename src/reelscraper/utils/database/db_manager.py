from typing import List, Dict, Optional, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from .db_base import Base, Account, Reel


class DBManager:
    """
    [DBManager] handles database operations using SQLAlchemy.

    Uses composition for managing account and reel data with single responsibility.
    Follows clean code guidelines to provide a simple interface for CRUD operations.

    **Parameters:**
    - `[db_url]`: Database connection URL (e.g. "sqlite:///scraper.db").
    - `[echo]`: If True, logs SQL statements for debugging (default: False).
    """

    def __init__(
        self,
        db_url: str = "sqlite:///scraper.db",
        echo: bool = False,
    ) -> None:
        """
        Initializes database engine, creates tables if not present, and configures session handling.

        **Parameters:**
        - `[db_url]`: Database URL string (e.g. "sqlite:///scraper.db").
        - `[echo]`: Enables SQL statement logging if True (default: False).
        """
        self.engine = create_engine(
            db_url,
            echo=echo,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
            poolclass=StaticPool if "sqlite" in db_url else None,
        )
        Base.metadata.create_all(self.engine)
        self._session_local = sessionmaker(bind=self.engine)

    def get_or_create_account(self, session: Session, username: str) -> Account:
        """
        Retrieves an [Account] by [username] or creates a new entry if it does not exist.

        **Parameters:**
        - `[session]`: Active SQLAlchemy session.
        - `[username]`: Instagram username.

        **Returns:**
        - [Account] object corresponding to the specified username.
        """
        account = session.query(Account).filter_by(username=username).first()
        if account is None:
            account = Account(username=username)
            session.add(account)
            session.commit()
        return account

    def store_reels(self, username: str, reels_data: List[Dict[str, Any]]) -> None:
        """
        Stores a list of reels in the database, skipping duplicates based on `shortcode`.

        **Parameters:**
        - `[username]`: Instagram username associated with the reels.
        - `[reels_data]`: List of dictionaries containing reel information.

        **Returns:**
        - None, but persists new reels in the database. Rolls back on SQLAlchemyError.

        **Raises:**
        - `SQLAlchemyError`: If database transaction fails.
        """
        with self._session_local() as session:
            # Find or create the account row
            account: Account = self.get_or_create_account(session, username)

            # Insert reels, avoiding duplicates
            for reel_data in reels_data:
                shortcode: Optional[str] = reel_data.get("shortcode")
                if not shortcode:
                    # Skip incomplete data (no shortcode means invalid reel)
                    continue

                existing_reel: Optional[Reel] = (
                    session.query(Reel).filter_by(shortcode=shortcode).first()
                )
                if existing_reel:
                    # Duplicate found, skip insertion
                    continue

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
