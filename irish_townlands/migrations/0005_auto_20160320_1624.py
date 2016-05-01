# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-20 16:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('irish_townlands', '0004_auto_20160320_1600'),
    ]

    operations = [
        migrations.AlterField(
            model_name='barony',
            name='osm_id',
            field=models.BigIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='civilparish',
            name='osm_id',
            field=models.BigIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='county',
            name='osm_id',
            field=models.BigIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='electoraldivision',
            name='osm_id',
            field=models.BigIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='polygon',
            name='osm_id',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='townland',
            name='osm_id',
            field=models.BigIntegerField(unique=True),
        ),
    ]