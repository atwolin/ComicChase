from django.db import models
from django.utils.translation import gettext_lazy as _


class Publisher(models.Model):
    """
    出版社 Model
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
    系列漫畫 Model
    """

    class JapanStatus(models.TextChoices):
        ONGOING = "ongoing", _("連載中")
        COMPLETED = "completed", _("已完結")
        HIATUS = "hiatus", _("休刊中")

    class Genre(models.TextChoices):
        ACTION = "action", _("動作")
        ADVENTURE = "adventure", _("冒險")
        COMEDY = "comedy", _("喜劇")
        DRAMA = "drama", _(" drama")
        FANTASY = "fantasy", _("奇幻")
        HORROR = "horror", _("恐怖")
        MYSTERY = "mystery", _("懸疑")
        ROMANCE = "romance", _("戀愛")
        SCI_FI = "sci_fi", _("科幻")
        SLICE_OF_LIFE = "slice_of_life", _("日常")
        SPORTS = "sports", _("運動")
        SUPERNATURAL = "supernatural", _("超自然")

    title_jp = models.CharField(_("原名"), max_length=255, db_index=True, unique=True)
    title_tw = models.CharField(
        _("譯名"), max_length=255, db_index=True, null=True, blank=True
    )
    author_jp = models.CharField(_("作者原名"), max_length=100, null=True, blank=True)
    author_tw = models.CharField(
        _("作者譯名"),
        max_length=100,
        null=True,
        blank=True,
    )
    status_jp = models.CharField(
        _("日本出版狀態"),
        max_length=10,
        choices=JapanStatus.choices,
        default=JapanStatus.ONGOING,
        db_index=True,
    )
    genres = models.CharField(
        _("類型"),
        max_length=255,
        blank=True,
        help_text=_("多個類型用逗號分隔，例如：action,adventure,fantasy"),
    )
    first_published_year = models.PositiveIntegerField(
        _("出版年份"),
        null=True,
        blank=True,
        db_index=True,
        help_text=_("漫畫出版的年份"),
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
        verbose_name = _("系列漫畫")
        verbose_name_plural = _("系列漫畫")
        ordering = ["title_tw", "title_jp"]

    def __str__(self):
        return self.title_tw or self.title_jp

    def get_genres_list(self):
        """返回類型列表"""
        if not self.genres:
            return []
        return [g.strip() for g in self.genres.split(",") if g.strip()]


class UserCollection(models.Model):
    """
    用戶收藏 Model
    """

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="collections",
        verbose_name=_("用戶"),
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name="collected_by",
        verbose_name=_("漫畫系列"),
    )
    created_at = models.DateTimeField(_("收藏時間"), auto_now_add=True)
    notes = models.TextField(_("備註"), blank=True)

    class Meta:
        verbose_name = _("用戶收藏")
        verbose_name_plural = _("用戶收藏")
        unique_together = [["user", "series"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.series}"


class Volume(models.Model):
    """
    單行本 Model
    """

    # 每一列資料代表一本實體書（不論地區）
    class Region(models.TextChoices):
        JAPAN = "JP", _("Japan")
        TAIWAN = "TW", _("Taiwan")

    # 關聯與卷數
    series = models.ForeignKey(
        Series,
        verbose_name=_("關聯漫畫"),
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

    # 基本資訊
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

    # 版本資訊
    variant = models.CharField(
        _("版本備註"),
        max_length=50,
        blank=True,
        default="",
        help_text=_("如：特裝版、首刷限定。普通版留空。"),
    )

    # 出版資訊
    # 刪除 _jp / _tw ，由 region 定義了地區
    release_date = models.DateField(_("發售日期"), null=True, blank=True)
    isbn = models.CharField(
        _("ISBN"), max_length=13, null=True, blank=True, unique=True
    )

    class Meta:
        verbose_name = _("單行本")
        verbose_name_plural = _("單行本")
        ordering = ["series", "volume_number", "region", "release_date"]

        # 確保沒重複寫入
        constraints = [
            models.UniqueConstraint(
                fields=["series", "volume_number", "region", "variant"],
                name="unique_volume_variant",
            )
        ]

    def __str__(self):
        region_str = self.get_region_display()
        variant_str = f" ({self.variant})" if self.variant else ""
        return f"[{region_str}] {self.series} - Vol. {self.volume_number}{variant_str}"
