# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import NMTK_server.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('NMTK_server', '0002_auto_20151123_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='tool',
            name='authorized_users',
            field=models.ManyToManyField(related_name='authorized_tools', db_table=b'tool_authorized_users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='toolserver',
            name='authorized_users',
            field=models.ManyToManyField(related_name='authorized_tool_servers', db_table=b'tool_server_authorized_users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='file',
            field=models.FileField(storage=NMTK_server.models.NMTKDataFileSystemStorage(), upload_to=NMTK_server.models.data_file_path),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='model',
            field=models.FileField(storage=NMTK_server.models.NMTKResultsFileSystemStorage(), null=True, upload_to=NMTK_server.models.data_file_model_path, blank=True),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='processed_file',
            field=models.FileField(storage=NMTK_server.models.NMTKGeoJSONFileSystemStorage(), upload_to=NMTK_server.models.converted_data_file_path),
        ),
        migrations.AlterField(
            model_name='mapcolorstyle',
            name='ramp_graphic',
            field=models.ImageField(storage=NMTK_server.models.NMTKDataFileSystemStorage(), null=True, upload_to=NMTK_server.models.color_ramp_graphic_path, blank=True),
        ),
        migrations.AlterField(
            model_name='toolsamplefile',
            name='file',
            field=models.FileField(storage=NMTK_server.models.NMTKDataFileSystemStorage(), upload_to=NMTK_server.models.tool_sample_file_path),
        ),
    ]
