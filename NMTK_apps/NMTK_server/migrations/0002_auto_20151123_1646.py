# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import NMTK_server.models


class Migration(migrations.Migration):

    dependencies = [
        ('NMTK_server', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='file',
            field=models.FileField(storage=NMTK_server.models.NMTKDataFileSystemStorage(location=b'/var/www/vhosts/nmtk.gridgeo.com/nmtk_files/NMTK_server/files'), upload_to=NMTK_server.models.data_file_path),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='model',
            field=models.FileField(storage=NMTK_server.models.NMTKResultsFileSystemStorage(location=b'/var/www/vhosts/nmtk.gridgeo.com/nmtk_files/NMTK_server/files'), null=True, upload_to=NMTK_server.models.data_file_model_path, blank=True),
        ),
        migrations.AlterField(
            model_name='datafile',
            name='processed_file',
            field=models.FileField(storage=NMTK_server.models.NMTKGeoJSONFileSystemStorage(location=b'/var/www/vhosts/nmtk.gridgeo.com/nmtk_files/NMTK_server/files'), upload_to=NMTK_server.models.converted_data_file_path),
        ),
        migrations.AlterField(
            model_name='job',
            name='job_id',
            field=models.UUIDField(serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='mapcolorstyle',
            name='ramp_graphic',
            field=models.ImageField(storage=NMTK_server.models.NMTKDataFileSystemStorage(location=b'/var/www/vhosts/nmtk.gridgeo.com/nmtk_files/NMTK_server/files'), null=True, upload_to=NMTK_server.models.color_ramp_graphic_path, blank=True),
        ),
        migrations.AlterField(
            model_name='toolsamplefile',
            name='file',
            field=models.FileField(storage=NMTK_server.models.NMTKDataFileSystemStorage(location=b'/var/www/vhosts/nmtk.gridgeo.com/nmtk_files/NMTK_server/files'), upload_to=NMTK_server.models.tool_sample_file_path),
        ),
        migrations.AlterField(
            model_name='toolserver',
            name='tool_server_id',
            field=models.UUIDField(serialize=False, primary_key=True),
        ),
    ]
