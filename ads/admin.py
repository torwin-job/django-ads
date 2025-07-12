from django.contrib import admin
from .models import Ad, ExchangeProposal
from django.utils.html import format_html


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "condition", "created_at", "image_tag")
    list_filter = ("category", "condition", "created_at")
    search_fields = ("title", "description", "category", "condition", "user__username")
    readonly_fields = ("image_tag",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "title",
                    "description",
                    "category",
                    "condition",
                    "image",
                    "image_tag",
                )
            },
        ),
        (
            "Дополнительно",
            {
                "fields": ("created_at",),
            },
        ),
    )

    def image_tag(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url,
            )
        return "-"

    image_tag.short_description = "Изображение"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(ExchangeProposal)
class ExchangeProposalAdmin(admin.ModelAdmin):
    list_display = ("ad_sender", "ad_receiver", "status", "created_at", "comment_short")
    list_filter = ("status", "created_at")
    search_fields = ("ad_sender__title", "ad_receiver__title", "comment")
    autocomplete_fields = ["ad_sender", "ad_receiver"]

    def comment_short(self, obj):
        return (obj.comment[:40] + "...") if len(obj.comment) > 40 else obj.comment

    comment_short.short_description = "Комментарий"
