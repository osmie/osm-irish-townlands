# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Metadata'
        db.create_table('irish_townlands_metadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('irish_townlands', ['Metadata'])

        # Adding model 'Barony'
        db.create_table('irish_townlands_barony', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('osm_id', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name_ga', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('alt_name', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('area_m2', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('url_path', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('unique_suffix', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('centre_x', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('centre_y', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('bbox_width', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('bbox_height', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('polygon_geojson', self.gf('django.db.models.fields.TextField')(default='')),
            ('county', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='baronies', null=True, to=orm['irish_townlands.County'])),
        ))
        db.send_create_signal('irish_townlands', ['Barony'])

        # Adding model 'CivilParish'
        db.create_table('irish_townlands_civilparish', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('osm_id', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name_ga', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('alt_name', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('area_m2', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('url_path', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('unique_suffix', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('centre_x', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('centre_y', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('bbox_width', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('bbox_height', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('polygon_geojson', self.gf('django.db.models.fields.TextField')(default='')),
            ('county', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='civil_parishes', null=True, to=orm['irish_townlands.County'])),
        ))
        db.send_create_signal('irish_townlands', ['CivilParish'])

        # Adding model 'County'
        db.create_table('irish_townlands_county', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('osm_id', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name_ga', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('alt_name', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('area_m2', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('url_path', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('unique_suffix', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('centre_x', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('centre_y', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('bbox_width', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('bbox_height', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('polygon_geojson', self.gf('django.db.models.fields.TextField')(default='')),
            ('polygon_townland_gaps', self.gf('django.db.models.fields.TextField')(default='')),
            ('polygon_townland_overlaps', self.gf('django.db.models.fields.TextField')(default='')),
            ('polygon_barony_gaps', self.gf('django.db.models.fields.TextField')(default='')),
            ('polygon_barony_overlaps', self.gf('django.db.models.fields.TextField')(default='')),
            ('polygon_civil_parish_gaps', self.gf('django.db.models.fields.TextField')(default='')),
            ('polygon_civil_parish_overlaps', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal('irish_townlands', ['County'])

        # Adding model 'Townland'
        db.create_table('irish_townlands_townland', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('osm_id', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name_ga', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('alt_name', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
            ('area_m2', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('url_path', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('unique_suffix', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('centre_x', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('centre_y', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('bbox_width', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('bbox_height', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('polygon_geojson', self.gf('django.db.models.fields.TextField')(default='')),
            ('county', self.gf('django.db.models.fields.related.ForeignKey')(related_name='townlands', null=True, to=orm['irish_townlands.County'])),
            ('barony', self.gf('django.db.models.fields.related.ForeignKey')(related_name='townlands', null=True, to=orm['irish_townlands.Barony'])),
            ('civil_parish', self.gf('django.db.models.fields.related.ForeignKey')(related_name='townlands', null=True, to=orm['irish_townlands.CivilParish'])),
        ))
        db.send_create_signal('irish_townlands', ['Townland'])

        # Adding model 'TownlandTouch'
        db.create_table('irish_townlands_townlandtouch', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('townland_a', self.gf('django.db.models.fields.related.ForeignKey')(related_name='touching_as_a', to=orm['irish_townlands.Townland'])),
            ('townland_b', self.gf('django.db.models.fields.related.ForeignKey')(related_name='touching_as_b', to=orm['irish_townlands.Townland'])),
            ('length_m', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('direction_radians', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('irish_townlands', ['TownlandTouch'])

        # Adding unique constraint on 'TownlandTouch', fields ['townland_a', 'townland_b']
        db.create_unique('irish_townlands_townlandtouch', ['townland_a_id', 'townland_b_id'])

        # Adding model 'Error'
        db.create_table('irish_townlands_error', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('irish_townlands', ['Error'])


    def backwards(self, orm):
        # Removing unique constraint on 'TownlandTouch', fields ['townland_a', 'townland_b']
        db.delete_unique('irish_townlands_townlandtouch', ['townland_a_id', 'townland_b_id'])

        # Deleting model 'Metadata'
        db.delete_table('irish_townlands_metadata')

        # Deleting model 'Barony'
        db.delete_table('irish_townlands_barony')

        # Deleting model 'CivilParish'
        db.delete_table('irish_townlands_civilparish')

        # Deleting model 'County'
        db.delete_table('irish_townlands_county')

        # Deleting model 'Townland'
        db.delete_table('irish_townlands_townland')

        # Deleting model 'TownlandTouch'
        db.delete_table('irish_townlands_townlandtouch')

        # Deleting model 'Error'
        db.delete_table('irish_townlands_error')


    models = {
        'irish_townlands.barony': {
            'Meta': {'object_name': 'Barony'},
            'alt_name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'area_m2': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'bbox_height': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'bbox_width': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'centre_x': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'centre_y': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'county': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'baronies'", 'null': 'True', 'to': "orm['irish_townlands.County']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name_ga': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'osm_id': ('django.db.models.fields.IntegerField', [], {}),
            'polygon_geojson': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'unique_suffix': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'irish_townlands.civilparish': {
            'Meta': {'object_name': 'CivilParish'},
            'alt_name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'area_m2': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'bbox_height': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'bbox_width': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'centre_x': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'centre_y': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'county': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'civil_parishes'", 'null': 'True', 'to': "orm['irish_townlands.County']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name_ga': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'osm_id': ('django.db.models.fields.IntegerField', [], {}),
            'polygon_geojson': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'unique_suffix': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'irish_townlands.county': {
            'Meta': {'object_name': 'County'},
            'alt_name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'area_m2': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'bbox_height': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'bbox_width': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'centre_x': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'centre_y': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name_ga': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'osm_id': ('django.db.models.fields.IntegerField', [], {}),
            'polygon_barony_gaps': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'polygon_barony_overlaps': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'polygon_civil_parish_gaps': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'polygon_civil_parish_overlaps': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'polygon_geojson': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'polygon_townland_gaps': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'polygon_townland_overlaps': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'unique_suffix': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'irish_townlands.error': {
            'Meta': {'object_name': 'Error'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {})
        },
        'irish_townlands.metadata': {
            'Meta': {'object_name': 'Metadata'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'irish_townlands.townland': {
            'Meta': {'object_name': 'Townland'},
            'alt_name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'area_m2': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'barony': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'townlands'", 'null': 'True', 'to': "orm['irish_townlands.Barony']"}),
            'bbox_height': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'bbox_width': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'centre_x': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'centre_y': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'civil_parish': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'townlands'", 'null': 'True', 'to': "orm['irish_townlands.CivilParish']"}),
            'county': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'townlands'", 'null': 'True', 'to': "orm['irish_townlands.County']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name_ga': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'osm_id': ('django.db.models.fields.IntegerField', [], {}),
            'polygon_geojson': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'unique_suffix': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'irish_townlands.townlandtouch': {
            'Meta': {'unique_together': "[('townland_a', 'townland_b')]", 'object_name': 'TownlandTouch'},
            'direction_radians': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length_m': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'townland_a': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'touching_as_a'", 'to': "orm['irish_townlands.Townland']"}),
            'townland_b': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'touching_as_b'", 'to': "orm['irish_townlands.Townland']"})
        }
    }

    complete_apps = ['irish_townlands']