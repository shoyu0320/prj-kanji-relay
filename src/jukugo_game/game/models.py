import uuid
from typing import Any, Dict

from django.db import models
from account.models import SpecialUser


# makemigrations, migrate はいらないものが入らないように、migrations内を消しつつ進めること
# こいつがデータベースの中身を決める
class Jukugo(models.Model):
    account = models.ForeignKey(
        SpecialUser,
        on_delete=models.DO_NOTHING,
        verbose_name="アカウント名",
        related_name="game",
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    jukugo = models.CharField(
        verbose_name="入力", blank=True, null=True, default="", max_length=5
    )
    pre_jukugo = models.CharField(
        verbose_name="前の熟語", blank=True, null=True, default="", max_length=5
    )

    # A class that is used to define the database table name.
    class Meta:
        db_table = "game"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["account_ids"] = Jukugo.objects.all()  # 登録したデータを走査してる
        return context
