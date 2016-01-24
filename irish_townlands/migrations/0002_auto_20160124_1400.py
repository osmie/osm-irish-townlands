# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('irish_townlands', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='barony',
            name='name_griffithsvaluation_tag',
            field=models.CharField(default=None, max_length=255, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='civilparish',
            name='name_griffithsvaluation_tag',
            field=models.CharField(default=None, max_length=255, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='county',
            name='name_griffithsvaluation_tag',
            field=models.CharField(default=None, max_length=255, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='electoraldivision',
            name='name_griffithsvaluation_tag',
            field=models.CharField(default=None, max_length=255, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='subtownland',
            name='name_griffithsvaluation_tag',
            field=models.CharField(default=None, max_length=255, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='townland',
            name='name_griffithsvaluation_tag',
            field=models.CharField(default=None, max_length=255, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='civilparish',
            name='counties',
            field=models.ManyToManyField(default=None, related_name='civil_parishes', to='irish_townlands.County', db_index=True),
        ),
    ]
