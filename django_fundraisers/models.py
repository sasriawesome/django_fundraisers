import enum
import uuid
from django.db import models
from django.db.utils import cached_property
from django.core.validators import MinValueValidator
from django.utils import translation, timezone
from django.contrib.auth import get_user_model
from django.shortcuts import reverse

from django_numerators.models import NumeratorMixin
from django_products.models import Product
from django_products.mixins import PostMixin
from django_products.utils import unique_slugify

from filer.fields.image import FilerImageField
from polymorphic.models import PolymorphicModel

_ = translation.ugettext_lazy


class MaxLength(enum.Enum):
    SHORT = 128
    MEDIUM = 256
    LONG = 512
    XLONG = 1024
    TEXT = 2048
    RICHTEXT = 10000


class BaseManager(models.Manager):
    """
        Implement paranoid mechanism queryset
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def get(self, *args, **kwargs):
        kwargs['is_deleted'] = False
        return super().get(*args, **kwargs)


class BaseModel(models.Model):
    class Meta:
        abstract = True

    objects = BaseManager()

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        verbose_name='uuid')
    is_deleted = models.BooleanField(
        default=False,
        editable=False,
        verbose_name=_('is deleted?'))
    deleted_by = models.ForeignKey(
        get_user_model(),
        editable=False,
        null=True, blank=True,
        related_name="%(class)s_deleter",
        on_delete=models.CASCADE,
        verbose_name=_('deleter'))
    deleted_at = models.DateTimeField(
        null=True, blank=True, editable=False)
    owner = models.ForeignKey(
        get_user_model(),
        editable=False,
        null=True, blank=True,
        related_name="%(class)s_creator",
        on_delete=models.CASCADE,
        verbose_name=_('creator'))
    created_at = models.DateTimeField(
        default=timezone.now, editable=False)
    modified_at = models.DateTimeField(
        null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        self.modified_at = timezone.now()
        super().save(**kwargs)

    def delete(self, using=None, keep_parents=False, paranoid=False):
        """
            Give paranoid delete mechanism to each record
        """
        if paranoid:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
        else:
            super().delete(using=using, keep_parents=keep_parents)


class Fundraiser(NumeratorMixin, BaseModel):
    class Meta:
        verbose_name = _("Fundraiser")
        verbose_name_plural = _("Fundraisers")

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"))
    slug = models.SlugField(
        max_length=500,
        null=True, blank=False,
        verbose_name=_("slug"))
    founder = models.OneToOneField(
        get_user_model(),
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("founder"))
    year_founded = models.IntegerField(
        null=True, blank=False,
        verbose_name=_('Year founded'))
    logo = FilerImageField(
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="campaigner_logos")
    mission = models.TextField(
        max_length=5000,
        null=True, blank=False,
        verbose_name=_('Mission'))

    phone1 = models.CharField(
        max_length=20,
        null=True, blank=True,
        verbose_name=_('Phone 1'))
    fax = models.CharField(
        max_length=20,
        null=True, blank=True,
        verbose_name=_('Fax'))
    whatsapp = models.CharField(
        max_length=20,
        null=True, blank=True,
        verbose_name=_('Whatsapp'))
    email = models.EmailField(
        max_length=50,
        null=True, blank=True,
        verbose_name=_('Email'))
    website = models.URLField(
        max_length=125,
        null=True, blank=True,
        verbose_name=_('Website'))

    street = models.CharField(
        null=True, blank=True,
        max_length=250,
        verbose_name=_('Street'))
    city = models.CharField(
        null=True, blank=True,
        max_length=125,
        verbose_name=_('City'))
    province = models.CharField(
        null=True, blank=True,
        max_length=125,
        verbose_name=_('Province'))
    country = models.CharField(
        null=True, blank=True,
        max_length=125,
        verbose_name=_('Country'))
    zipcode = models.CharField(
        null=True, blank=True,
        max_length=15,
        verbose_name=_('Zip Code'))
    balance = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Balance"))

    is_organization = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name)
        return super().save(*args, **kwargs)

    @property
    def opts(self):
        return self._meta

    @cached_property
    def url(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return reverse('%s:%s' % (self.opts.app_label, self.opts.model_name), args=(self.slug,))


class Membership(BaseModel):
    class Meta:
        verbose_name = _("Membership")
        verbose_name_plural = _("Memberships")
        unique_together = ('fundraiser', 'member')

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        verbose_name='uuid')
    fundraiser = models.ForeignKey(
        Fundraiser,
        null=True, blank=True,
        related_name="members",
        on_delete=models.CASCADE,
        verbose_name=_('fundraiser'))
    member = models.ForeignKey(
        get_user_model(),
        null=True, blank=True,
        related_name="fundraisers",
        on_delete=models.CASCADE,
        verbose_name=_('member'))
    is_active = models.BooleanField(
        default=False,
        editable=False,
        verbose_name=_('is active?'))
    is_admin = models.BooleanField(
        default=False,
        editable=False,
        verbose_name=_('is admin?'))
    is_staff = models.BooleanField(
        default=False,
        editable=False,
        verbose_name=_('is staff?'))
    is_follower = models.BooleanField(
        default=True,
        editable=False,
        verbose_name=_('is follower?'))
    date_joined = models.DateTimeField(
        null=True, blank=True,
        editable=False,
        verbose_name=_('Date joined'))

    def __str__(self):
        return self.id



class Campaign(PostMixin, Product):
    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")

    min_donation = models.DecimalField(
        default=10000, max_digits=15, decimal_places=0,
        validators=[MinValueValidator(10000)],
        verbose_name=_("min donation"),
        help_text=_("Minimum donation needed for this campaign"))
    target_donation = models.DecimalField(
        default=10000, max_digits=15, decimal_places=0,
        validators=[MinValueValidator(10000)],
        verbose_name=_("target donation"),
        help_text=_("Donation needed for this campaign"))
    summary = models.TextField(
        max_length=250,
        verbose_name=_("summary"),
        help_text=_("Describe campaign shortly"))
    body = models.TextField(
        max_length=5000,
        verbose_name=_("body"),
        help_text=_("Describe campaign more verbose"))
    fundraiser = models.ForeignKey(
        Fundraiser,
        blank=True, null=True,
        verbose_name=_('fundraiser'),
        on_delete=models.SET_NULL,
        related_name='campaigns')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('%s:%s' % (self.opts.app_label, self.opts.model_name), args=(self.slug,))


class FundraiserTransaction(NumeratorMixin, PolymorphicModel):
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        verbose_name='uuid')
    flow = models.CharField(
        max_length=3,
        choices=(('IN', 'In'), ('OUT', 'Out')),
        default='IN', verbose_name=_('Flow'))
    fundraiser = models.ForeignKey(
        Fundraiser, on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_("Fundraiser"))
    amount = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Amount"))
    old_balance = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Old Balance"))
    balance = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Balance"))
    note = models.CharField(
        max_length=250,
        null=True, blank=True,
        verbose_name=_('Note'))
    created_at = models.DateTimeField(
        default=timezone.now, editable=False)

    def __str__(self):
        return self.inner_id

    @property
    def reference(self):
        return self.get_real_instance().get_reference()

    def get_reference(self):
        raise NotImplementedError

    def get_amount(self):
        raise NotImplementedError

    def increase_balance(self):
        self.balance = self.fundraiser.balance + self.amount
        return self.balance

    def decrease_balance(self):
        self.balance = self.fundraiser.balance - self.amount
        return self.balance

    def calculate_balance(self):
        return {'IN': self.increase_balance, 'OUT': self.decrease_balance}[self.flow]()

    def save(self, *args, **kwargs):
        self.old_balance = self.fundraiser.balance
        self.amount = self.get_amount()
        self.calculate_balance()
        super().save(*args, **kwargs)