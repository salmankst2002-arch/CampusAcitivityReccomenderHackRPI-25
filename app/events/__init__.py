from flask import Blueprint

# Option 1: no url_prefix here
events_bp = Blueprint("events", __name__)

from . import routes  # noqa
