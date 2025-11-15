# scripts/seed.py
import click

from app import create_app
from app.extensions import db
from app.models import User, Club


@click.command()
def seed():
    """Seed the database with initial Users and Clubs."""
    app = create_app()

    with app.app_context():
        # Clear existing data (optional for development)
        db.session.query(User).delete()
        db.session.query(Club).delete()
        db.session.commit()

        # Create some users
        users = [
            User(
                email="alice@example.com",
                name="Alice",
                year="freshman",
                major="Computer Science",
                interests="AI,Music,Games",
            ),
            User(
                email="bob@example.com",
                name="Bob",
                year="sophomore",
                major="Physics",
                interests="Robotics,Sports",
            ),
        ]

        # Create some clubs
        clubs = [
            Club(
                name="AI Club",
                description="Weekly meetups to talk about AI and ML projects.",
                tags="AI,Programming,Tech",
                meeting_time="Tue 18:00",
                location="Room 101",
            ),
            Club(
                name="Music Jam Session",
                description="Casual music sessions for all levels.",
                tags="Music,Performance",
                meeting_time="Fri 19:00",
                location="Studio 3",
            ),
            Club(
                name="Board Game Night",
                description="Play board games and meet new friends.",
                tags="Games,Social",
                meeting_time="Wed 20:00",
                location="Student Lounge",
            ),
        ]

        db.session.add_all(users + clubs)
        db.session.commit()

        print("Seed completed: inserted Users and Clubs.")


if __name__ == "__main__":
    seed()
