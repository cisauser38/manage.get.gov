# Generated by Django 4.2.1 on 2023-06-09 16:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registrar", "0026_alter_domainapplication_address_line2_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domaininformation",
            name="address_line1",
            field=models.TextField(
                blank=True,
                help_text="Street address",
                null=True,
                verbose_name="Street address",
            ),
        ),
        migrations.AlterField(
            model_name="domaininformation",
            name="address_line2",
            field=models.TextField(
                blank=True,
                help_text="Street address line 2",
                null=True,
                verbose_name="Street address line 2",
            ),
        ),
        migrations.AlterField(
            model_name="domaininformation",
            name="state_territory",
            field=models.CharField(
                blank=True,
                help_text="State, territory, or military post",
                max_length=2,
                null=True,
                verbose_name="State, territory, or military post",
            ),
        ),
        migrations.AlterField(
            model_name="domaininformation",
            name="urbanization",
            field=models.TextField(
                blank=True,
                verbose_name="Urbanization (Puerto Rico only)",
                null=True,
                verbose_name="Urbanization (Puerto Rico only)",
            ),
        ),
    ]
