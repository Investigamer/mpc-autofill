from datetime import date

from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.postgres.fields import ArrayField
from django.db import transaction
from django.db.models import Count, Sum, ExpressionWrapper, IntegerField, Q, F, Max, DateField
from django.db.models.functions import Coalesce
from django.utils.safestring import mark_safe
from django_q.admin import FailAdmin as FailAdminBase
from django_q.admin import QueueAdmin as QueueAdminBase
from django_q.admin import ScheduleAdmin as ScheduleAdminBase
from django_q.admin import TaskAdmin as SuccessAdminBase
from django_q.models import Schedule, Failure, OrmQ, Success
from unfold.admin import ModelAdmin
from unfold.contrib.inlines.admin import NonrelatedTabularInline
from unfold.contrib.filters.admin import SliderNumericFilter, RangeDateFilter
from unfold.contrib.forms.widgets import ArrayWidget
from unfold.forms import UserChangeForm, UserCreationForm, AdminPasswordChangeForm

from .models import (
    CanonicalArtist,
    CanonicalCard,
    CanonicalExpansion,
    Card,
    CardTypes,
    DFCPair,
    Project,
    ProjectMember,
    Source,
    Tag,
)
from .sources.source_types import SourceTypeChoices

"""
* Admin Filters
"""


class DPIFilter(SliderNumericFilter):
    MAX_DECIMALS = 0
    STEP = 50

    def __init__(
        self,
        _field,
        request,
        params,
        model,
        model_admin,
        field_path
    ) -> None:
        """Pass an IntegerField as a placeholder for the annotated 'dpi_average' field from the QuerySet."""
        _field = IntegerField(name='dpi_average', verbose_name='Average DPI')
        super().__init__(_field, request, params, model, model_admin, _field.name)


class LastUpdatedFilter(RangeDateFilter):

    def __init__(
        self,
        _field,
        request,
        params,
        model,
        model_admin,
        field_path
    ) -> None:
        """Pass a DateField as a placeholder for the annotated 'last_updated' field from the QuerySet."""
        _field = DateField(name='last_updated', verbose_name='Last Activity')
        super().__init__(_field, request, params, model, model_admin, _field.name)


"""
* Admin Pages
"""


