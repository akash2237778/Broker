"""Controller for /projects endpoint"""

from typing import (Dict, List, Optional)

from random import choice
from flask import current_app
from pymongo.errors import DuplicateKeyError

from broker.errors.exceptions import InternalServerError

def register_project(
    data: Dict

) -> str:
print(data)
