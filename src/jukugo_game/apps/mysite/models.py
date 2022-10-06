import uuid

from django.db import models
from django.utils import timezone


class Register(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(verbose_name="日付", default=timezone.now)
    user_name = models.CharField(verbose_name="ユーザー名", max_length=10)
    created_at = models.DateTimeField(verbose_name="作成日時", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="編集日時", blank=True, null=True)