# Register your models here.
@admin.register(Tag)
class AdminTag(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    formfield_overrides = {
        ArrayField: {"widget": ArrayWidget}
    }


@admin.register(Card)
class AdminCard(ModelAdmin):
    list_display = ("identifier", "name", "source", "dpi", "date_created", "tags")
    search_fields = ("identifier", "name")
    raw_id_fields = ["canonical_card", "inferred_canonical_card"]


@admin.register(DFCPair)
class AdminDFCPair(ModelAdmin):
    list_display = ("front", "back")
    search_fields = ("front",)


class SourceReorderInline(NonrelatedTabularInline):
    model = Source
    fields = ("ordinal", "name", "description", "is_public", "is_paused")
    list_editable = ("description", "is_paused", "is_public")
    readonly_fields = ("name",)
    verbose_name = "Reorder"
    verbose_name_plural = "Reorder"
    hide_title = True

    # Drag to sort by ordinal
    ordering = ("ordinal",)
    ordering_field = "ordinal"

    # Separate inline tab
    tab = True

    def get_form_queryset(self, _obj):
        # Source the data for unrelated inline
        return Source.objects.all().order_by("ordinal")

    def save_new_instance(self, parent, instance):
        # Required to exist
        pass


@admin.register(Source)
class AdminSource(ModelAdmin):
    list_display = (
        "ordinal",
        "name",
        "identifier",
        "num_total",
        "num_cards",
        "num_tokens",
        "num_backs",
        "dpi_average",
        "last_updated",
        "url",
        "is_paused",
        "is_public")
    list_display_links = ("ordinal", "name")
    list_fullwidth = True
    list_editable = ("identifier", "is_paused", "is_public")
    list_filter_submit = True
    list_filter = (
        ('card__dpi', DPIFilter),
        ('card__date_modified', LastUpdatedFilter),
        ('is_paused', admin.BooleanFieldListFilter),
        ('is_public', admin.BooleanFieldListFilter),
    )
    readonly_fields = ('dpi_average',)
    ordering = ('ordinal',)
    search_fields = ("name", "identifier")
    inlines = [SourceReorderInline]

    @admin.display(description="DPI", ordering='dpi_average')
    def dpi_average(self, obj) -> int:
        """Average DPI of images provided by a source."""
        return int(obj.dpi_average or 0)

    @admin.display(description="Contribution", ordering='num_total')
    def contribution(self, obj) -> str:
        """A formatted string of the total contributions for this source.

        Todo:
            Deprecate this?
        """
        return (f"{obj.qty_cards} cards, "
                f"{obj.qty_cardbacks} backs, "
                f"{obj.qty_tokens} tokens")

    @admin.display(description="Last Active", ordering="last_updated", empty_value='—')
    def last_updated(self, obj) -> date | str:
        _date_time = obj.last_updated
        if _date_time:
            try:
                return _date_time.date()
            except (AttributeError, ValueError, TypeError):
                pass
        return _date_time

    # @admin.display(description="ID", ordering='identifier')
    def id_short(self, obj) -> str:
        """ID"""
        _id = obj.identifier
        if len(_id) < 6:
            return f'{_id}...'
        return f'{_id[:6]}...'

    @admin.display(description="Total", ordering='num_total')
    def num_total(self, obj) -> int:
        """Total image provided by this source."""
        return int(obj.num_total)

    @admin.display(description="Cards", ordering='num_cards')
    def num_cards(self, obj) -> int:
        """Total cards provided by this source."""
        return int(obj.num_cards)

    @admin.display(description="Tokens", ordering='num_tokens')
    def num_tokens(self, obj) -> int:
        """Total tokens provided by this source."""
        return int(obj.num_tokens)

    @admin.display(description="Backs", ordering='num_backs')
    def num_backs(self, obj) -> int:
        """Total cardbacks provided by this source."""
        return int(obj.num_backs)

    def url(self, obj) -> str:
        if obj.source_type == SourceTypeChoices.GOOGLE_DRIVE:
            return mark_safe(
                f'<a href="https://drive.google.com/open?id={obj.identifier}">🌐</a>')
        return '⛔'

    def get_queryset(self, request):
        """Modify the queryset to add total cards and dpi average fields."""
        return super().get_queryset(request).annotate(
            num_total=Count('card'),
            num_cards=Count('card', filter=Q(card__card_type=CardTypes.CARD)),
            num_tokens=Count('card', filter=Q(card__card_type=CardTypes.TOKEN)),
            num_backs=Count('card', filter=Q(card__card_type=CardTypes.CARDBACK)),
            dpi_average=Coalesce(
                ExpressionWrapper(
                    expression=(Sum('card__dpi') / Coalesce(F('num_total'), 1)),
                    output_field=IntegerField()),
                0),
            last_updated=ExpressionWrapper(
                expression=Coalesce(Max('card__date_modified'), date.today()),
                output_field=DateField())
        )

    @transaction.atomic
    def save_formset(self, request, form, formset, change) -> None:
        """Normalize ordinals to (1 -> N) for the sortable inline so we never persist 0."""

        # If this isn't for Source inline, fall back to default behavior
        if getattr(formset, "model", None) is not Source:
            return super().save_formset(request, form, formset, change)

        # Save without committing to avoid partial writes
        instances = formset.save(commit=False)

        # Delete marked-for-deletion first
        for obj in formset.deleted_objects:
            obj.delete()

        # Build ordered list of forms we keep, sorted by ordinal just in case
        kept_forms = [
            f for f in formset.forms
            if getattr(f, "cleaned_data", None) and not f.cleaned_data.get("DELETE")
        ]
        kept_forms.sort(key=lambda f: f.cleaned_data.get("ordinal", 0))

        # Reassign ordinals incrementing from 1, save, handle remaining m2m
        for i, f in enumerate(kept_forms, start=1):
            obj = f.instance
            obj.ordinal = i
            obj.save()
        return formset.save_m2m()


@admin.register(Project)
class AdminProject(ModelAdmin):
    list_display = ("key", "name", "user", "date_created", "date_modified", "cardback", "cardstock")


@admin.register(ProjectMember)
class AdminCardProjectMembership(ModelAdmin):
    list_display = ("card_id", "project", "query", "slot", "face")


@admin.register(CanonicalArtist)
class AdminCanonicalArtist(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(CanonicalExpansion)
class AdminCanonicalExpansion(ModelAdmin):
    list_display = ("code", "name", "game")
    search_fields = ("code", "name")


@admin.register(CanonicalCard)
class AdminCanonicalCard(ModelAdmin):
    list_display = ("identifier", "name", "expansion", "collector_number", "is_default")
    search_fields = ("name",)


"""
* Django Auth Admin Integration
"""

# Unregister Django defaults
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


"""
* Django-Q Admin Integration
"""

# Unregister Django-Q defaults
admin.site.unregister(Failure)
admin.site.unregister(OrmQ)
admin.site.unregister(Schedule)
admin.site.unregister(Success)


@admin.register(Failure)
class FailAdmin(FailAdminBase, ModelAdmin):
    pass


@admin.register(OrmQ)
class QueueAdmin(QueueAdminBase, ModelAdmin):
    pass


@admin.register(Schedule)
class ScheduleAdmin(ScheduleAdminBase, ModelAdmin):
    pass


@admin.register(Success)
class SuccessAdmin(SuccessAdminBase, ModelAdmin):
    pass
