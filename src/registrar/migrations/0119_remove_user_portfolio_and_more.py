# Generated by Django 4.2.10 on 2024-08-19 20:24

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("registrar", "0118_alter_portfolio_options_alter_portfolio_creator_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="portfolio",
        ),
        migrations.RemoveField(
            model_name="user",
            name="portfolio_additional_permissions",
        ),
        migrations.RemoveField(
            model_name="user",
            name="portfolio_roles",
        ),
        migrations.AddField(
            model_name="user",
            name="last_selected_portfolio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="portfolio_selected_by_users",
                to="registrar.portfolio",
            ),
        ),
        migrations.CreateModel(
            name="UserPortfolioPermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "roles",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ("organization_admin", "Admin"),
                                ("organization_admin_read_only", "Admin read only"),
                                ("organization_member", "Member"),
                            ],
                            max_length=50,
                        ),
                        blank=True,
                        help_text="Select one or more roles.",
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "additional_permissions",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ("view_all_domains", "View all domains and domain reports"),
                                ("view_managed_domains", "View managed domains"),
                                ("view_member", "View members"),
                                ("edit_member", "Create and edit members"),
                                ("view_all_requests", "View all requests"),
                                ("view_created_requests", "View created requests"),
                                ("edit_requests", "Create and edit requests"),
                                ("view_portfolio", "View organization"),
                                ("edit_portfolio", "Edit organization"),
                                ("view_suborganization", "View suborganization"),
                                ("edit_suborganization", "Edit suborganization"),
                            ],
                            max_length=50,
                        ),
                        blank=True,
                        help_text="Select one or more additional permissions.",
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "portfolio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="portfolio_users",
                        to="registrar.portfolio",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="portfolio_permissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "portfolio")},
            },
        ),
    ]
