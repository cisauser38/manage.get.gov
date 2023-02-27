# Generated by Django 4.1.3 on 2022-11-10 14:23

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_fsm  # type: ignore


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Contact",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "first_name",
                    models.TextField(
                        blank=True, db_index=True, help_text="First name", null=True
                    ),
                ),
                (
                    "middle_name",
                    models.TextField(blank=True, help_text="Middle name", null=True),
                ),
                (
                    "last_name",
                    models.TextField(
                        blank=True, db_index=True, help_text="Last name", null=True
                    ),
                ),
                ("title", models.TextField(blank=True, help_text="Title", null=True)),
                (
                    "email",
                    models.TextField(
                        blank=True, db_index=True, help_text="Email", null=True
                    ),
                ),
                (
                    "phone",
                    models.TextField(
                        blank=True, db_index=True, help_text="Phone", null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Website",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("website", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="DomainApplication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    django_fsm.FSMField(
                        choices=[
                            ("started", "started"),
                            ("submitted", "submitted"),
                            ("investigating", "investigating"),
                            ("approved", "approved"),
                        ],
                        default="started",
                        max_length=50,
                    ),
                ),
                (
                    "organization_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("federal", "a federal agency"),
                            ("interstate", "an organization of two or more states"),
                            (
                                "state_or_territory",
                                "one of the 50 U.S. states, the District of Columbia, American Samoa, Guam, Northern Mariana Islands, Puerto Rico, or the U.S. Virgin Islands",
                            ),
                            (
                                "tribal",
                                "a tribal government recognized by the federal or state government",
                            ),
                            ("county", "a county, parish, or borough"),
                            ("city", "a city, town, township, village, etc."),
                            (
                                "special_district",
                                "an independent organization within a single state",
                            ),
                        ],
                        help_text="Type of Organization",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "federal_branch",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Executive", "Executive"),
                            ("Judicial", "Judicial"),
                            ("Legislative", "Legislative"),
                        ],
                        help_text="Branch of federal government",
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "is_election_office",
                    models.BooleanField(
                        blank=True,
                        help_text="Is your ogranization an election office?",
                        null=True,
                    ),
                ),
                (
                    "organization_name",
                    models.TextField(
                        blank=True,
                        db_index=True,
                        help_text="Organization name",
                        null=True,
                    ),
                ),
                (
                    "street_address",
                    models.TextField(blank=True, help_text="Street Address", null=True),
                ),
                (
                    "unit_type",
                    models.CharField(
                        blank=True, help_text="Unit type", max_length=15, null=True
                    ),
                ),
                (
                    "unit_number",
                    models.CharField(
                        blank=True, help_text="Unit number", max_length=255, null=True
                    ),
                ),
                (
                    "state_territory",
                    models.CharField(
                        blank=True, help_text="State/Territory", max_length=2, null=True
                    ),
                ),
                (
                    "zip_code",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="ZIP code",
                        max_length=10,
                        null=True,
                    ),
                ),
                (
                    "purpose",
                    models.TextField(
                        blank=True, help_text="Purpose of the domain", null=True
                    ),
                ),
                (
                    "anything_else",
                    models.TextField(
                        blank=True, help_text="Anything else we should know?", null=True
                    ),
                ),
                (
                    "acknowledged_policy",
                    models.BooleanField(
                        blank=True,
                        help_text="Acknowledged .gov acceptable use policy",
                        null=True,
                    ),
                ),
                (
                    "alternative_domains",
                    models.ManyToManyField(
                        blank=True, related_name="alternatives+", to="registrar.website"
                    ),
                ),
                (
                    "authorizing_official",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authorizing_official",
                        to="registrar.contact",
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="applications_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "current_websites",
                    models.ManyToManyField(
                        blank=True, related_name="current+", to="registrar.website"
                    ),
                ),
                (
                    "investigator",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="applications_investigating",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "other_contacts",
                    models.ManyToManyField(
                        blank=True,
                        related_name="contact_applications",
                        to="registrar.contact",
                    ),
                ),
                (
                    "requested_domain",
                    models.ForeignKey(
                        blank=True,
                        help_text="The requested domain",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="requested+",
                        to="registrar.website",
                    ),
                ),
                (
                    "submitter",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="submitted_applications",
                        to="registrar.contact",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "contact_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="registrar.contact",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("street1", models.TextField(blank=True)),
                ("street2", models.TextField(blank=True)),
                ("street3", models.TextField(blank=True)),
                ("city", models.TextField(blank=True)),
                ("sp", models.TextField(blank=True)),
                ("pc", models.TextField(blank=True)),
                ("cc", models.TextField(blank=True)),
                ("display_name", models.TextField()),
                (
                    "user",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("registrar.contact", models.Model),
        ),
    ]
