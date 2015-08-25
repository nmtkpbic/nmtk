# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields
import NMTK_server.models
import jsonfield.fields
import django.db.models.deletion
from django.conf import settings
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(storage=NMTK_server.models.NMTKDataFileSystemStorage(location=b'/var/www/vhosts/nmtk-dev.gridgeo.com/nmtk_files/NMTK_server/files'), upload_to=NMTK_server.models.data_file_path)),
                ('processed_file', models.FileField(storage=NMTK_server.models.NMTKGeoJSONFileSystemStorage(location=b'/var/www/vhosts/nmtk-dev.gridgeo.com/nmtk_files/NMTK_server/files'), upload_to=NMTK_server.models.converted_data_file_path)),
                ('name', models.CharField(max_length=64)),
                ('type', models.CharField(default=b'source', max_length=10, choices=[(b'source', b'Candidate for Input'), (b'result', b'Results from Job'), (b'both', b'Result from Job, can be used for input')])),
                ('status', models.IntegerField(default=1, choices=[(1, b'Import Pending'), (2, b'File submitted for processing'), (3, b'Import Complete'), (4, b'Unrecognized Type'), (5, b'Import of Job Results Pending'), (6, b'Import of Job Results Failed'), (7, b'Import of Job Results Complete')])),
                ('status_message', models.TextField(null=True, blank=True)),
                ('srid', models.IntegerField(null=True, blank=True)),
                ('srs', models.TextField(null=True, blank=True)),
                ('feature_count', models.IntegerField(null=True, blank=True)),
                ('extent', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('geom_type', models.IntegerField(blank=True, null=True, choices=[(1, b'POINT'), (7, b'GEOMETRYCOLLECTION'), (2, b'LINESTRING'), (4, b'MULTIPOINT'), (6, b'MULTIPOLYGON'), (3, b'POLYGON'), (5, b'MULTILINESTRING'), (99, b'RASTER')])),
                ('description', models.TextField(null=True, blank=True)),
                ('content_type', models.CharField(max_length=128)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('fields', jsonfield.fields.JSONField(null=True, blank=True)),
                ('field_attributes', jsonfield.fields.JSONField(null=True, blank=True)),
                ('deleted', models.BooleanField(default=False)),
                ('result_field', models.CharField(max_length=32, null=True, blank=True)),
                ('result_field_units', models.CharField(max_length=64, null=True, blank=True)),
                ('model', models.FileField(storage=NMTK_server.models.NMTKResultsFileSystemStorage(location=b'/var/www/vhosts/nmtk-dev.gridgeo.com/nmtk_files/NMTK_server/files'), null=True, upload_to=NMTK_server.models.data_file_model_path, blank=True)),
                ('checksum', models.CharField(max_length=50)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_created'],
                'db_table': 'nmtk_data_file',
                'verbose_name': 'Data File',
                'verbose_name_plural': 'Data Files',
            },
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('uri', models.CharField(max_length=255)),
                ('comments', models.TextField()),
                ('transparency', models.CharField(max_length=16, null=True, choices=[(b'No Opinion', b'No Opinion'), (b'Works', b'Works'), (b'Needs Help', b'Needs Help'), (b'No Way', b'No Way')])),
                ('functionality', models.CharField(max_length=16, null=True, choices=[(b'No Opinion', b'No Opinion'), (b'Works', b'Works'), (b'Needs Help', b'Needs Help'), (b'No Way', b'No Way')])),
                ('usability', models.CharField(max_length=16, null=True, choices=[(b'No Opinion', b'No Opinion'), (b'Works', b'Works'), (b'Needs Help', b'Needs Help'), (b'No Way', b'No Way')])),
                ('performance', models.CharField(max_length=16, null=True, choices=[(b'No Opinion', b'No Opinion'), (b'Works', b'Works'), (b'Needs Help', b'Needs Help'), (b'No Way', b'No Way')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_created'],
                'db_table': 'nmtk_feedback',
                'verbose_name': 'Feedback',
                'verbose_name_plural': 'Feedback Items',
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('job_id', models.UUIDField(default=uuid.uuid4, serialize=False, primary_key=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default=b'U', max_length=32, choices=[(b'U', b'Configuration Pending'), (b'A', b'Active'), (b'F', b'Failed'), (b'TF', b'Tool Failed to Accept Job'), (b'PP', b'Post-processing results'), (b'PF', b'Post-processing of results failed'), (b'C', b'Complete')])),
                ('config', jsonfield.fields.JSONField(null=True)),
                ('description', models.CharField(help_text=b'A free-form description of this job', max_length=2048)),
                ('email', models.BooleanField(default=False, help_text=b'Email user upon job completion')),
            ],
            options={
                'ordering': ['-date_created'],
                'db_table': 'nmtk_job',
                'verbose_name': 'Job',
                'verbose_name_plural': 'Jobs',
            },
        ),
        migrations.CreateModel(
            name='JobFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('namespace', models.CharField(max_length=255)),
                ('datafile', models.ForeignKey(to='NMTK_server.DataFile', on_delete=django.db.models.deletion.PROTECT)),
                ('job', models.ForeignKey(to='NMTK_server.Job')),
            ],
            options={
                'db_table': 'nmtk_job_file',
            },
        ),
        migrations.CreateModel(
            name='JobStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('category', models.IntegerField(default=2, choices=[(1, b'Debug'), (2, b'Status'), (4, b'Message'), (5, b'Warning'), (6, b'Error'), (3, b'System')])),
                ('message', models.CharField(max_length=1024)),
                ('job', models.ForeignKey(to='NMTK_server.Job')),
            ],
            options={
                'ordering': ['job__pk', '-timestamp'],
                'db_table': 'nmtk_job_status',
                'verbose_name': 'Job Status',
                'verbose_name_plural': 'Job Status',
            },
        ),
        migrations.CreateModel(
            name='MapColorStyle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=16)),
                ('other_r', models.IntegerField(verbose_name=b'R', validators=[django.core.validators.MaxValueValidator(255), django.core.validators.MinValueValidator(0)])),
                ('other_g', models.IntegerField(verbose_name=b'G', validators=[django.core.validators.MaxValueValidator(255), django.core.validators.MinValueValidator(0)])),
                ('other_b', models.IntegerField(verbose_name=b'B', validators=[django.core.validators.MaxValueValidator(255), django.core.validators.MinValueValidator(0)])),
                ('default', models.BooleanField(default=False)),
                ('category', models.CharField(max_length=20, null=True)),
                ('ramp_graphic', models.ImageField(storage=NMTK_server.models.NMTKDataFileSystemStorage(location=b'/var/www/vhosts/nmtk-dev.gridgeo.com/nmtk_files/NMTK_server/files'), null=True, upload_to=NMTK_server.models.color_ramp_graphic_path, blank=True)),
            ],
            options={
                'db_table': 'nmtk_map_color_styles',
                'verbose_name': 'Map Color Style',
                'verbose_name_plural': 'Map Color Styles',
            },
        ),
        migrations.CreateModel(
            name='PageContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('content', models.TextField()),
                ('enabled', models.BooleanField(default=True)),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField(editable=False)),
            ],
            options={
                'ordering': ['order'],
                'db_table': 'nmtk_content',
            },
        ),
        migrations.CreateModel(
            name='PageName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'The name for the page this text belongs to', max_length=16)),
            ],
            options={
                'db_table': 'nmtk_pagename',
            },
        ),
        migrations.CreateModel(
            name='ResultsFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('primary', models.BooleanField(default=False)),
                ('datafile', models.ForeignKey(to='NMTK_server.DataFile', on_delete=django.db.models.deletion.PROTECT)),
                ('job', models.ForeignKey(to='NMTK_server.Job')),
            ],
            options={
                'db_table': 'nmtk_results_file',
            },
        ),
        migrations.CreateModel(
            name='Tool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'The name of the tool', max_length=64)),
                ('tool_path', models.CharField(help_text=b'The URL path for the tool', max_length=64)),
                ('active', models.BooleanField(default=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'nmtk_tool',
                'verbose_name': 'Tool',
                'verbose_name_plural': 'Tools',
            },
        ),
        migrations.CreateModel(
            name='ToolConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('json_config', jsonfield.fields.JSONField(default=dict)),
                ('tool', models.OneToOneField(to='NMTK_server.Tool')),
            ],
            options={
                'db_table': 'nmtk_tool_config',
                'verbose_name': 'Tool Configuration',
                'verbose_name_plural': 'Tool Configurations',
            },
        ),
        migrations.CreateModel(
            name='ToolSampleConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sample_config', jsonfield.fields.JSONField(default=dict)),
                ('tool', models.OneToOneField(to='NMTK_server.Tool')),
            ],
            options={
                'db_table': 'nmtk_tool_sample_config',
                'verbose_name': 'Tool Sample Configuration',
                'verbose_name_plural': 'Tool Sample Configurations',
            },
        ),
        migrations.CreateModel(
            name='ToolSampleFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('namespace', models.CharField(max_length=32)),
                ('file', models.FileField(storage=NMTK_server.models.NMTKDataFileSystemStorage(location=b'/var/www/vhosts/nmtk-dev.gridgeo.com/nmtk_files/NMTK_server/files'), upload_to=NMTK_server.models.tool_sample_file_path)),
                ('checksum', models.CharField(max_length=50)),
                ('content_type', models.CharField(max_length=64, null=True)),
                ('tool', models.ForeignKey(to='NMTK_server.Tool')),
            ],
            options={
                'db_table': 'nmtk_tool_sample_file',
                'verbose_name': 'Tool Sample File',
                'verbose_name_plural': 'Tool Sample Files',
            },
        ),
        migrations.CreateModel(
            name='ToolServer',
            fields=[
                ('name', models.CharField(help_text=b'A descriptive name for this tool server.', max_length=64)),
                ('tool_server_id', models.UUIDField(default=uuid.uuid4, serialize=False, primary_key=True)),
                ('contact', models.EmailField(max_length=254, null=True)),
                ('auth_token', models.CharField(default=NMTK_server.models.generate_auth_token_string, max_length=50)),
                ('remote_ip', NMTK_server.models.IPAddressFieldNullable(help_text=b'The IP where the tool resides so we can verify the request source IP as well if needed', null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('verify_ssl', models.BooleanField(default=True)),
                ('server_url', models.URLField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'nmtk_tool_server',
                'verbose_name': 'Tool Server',
                'verbose_name_plural': 'Tool Servers',
            },
        ),
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('config', models.TextField(help_text=b'A JSON encoded string containing user preferences')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'nmtk_user_preference',
                'verbose_name': 'User Preference',
                'verbose_name_plural': 'User Preferences',
            },
        ),
        migrations.AddField(
            model_name='tool',
            name='tool_server',
            field=models.ForeignKey(to='NMTK_server.ToolServer'),
        ),
        migrations.AddField(
            model_name='pagecontent',
            name='page',
            field=models.ForeignKey(to='NMTK_server.PageName'),
        ),
        migrations.AddField(
            model_name='job',
            name='job_files',
            field=models.ManyToManyField(related_name='job_files', through='NMTK_server.JobFile', to='NMTK_server.DataFile'),
        ),
        migrations.AddField(
            model_name='job',
            name='results_files',
            field=models.ManyToManyField(related_name='results', through='NMTK_server.ResultsFile', to='NMTK_server.DataFile'),
        ),
        migrations.AddField(
            model_name='job',
            name='tool',
            field=models.ForeignKey(to='NMTK_server.Tool', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='job',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
