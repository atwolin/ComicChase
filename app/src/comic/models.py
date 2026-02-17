from urllib.parse import urlparse

from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Publisher(models.Model):
    """
    Represents a publisher of comic books.

    This model stores information about publishers. It is used to associate
    each comic volume with its publisher.
    """

    class Region(models.TextChoices):
        JAPAN = "JP", _("Japan")
        TAIWAN = "TW", _("Taiwan")

    name = models.CharField(_("出版社名稱"), max_length=100, unique=True)
    region = models.CharField(
        _("地區"),
        max_length=2,
        choices=Region.choices,
        default=Region.JAPAN,
        help_text="JP (日本) 或 TW (台灣)",
    )

    class Meta:
        verbose_name = _("出版社")
        verbose_name_plural = _("出版社")

    def __str__(self):
        return f"{self.name} ({self.get_region_display()})"


class Series(models.Model):
    """
    Represents a comic book series.

    This model contains core information about a comic series.
    """

    class JapanStatus(models.TextChoices):
        ONGOING = "ongoing", _("連載中")
        COMPLETED = "completed", _("已完結")
        HIATUS = "hiatus", _("休刊中")

    title_jp = models.CharField(_("原名"), max_length=255, db_index=True, unique=True)
    title_tw = models.CharField(
        _("譯名"),
        max_length=255,
        db_index=True,
        blank=True,
        default="",
    )
    author_jp = models.CharField(_("作者原名"), max_length=100)
    author_tw = models.CharField(
        _("作者譯名"),
        max_length=100,
        blank=True,
        default="",
    )
    status_jp = models.CharField(
        _("日本出版狀態"),
        max_length=10,
        choices=JapanStatus.choices,
        default=JapanStatus.ONGOING,
    )

    latest_volume_jp = models.ForeignKey(
        "Volume",
        on_delete=models.SET_NULL,
        related_name="series_latest_jp",
        null=True,
        blank=True,
        verbose_name=_("最新單行本 (日)"),
    )
    latest_volume_tw = models.ForeignKey(
        "Volume",
        on_delete=models.SET_NULL,
        related_name="series_latest_tw",
        null=True,
        blank=True,
        verbose_name=_("最新單行本 (台)"),
    )

    class Meta:
        verbose_name = _("系列")
        verbose_name_plural = _("系列")
        ordering = ["title_tw", "title_jp"]
        indexes = [
            GinIndex(
                fields=["title_tw"],
                name="series_title_tw_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                fields=["title_jp"],
                name="series_title_jp_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                fields=["author_tw"],
                name="series_author_tw_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                fields=["author_jp"],
                name="series_author_jp_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self):
        return self.title_tw or self.title_jp


class Volume(models.Model):
    """
    Represents a single volume of a comic book series.

    Each instance corresponds to a specific physical book and stores details.
    """

    class Region(models.TextChoices):
        JAPAN = "JP", _("Japan")
        TAIWAN = "TW", _("Taiwan")

    series = models.ForeignKey(
        Series,
        verbose_name=_("系列"),
        on_delete=models.CASCADE,
        related_name="volumes",
        null=True,
        blank=True,
    )
    publisher = models.ForeignKey(
        Publisher,
        verbose_name=_("出版社"),
        on_delete=models.SET_NULL,
        related_name="published_volumes",
        null=True,
        blank=True,
    )

    # Basic volume information
    region = models.CharField(
        _("地區"),
        max_length=2,
        choices=Region.choices,
        default=Region.JAPAN,
        db_index=True,
    )
    volume_number = models.PositiveIntegerField(
        _("卷數"), db_index=True, blank=True, null=True
    )
    variant = models.CharField(
        _("版本備註"),
        max_length=50,
        blank=True,
        default="",
        help_text=_("如：特裝版、首刷限定。普通版留空。"),
    )
    release_date = models.DateField(_("發售日期"), null=True, blank=True)
    isbn = models.CharField(_("ISBN"), max_length=13, blank=True, default="")
    image_url = models.URLField(_("封面圖片 URL"), blank=True, default="")
    created_at = models.DateTimeField(
        _("入庫時間"),
        auto_now_add=True,
        help_text=_("此筆資料寫入資料庫的時間"),
    )

    class Meta:
        verbose_name = _("單行本")
        verbose_name_plural = _("單行本")
        ordering = ["series", "region", "volume_number", "release_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["series", "volume_number", "region", "variant"],
                name="unique_volume_variant",
            )
        ]

    def clean(self):
        """Validate model fields to prevent security issues."""
        super().clean()

        # Validate image_url scheme to prevent XSS attacks
        if self.image_url:
            parsed_url = urlparse(self.image_url)
            allowed_schemes = ["http", "https"]

            if parsed_url.scheme and parsed_url.scheme.lower() not in allowed_schemes:
                raise ValidationError(
                    {
                        "image_url": _(
                            f"不安全的 URL scheme: '{parsed_url.scheme}'. "
                            f"僅允許 {', '.join(allowed_schemes)}"
                        )
                    }
                )

    def __str__(self):
        region_str = self.get_region_display()
        variant_str = f" ({self.variant})" if self.variant else ""
        return f"[{region_str}] {self.series} - Vol. {self.volume_number}{variant_str}"
