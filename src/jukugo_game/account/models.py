import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Field


class SpecialUser(User):
    special_id: Field = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=False
    )
