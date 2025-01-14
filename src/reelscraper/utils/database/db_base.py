from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Account(Base):
    """
    [Account] model for storing account details.

    Defines a many-to-one relationship with [Reel].

    **Parameters / Columns:**
    - `[id]`: Primary key integer, autoincrement.
    - `[username]`: Unique string representing the Instagram username.
    - `[reels]`: Relationship referencing multiple [Reel] instances.
    """

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)

    # Relationship: an account can have multiple reels
    reels = relationship("Reel", back_populates="account")


class Reel(Base):
    """
    [Reel] model for storing reel information.

    Defines a many-to-one relationship with [Account].

    **Parameters / Columns:**
    - `[id]`: Primary key integer, autoincrement.
    - `[url]`: String representing the reel's URL.
    - `[shortcode]`: Unique reel shortcode, used as an index.
    - `[username]`: String for referencing the reel's poster.
    - `[likes]`: Number of likes on the reel.
    - `[comments]`: Number of comments on the reel.
    - `[views]`: Number of views on the reel.
    - `[posted_time]`: Unix timestamp of when the reel was posted.
    - `[video_duration]`: Duration in seconds of the reel.
    - `[numbers_of_qualities]`: Number of available quality variants.
    - `[width]`: Video width.
    - `[height]`: Video height.
    - `[account_id]`: Foreign key linking to [Account].
    - `[account]`: Relationship back to the [Account] model.
    """

    __tablename__ = "reels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False)
    shortcode = Column(String, unique=True, index=True, nullable=False)
    username = Column(
        String, nullable=False
    )  # for easy reference, but also mapped to Account
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    views = Column(Integer, default=0)
    posted_time = Column(Integer, default=0)
    video_duration = Column(Float, default=0.0)
    numbers_of_qualities = Column(Integer, default=1)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)

    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    account = relationship("Account", back_populates="reels")
