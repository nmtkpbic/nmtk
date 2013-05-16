NMTK
====

Non Motorized Transportation Tooklit

The Non Motorized Transportation Toolkit is a tool that facilitates the development and execution of 
non-motorized transportation models.

Installation Instructions
=========================

The installation of this tool is predicated on an understanding of basic systems administration skills, as well
as some knowledge surrounding configuring a web server (such as Apache.)

#.  Checkout the existing code and change into the root directory of the repository.
#.  Initialize a virtual environment, using a command such as::

    virtualenv venv

#.  Activate the virtual environment using the command::

    source venv/bin/activate

#.  Install the pip tool into the venv::

    easy_install pip

#.  Install all the pre-requsite modules::

   pip install -r requirements.txt

#.  Install the celery and Apache components, configuration files exist for these in the "celery" and "conf" directories (celery and apache, respectively)

#.  Change to the NMTK_apps subdirectory and initialize the database::

   python manage.py syncdb

#.  Verify that you can access things via the web - and add new tools, etc.
