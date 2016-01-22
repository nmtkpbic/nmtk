# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('NMTK_server', '0004_auto_20151124_1734'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.CharField(default=b'U', max_length=32, choices=[(b'U', b'Configuration Pending'), (b'A', b'Active'), (b'F', b'Failed'), (b'TF', b'Tool Failed to Accept Job'), (b'PP', b'Post-processing results'), (b'PF', b'Failed to process results'), (b'C', b'Complete')]),
        ),
    ]
