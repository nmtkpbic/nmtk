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
    
      
 8.  Edit NMTK_apps/NMTK_apps/settings.py and change the SECRET_KEY, SITE_DOMAIN and any
 references to hostnames (based on the virtual hostname of your system.)
 
 9.  Change to the NMTK_apps subdirectory and initialize the database, and generate static media::

   pushd NMTK_apps
   python manage.py syncdb # Note: Here you should create an administrative user for yourself
   python manage.py collectstatic
   popd

 10.  Change the nmtk_files subdirectory so that it, and all it's subdirectories,
 are writeable by the www-data user (or whatever user the web server runs as.)::
 
   chown -R nmtk_files www-data.www-data

 11.  Change the database and log locations so that the apache user will be able to access/write to them::

  sudo chown -R www-data logs
  sudo chmod g+rwxs logs
  sudo g+rw logs/*

 12.  Now ensure that the sample fixture data is correct - you need not load this,
     and it will probably go away eventually, but it provides a "default" config
     for the purposes of having a server communicate with the default client.
     
  edit NMTK_apps/NMTK_server/fixtures/initial_data.json
  
    - in particular, ensure the host name there is correct.
     
 13.  Change the SECRET_KEY value in NMTK_apps/NMTK_apps/settings.py to 
      be unique for your installation.  The SECRET_KEY is used for various 
      hashing operations, and needs to be different for each site (for security
      reasons.)
 
 14.  Restart your apache server
 
 15.  Run the discover_tools command to discover new tools, and remove no-longer
      valid/published tools::
    
     python manage.py discover_tools   
     
The remainder of configuration (such as removing the default tool server and/or
adding a new tool server) can now be done via the Administrative pages of the 
application - via the web.

To add a new tool::
 
Here we will assume the NMTK server "base" URL is is http://nmtk.otg-nc.com)::

0.  Ensure your tool server is working (accepting requests via the web) 
    otherwise adding it will be a futile task, since the server will immediately 
    try to query the tool server for a list of tools it provides.
    
1.  Open your browser and point to the administrative page of the server::

  http://nmtk.otg-nc.com/server/admin

2.  Login using the credentials you created in step 9 (above)

3.  Click on "Tool Servers"

4.  If you wish to not use the "default" tools, then click the check box next 
	to the "Sample tool server", choose "delete" from the drop down, and 
	press "Go" to delete the tool server.  Note that deleting the tool server 
	will also delete all associated tools supplied by that server.

5.  To add a new tool server, click on "Add Tool Server" (upper right of the page.)

6.  Give your tool server a sensible name, and provide it with a URL (the url
for the tool server.)  Note that the URL with "/index" appended should return a
list of the available tools as a JSON string.  

7.  Copy the "auth token", which is the key used to sign requests between the 
	NMTK server and tool server.  This is commonly referred to as a 
	"shared secret" and is used to authenticate requests between the NMTK
	server and tool server.  You will need to share it with the tool server
	admin.

8.  Click "Save" to add the tool server (the NMTK server will immediately go 
	out and query the tool server to get a list of tools!)

9.  Copy the tool server ID that appears on the "Tool Servers" admin page
    and provide it, along with the shared secret you got in step 7 to the
    maintainer of the tool server.  You should also provide the tool admin
    the URL for the NMTK server.
    
Using the NMTK provided tool server::

If you are using the NMTK provided tool server, you'll need to get a set of
credentials (auth token and a tool server ID) from the NMTK server administrator.

Once you have these credentials, open up NMTK_apps/NMTK_apps/settings.py and
scroll to the end of the file.

Add a new entry to the NMTK_SERVERS= dictionary.  The key should be
the tool server ID (as provided by the NMTK server admin).  The value
should be another dictionary with two keys:

 - url - The URL for the NMTK server
 - secret - The "shared secret" (also called "auth key") provided by the NMTK 
            server administrator.
            
Restart apache to ensure these settings are reloaded and the tool will properly
accept and respond to authenticated requests from the tool server.

Note: If you wish to re-discover tools that an NMTK server provides, you have 
two options::
  * python manage.py discover_tools
      - This command will re-discover the provided tools for each tool server
        that is configured.
  * Return to the admin page, edit the tool server you wish to refresh, and hit
    "save" (no need to make any changes, the act of saving will kick off a 
    refresh for the tools provided by that tool server.)
