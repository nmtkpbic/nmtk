NMTK
====

Non Motorized Transportation Tooklit

The Non Motorized Transportation Toolkit is a tool that facilitates the development and execution of 
non-motorized transportation models.


==============
Pre-Requisites
==============

There are some pre-requisites that should be installed, the assumption in this case is that you are using debian, but 
these pre-reqs (and their install packages) translate easily (try google) to numerous other OSs::

 * apache2
 * python-dev
 * python-setuptools
 * python-virtualenv
 * r-base
 * libapache2-mod-wsgi
 * libxslt-dev libxml2-dev
 * libspatialite3 libspatialite-dev spatialite-bin

You must also download, compile, and install (from source) GDAL version 1.10 or greater.  GDAL v1.10 added
support for CRS values in GeoJSON files - which are a requirement for NMTK.  Also, please note
that when compiling, be sure to provide the --with-python argument.

These directions assume that you install GDAL source in /usr/local/src/gdal-1.10.0 (you may need to change
the directions below if you installed the source elsewhere.)

These directions also assume that you have placed the GDAL components in /usr/local/lib , if not, you will need
to modify NMTK_apps/manage.py and NMTK_apps/NMTK_apps/wsgi.py with the appropriate locations, otherwise GDAL
specific operations will fail (due to the library not being found.)


Installation Instructions
=========================

The installation of this tool is predicated on an understanding of basic systems administration skills, as well
as some knowledge surrounding configuring a web server (such as Apache.)

 1.  Checkout the existing code and change into the root directory of the repository.
 2.  Initialize a virtual environment, using a command such as::

    virtualenv venv

 3.  Activate the virtual environment using the command::

    source venv/bin/activate

 4.  Install numpy by hand using requirements.txt (pip gets it wrong for some reason otherwise...)::

   pip install $(cat requirements.txt|grep -i ^numpy)

 5.  Install all the pre-requsite modules::

   pip install -r requirements.txt

  Note::
  
  Sometimes the GDAL installation will fail because pip gets the bindings, but not the entire GDAL library (which GDALs setup requires.)  This
  can be handled using the following procedure::
    
    pip install --no-install $(grep GDAL requirements.txt)
    pushd venv/build/GDAL
    python setup.py build_ext --include-dirs=/usr/local/include --library-dirs=/usr/local/lib
    pip install --no-download GDAL
    popd
    sudo sh -c 'echo "/usr/local/lib" >> /etc/ld.so.conf' # Add the path to gdal libs to system
    sudo ldconfig
    
   Note::
   
   The PySqlite Library requires some special handling::
   
     pip uninstall pysqlite # Answer yes when prompted
     pip install --no-install $(grep pysqlite requirements.txt)
     pushd venv/build/pysqlite/
     vi setup.cfg # Comment out the line that contains define=SQLITE_OMIT_LOAD_EXTENSION
                  # By putting a # at the start of the line
     pip install --no-download pysqlite
     
     

 6.  Install the celery and Apache components, configuration files exist for 
 these in the "celery" and "conf" directories (celery and apache, respectively)
 
 7.  By default, files for the NMTK server will go in the nmtk_files subdirectory,
 create this directory if it does not exist, and ensure that you have write access to it::
 
     mkdir nmtk_files
     chown www-data.${USER} nmtk_files
     chmod g+rwxs nmtk_files
     
 
 7a. Create the initial spatialite database::
     
     pushd nmtk_files
     spatialite nmtk.sqlite  "SELECT InitSpatialMetaData();"
     # Note: Ignore the "table spatial_ref_sys already exists error"
     chown www-data nmtk.sqlite
 
 8.  Change to the NMTK_apps subdirectory and initialize the database, and generate static media::

   pushd NMTK_apps
   python manage.py syncdb
   python manage.py collectstatic
   popd

 9.  Change the nmtk_files subdirectory so that it, and all it's subdirectories,
 are writeable by the www-data user (or whatever user the web server runs as.)::
 
   chown -R nmtk_files www-data.www-data

 10.  Change the database and log locations so that the apache user will be able to access/write to them::

  sudo chown -R www-data logs
  sudo chmod g+rwxs logs
  sudo g+rw logs/*

 11.  Now ensure that the sample fixture data is correct - you need not load this,
     and it will probably go away eventually, but it provides a "default" config
     for the purposes of having a server communicate with the default client.
     
  edit NMTK_apps/NMTK_server/fixtures/initial_data.json
  
    - in particular, ensure the host name there is correct.
     
 12.  Restart your apache server
 
 13.  Run the discover_tools command to discover new tools, and remove no-longer
      valid/published tools::
    
     python manage.py discover_tools   
     
 14.  Edit NMTK_apps/NMTK_apps/settings.py and change the SECRET_KEY and any
 references to hostnames (based on the virtual hostname of your system.)
