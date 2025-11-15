# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Single global instances of extensions (no app bound here)
db = SQLAlchemy()
migrate = Migrate()
