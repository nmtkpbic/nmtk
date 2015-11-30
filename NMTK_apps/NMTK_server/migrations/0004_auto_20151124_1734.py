# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('NMTK_server', '0003_auto_20151124_1052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tool',
            name='authorized_users',
            field=models.ManyToManyField(help_text=b'To make this available to all users, make sure no users are selected.  Otherwise, select only those users that should have access to this tool Note: Changes to the tool server list of allowed users will NOT effect this, and changes made here may override changes at the tool server level restrictions.', related_name='authorized_tools', db_table=b'tool_authorized_users', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='toolserver',
            name='authorized_users',
            field=models.ManyToManyField(help_text=b'To make this available to all users, make sure no users are selected.  Otherwise, select only those users that should have access to tools provided by this tool server.  Note: This sets the default users that can view all tools for new tools discovered on this tool server, changes here will NOT overwrite any existing per-tool user restrictions (or lack thereof.)', related_name='authorized_tool_servers', db_table=b'tool_server_authorized_users', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
