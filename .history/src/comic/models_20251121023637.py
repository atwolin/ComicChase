from django.db import models
from django.utils.translation import gettext_lazy as _

class Publisher(models.Model):
    """
    出版社 Model
    """
    class Region(models.TextChoices):
        JAPAN = 'JP', _('Japan')
        TAIWAN = 'TW', _('Taiwan')

    #關聯
    comic = model

    name = models.CharField(_("出版社名稱"), max_length=100, unique=True)
    region = models.CharField(
        _("地區"),
        max_length=2,
        choices=Region.choices,
        help_text="JP (日本) 或 TW (台灣)"
    )

    class Meta:
        verbose_name = _("出版社")
        verbose_name_plural = _("出版社")

    def __str__(self):
        return f"{self.name} ({self.get_region_display()})"


class Comic(models.Model):
    """
    漫畫作品 Model
    """
    class JapanStatus(models.TextChoices):
        ONGOING = 'ongoing', _('連載中')
        COMPLETED = 'completed', _('已完結')
        HIATUS = 'hiatus', _('休刊中')

    title_jp = models.CharField(
        _("日文原名"), max_length=255, db_index=True, unique=True
    )
    title_tw = models.CharField(
        _("台灣譯名"), max_length=255, db_index=True, null=True, blank=True
    )
    author_jp = models.CharField(_("日文原名作者"), max_length=100)
    author_tw = models.CharField(
        _("台灣譯名作者"),
        max_length=100,
        null=True,
        blank=True,
    )
    status_jp = models.CharField(
        _("日本出版狀態"),
        max_length=10,
        choices=JapanStatus.choices,
        default=JapanStatus.ONGOING
    )

    class Meta:
        verbose_name = _("漫畫作品")
        verbose_name_plural = _("漫畫作品")
        ordering = ['title_tw', 'title_jp'] # 同步更新 ordering

    def __str__(self):
        return self.title_tw or self.title_jp


class Volume(models.Model):
    """
    單行本 Model
    """
    #關聯與卷數
    comic = models.ForeignKey(
        Comic,
        verbose_name=_("關聯漫畫"),
        on_delete=models.CASCADE,
        related_name="volumes",
        blank=True,
        null=True
    )
    volume_number = models.PositiveIntegerField(_("卷數"), unique=True, blank=True, null=True)

    #日本出版資訊
    release_date_jp = models.DateField(_("日本發售日期"), blank=True, null=True)
    isbn_jp = models.CharField(_("日本 ISBN"), max_length=13, unique=True, blank=True, null=True)
    publisher_jp = models.ForeignKey(
        Publisher,
        verbose_name=_("日本出版社"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="jp_volumes",
        limit_choices_to={'region': 'JP'}
    )

    #台灣出版資訊
    release_date_tw = models.DateField(_("台灣發售日期"), blank=True, null=True)
    isbn_tw = models.CharField(_("台灣 ISBN"), unique=True, max_length=13, null=True)
    publisher_tw = models.ForeignKey(
        Publisher,
        verbose_name=_("台灣代理出版社"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tw_volumes",
        limit_choices_to={'region': 'TW'}
    )

    class Meta:
        verbose_name = _("單行本")
        verbose_name_plural = _("單行本")
        indexes = [
            models.Index(fields=['isbn_tw'])
        ]
        unique_together = ('comic', 'volume_number')
        ordering = ['comic', 'volume_number']

    def __str__(self):
        return f"{self.comic} - Vol. {self.volume_number}"
