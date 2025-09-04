from flask import Blueprint

bp = Blueprint("v2", __name__)
from . import routes, auth  # noqa
