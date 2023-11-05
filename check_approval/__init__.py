from flask import Blueprint

check_aprvl = Blueprint('check_aprvl', __name__)

from . import routes
