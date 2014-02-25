'''
This module is designed to handle some account loading - basically, when
a new account is generated, a signal will call the setupAccount function, which
should take the account information and use it to perform some basic setup steps -
basically loading a base data file into the account.

Ideally, this would be called after the account is activated, since at that time 
we know that the account is real.  If we do it any other way, then we run into
issues with regard to this being used as a vector for DOS attacks.

Chander Ganesan <chander@otg-nc.com> / http://www.otg-nc.com
'''
import os
from django.core.files import File
from django.core.files.base import ContentFile

cdir=os.path.dirname(__file__)
# files=[('ALX.geojson', 
#         'Alexandria, VA Data Suitable for the Minnesota Models',
#         'application/json',),
#        ('SF_for_Model_4326.geojson',
#         'San Francisco Sample Data (for San Francisco Models)',
#         'application/json')]
files=[]

def setupAccount(user):
    from NMTK_server import models
    '''
    Pass an instance of the user object in to the function
    '''
    for filename, desc, content_type in files:
        f=File(open(os.path.join(cdir, filename)))
        df=models.DataFile(user=user,
                           description=desc,
                           name=filename,
                           content_type=content_type)
        df.file.save(filename, f)