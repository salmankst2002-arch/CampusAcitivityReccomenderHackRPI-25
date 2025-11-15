# scripts/seed.py
import click

from app import create_app
from app.extensions import db
from app.models import User, Club, Event  # Import Event as well
from datetime import datetime


@click.command()
def seed():
    """Seed the database with initial Users, Clubs, and Events using the 10-tag vocab."""
    app = create_app()

    with app.app_context():
        # Clear existing data (development only)
        # NOTE: Order matters because of foreign key constraints.
        db.session.query(Event).delete()
        db.session.query(User).delete()
        db.session.query(Club).delete()
        db.session.commit()

        # ------------------------------------------------------------------
        # Users
        # interests must be a comma-separated list of TAG_VOCAB entries:
        # academic_stem_tech, business_career, creative_arts, sports,
        # gaming, service, activism_environment, politics, cultural, faith
        # ------------------------------------------------------------------
        users = [
            User(
                email="alice@example.com",
                name="Alice",
                year="freshman",
                major="Computer Science",
                interests="academic_stem_tech,gaming,creative_arts",
            ),
            User(
                email="bob@example.com",
                name="Bob",
                year="sophomore",
                major="Economics",
                interests="business_career,service,cultural",
            ),
            User(
                email="carol@example.com",
                name="Carol",
                year="junior",
                major="Environmental Science",
                interests="activism_environment,sports,service",
            ),
            User(
                email="dave@example.com",
                name="Dave",
                year="freshman",
                major="Undeclared",
                interests="gaming,sports,cultural",
            ),
            # Extra user with a campus-style email domain for visibility testing
            User(
                email="yusuke@albany.edu",
                name="Yusuke",
                year="freshman",
                major="Computer Science",
                interests="academic_stem_tech,activism_environment",
            ),
        ]

        # ------------------------------------------------------------------
        # Clubs
        # tags must also be comma-separated TAG_VOCAB entries.
        # ------------------------------------------------------------------
        clubs = [
            Club(
                name="AI & Robotics Lab Club",
                description=(
                    "Student-run club for projects in AI, robotics, and machine learning. "
                    "We do weekly hack nights and semester-long projects."
                ),
                tags="academic_stem_tech",
                meeting_time="Tue 18:00",
                location="Engineering Building Room 101",
            ),
            Club(
                name="Startup & Entrepreneurship Circle",
                description=(
                    "Discuss startup ideas, host pitch nights, and invite founders "
                    "and alumni to talk about building companies."
                ),
                tags="business_career,academic_stem_tech",
                meeting_time="Thu 19:00",
                location="Business School Lounge",
            ),
            Club(
                name="Campus Jazz Band",
                description=(
                    "Open jazz ensemble for all instruments and levels. "
                    "We rehearse weekly and perform once per semester."
                ),
                tags="creative_arts",
                meeting_time="Wed 19:30",
                location="Music Hall Studio 3",
            ),
            Club(
                name="Recreational Soccer Club",
                description=(
                    "Casual soccer games twice a week, open to all skill levels. "
                    "Great for staying active and meeting new people."
                ),
                tags="sports",
                meeting_time="Mon 17:00",
                location="Main Athletic Field",
            ),
            Club(
                name="Board Games & Tabletop Society",
                description=(
                    "Weekly board game nights with modern board games, card games, "
                    "and tabletop RPG one-shots."
                ),
                tags="gaming,creative_arts",
                meeting_time="Fri 19:00",
                location="Student Lounge",
            ),
            Club(
                name="Community Service Volunteers",
                description=(
                    "Organizes volunteering trips and service projects in the local community. "
                    "Transportation is usually provided."
                ),
                tags="service",
                meeting_time="Sat 10:00",
                location="Community Center",
            ),
            Club(
                name="Climate Action & Sustainability Group",
                description=(
                    "Student organization focused on climate activism, sustainability projects, "
                    "and campus-wide environmental campaigns."
                ),
                tags="activism_environment,service",
                meeting_time="Tue 17:30",
                location="Science Building Room 210",
            ),
            Club(
                name="Debate & Politics Forum",
                description=(
                    "Hosts weekly debates on current events and political issues, "
                    "plus practice sessions for competitions."
                ),
                tags="politics,academic_stem_tech",
                meeting_time="Thu 18:30",
                location="Humanities Building Room 305",
            ),
            Club(
                name="International & Cultural Exchange Club",
                description=(
                    "Cultural potlucks, language exchange, and events celebrating "
                    "different cultures on campus."
                ),
                tags="cultural",
                meeting_time="Fri 18:00",
                location="Global Lounge",
            ),
            Club(
                name="Interfaith Fellowship",
                description=(
                    "Discussion and community space for students from different faith "
                    "backgrounds. Weekly meetings and occasional retreats."
                ),
                tags="faith,service",
                meeting_time="Sun 16:00",
                location="Chapel Meeting Room",
            ),
        ]

        db.session.add_all(users + clubs)
        db.session.commit()

        # Reload from DB so that IDs are available
        all_users = User.query.order_by(User.id).all()
        all_clubs = Club.query.order_by(Club.id).all()

        # Simple helpers to pick specific clubs by index
        ai_club = all_clubs[0]   # AI & Robotics Lab Club
        startup_club = all_clubs[1]
        jazz_club = all_clubs[2]
        soccer_club = all_clubs[3]

        # ------------------------------------------------------------------
        # Events
        # visibility_mode:
        #   "public"          -> visible to everyone
        #   "members_only"    -> visible only to club members (stub for now)
        #   "domain_allowlist" -> only listed email domains can see the event
        #   "domain_blocklist" -> all except listed email domains can see the event
        # visible_email_domains is stored as comma-separated string on the model.
        # ------------------------------------------------------------------
        events = [
            # Public event, open to everyone
            Event(
                club_id=ai_club.id,
                title="Intro to Robotics Kickoff",
                description="Overview of the club projects and a simple robotics demo.",
                start_time=datetime(2025, 9, 20, 18, 0, 0),
                end_time=datetime(2025, 9, 20, 20, 0, 0),
                location="Engineering Building Room 101",
                is_online=False,
                join_link=None,
                capacity=50,
                visibility_mode="public",
                visible_email_domains=None,
            ),
            # Domain allowlist: only campus emails can see it
            Event(
                club_id=ai_club.id,
                title="Research Reading Group (CS Dept only)",
                description="Weekly reading group on ML and robotics papers.",
                start_time=datetime(2025, 9, 22, 18, 0, 0),
                end_time=datetime(2025, 9, 22, 19, 30, 0),
                location="Engineering Building Room 202",
                is_online=False,
                join_link=None,
                capacity=20,
                visibility_mode="domain_allowlist",
                visible_email_domains="albany.edu,kgu.ac.jp",
            ),
            # Online event example
            Event(
                club_id=startup_club.id,
                title="Founder AMA Night (Online)",
                description="Q&A session with alumni founder over Zoom.",
                start_time=datetime(2025, 9, 25, 19, 0, 0),
                end_time=datetime(2025, 9, 25, 20, 30, 0),
                location="Online",
                is_online=True,
                join_link="https://example.com/zoom-link",
                capacity=100,
                visibility_mode="public",
                visible_email_domains=None,
            ),
            # Domain blocklist example: hide from generic email domains
            Event(
                club_id=jazz_club.id,
                title="Jazz Jam Session (Campus-only)",
                description="Open jam session; please bring your own instrument.",
                start_time=datetime(2025, 9, 27, 19, 30, 0),
                end_time=datetime(2025, 9, 27, 22, 0, 0),
                location="Music Hall Studio 3",
                is_online=False,
                join_link=None,
                capacity=30,
                visibility_mode="domain_blocklist",
                visible_email_domains="gmail.com,yahoo.com",
            ),
            # Simple public sports event
            Event(
                club_id=soccer_club.id,
                title="Pick-up Soccer Game",
                description="Casual game, all skill levels welcome.",
                start_time=datetime(2025, 9, 21, 17, 0, 0),
                end_time=datetime(2025, 9, 21, 18, 30, 0),
                location="Main Athletic Field",
                is_online=False,
                join_link=None,
                capacity=None,
                visibility_mode="public",
                visible_email_domains=None,
            ),
        ]

        db.session.add_all(events)
        db.session.commit()

        print("Seed completed: inserted Users, Clubs, and Events with visibility settings.")


if __name__ == "__main__":
    seed()
