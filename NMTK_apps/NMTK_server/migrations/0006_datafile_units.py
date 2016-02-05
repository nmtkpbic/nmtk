# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('NMTK_server', '0005_auto_20160121_2045'),
    ]

    operations = [
        migrations.AddField(
            model_name='datafile',
            name='units',
            field=jsonfield.fields.JSONField(null=True, blank=True),
        ),
    ]
