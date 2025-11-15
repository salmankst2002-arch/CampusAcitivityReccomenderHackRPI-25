# app/models.py
import datetime as dt

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    year = db.Column(db.String(50), nullable=True)   # e.g., "freshman"
    major = db.Column(db.String(255), nullable=True)
    interests = db.Column(db.Text, nullable=True)    # simple comma-separated tags or JSON

    created_at = db.Column(
        db.DateTime, nullable=False, default=dt.datetime.utcnow
    )

    swipes = db.relationship(
        "Swipe",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class Club(db.Model):
    __tablename__ = "clubs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)         # e.g., "AI,Programming,Music"
    meeting_time = db.Column(db.String(255), nullable=True)  # e.g., "Tue 18:00"
    location = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime, nullable=False, default=dt.datetime.utcnow
    )

    swipes = db.relationship(
        "Swipe",
        back_populates="club",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Club id={self.id} name={self.name!r}>"


class Swipe(db.Model):
    __tablename__ = "swipes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    club_id = db.Column(
        db.Integer, db.ForeignKey("clubs.id"), nullable=False, index=True
    )
    liked = db.Column(db.Boolean, nullable=False)  # True if like, False if dislike
    created_at = db.Column(
        db.DateTime, nullable=False, default=dt.datetime.utcnow, index=True
    )

    user = db.relationship("User", back_populates="swipes")
    club = db.relationship("Club", back_populates="swipes")

    def __repr__(self) -> str:
        return f"<Swipe user_id={self.user_id} club_id={self.club_id} liked={self.liked}>"
