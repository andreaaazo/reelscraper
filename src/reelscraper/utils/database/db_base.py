from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)

    # Relationship: an account can have multiple reels
    reels = relationship("Reel", back_populates="account")


class Reel(Base):
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
