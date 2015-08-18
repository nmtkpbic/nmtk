'''
Management command to generate a checksum for a data file, in a format 
that the NMTK server will be able to match.
'''

import hashlib
import hmac
import os
from django.core.management.base import BaseCommand, CommandError
import sys


class Command(BaseCommand):
    help = 'Given the path to a file, generate a HMAC checksum for the file (suitable for use with a tool config)'

    def handle(self, *args, **options):
        if not (os.path.exists(args[0])):
            print "File {0} not found (you might need to provide a full path to the file)".format(os.path.join(os.getcwd(), args[0]))
        target_filename = args[0]
        checksum = hashlib.sha1()
        chunk_size = 1024
        with open(target_filename, 'r') as checksum_file:
            while True:
                data = checksum_file.read(chunk_size)
                if not data:
                    break
                checksum.update(data)

        print 'The computed checksum is: {0}'.format(checksum.hexdigest())
        print "This should match the output of the command: sha1sum {0}".format(target_filename)
