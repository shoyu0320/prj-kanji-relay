import uuid

from django.db import models
from django.utils import timezone


class Jukugo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(verbose_name="日付", default=timezone.now)
    user_name = models.CharField(verbose_name="ユーザー名", max_length=10)
    created_at = models.DateTimeField(verbose_name="作成日時", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="編集日時", blank=True, null=True)
    jukugo = models.CharField(verbose_name="今の熟語", blank=True, null=True)
    pre_jukugo = models.CharField(verbose_name="前の熟語", blank=True, null=True)
