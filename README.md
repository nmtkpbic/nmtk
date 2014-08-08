Non-Motorized Toolkit
Copyright (c) 2014 Open Technology Group Inc. (A North Carolina Corporation)
Developed under Federal Highway Administration (FHWA) Contracts:
DTFH61-12-P-00147 and DTFH61-14-P-00108

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright notice, 
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright 
      notice, this list of conditions and the following disclaimer 
      in the documentation and/or other materials provided with the distribution.
    * Neither the name of the Open Technology Group, the name of the 
      Federal Highway Administration (FHWA), nor the names of any 
      other contributors may be used to endorse or promote products 
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
Open Technology Group Inc BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF 
USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT 
OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


### NMTK

Non Motorized Travel Analysis Toolkit

The Non Motorized Travel Analysis Toolkit is a tool that facilitates the 
development and execution of non-motorized transportation models.

## System Requirements

While the NMTK Server/Tool Server(s) may run on systems with less resources than
those specified in the recommendations below, doing so is likely to result in
degraded performance.

  * 1 GB Physical memory (on systems running only the NMTK systems.)
  * A Minimum of 2 GB RAM+Swap
  
Note: There are no specific CPU requirements, but it is recommended that systems
      running the NMTK Server contain a CPU produced after 2010.

The NMTK architecture uses an asychnronous processing model that submits "jobs"
for execution in the background, then returns results to the user when those
jobs are complete.  As a result, the lower the system specifications/performance
the longer the user would have to potentially wait for a response.

NMTK compatible tools will vary with respect to computational resources required;
refer to tool documentation for any tool-specific system requirements.

## Version requirements

The current NMTK relies on specific versions of various software components, so it is
important to ensure that the versions of software that you are using meet these
minimum requirements (generally, newer versions are acceptable, but might require
additional testing to ensure they are compatible.)  Using an older (and in some
cases, a newer) version than what is recommended may not result in an immediately
visible incompatibility, but may fail in certain use cases.

- GDAL 1.10 or later
- MapServer 6.1 or later
- Spatialite 3 or later
- mod_wsgi 3.3 or later
- Python 2.7 or later

Note that many of the python components installed in the Virtual Environment
specify required version information, for that reason they are not listed here.

Refer to the requirements.txt file in the repository root for details about
python sub-component requirements.

## Installation Instructions

The installation instructions below are tested and work on Ubuntu 14.02 LTS.  Other
distributions may require different packages or steps to satisfy NMTK pre-requisites;
and may require different steps to perform installation (such as installing celery
daemons, Apache configuration files, etc.)

### Pre-Requisites

There are some pre-requisites that should be installed at the system level.  You may
wish to install additional suggested packages (such as documentation) related to each
of these, but doing so is unnecessary simply to run the NMTK system.  The assumption
in this case is that you are using Debian Linux or one of its derivatives such as
Ubuntu, but these pre-requisites (and their install packages) are commonly available
for other operating systems:

 * build-essentials
 * git
 * apache2
 * python-dev
 * python-setuptools
 * python-virtualenv
 * libapache2-mod-wsgi
 * libxslt-dev libxml2-dev
 * libspatialite5 libspatialite-dev spatialite-bin
 * libgd2-xpm-dev
 * libproj-dev
 * libfreetype6-dev
 * cgi-mapserver
 * libgdal-dev gdal-bin
 * gfortran libopenblas-dev liblapack-dev

You may also need to download, compile, and install (from source) GDAL version 1.10
or greater if your operating system does not provide a version greater than 1.10.
Ubuntu 14.04 LTS does provide a suitable GDAL version.  GDAL v1.10 added support for
CRS values in GeoJSON files - which are a requirement for NMTK.  Also, should you
compile GDAL locally, you should be sure to provide the --with-python argument and
that the location of the installed files is correctly recognized.

#### Optional Installs

Currently NMTK does not use these components, but it's likely that some tools and/or
the server may use these in the future.  Strictly speaking they are not a current
pre-requisite, but it may be useful to install these:

  * R (follow instructions here: http://cran.r-project.org/bin/linux/ubuntu/README)

### Configuring Swap Space

If your system has less than 2 GB of RAM, it is recommended that you set up
a swap space of at least 2 GB.  This can be done using the following commands:

  1.  First, compute the number of "blocks" required to allocate swap space of the
	  size you want/need.  In the instructions below, each block is set to 1 megabyte
	  (1024 x 1024) in size, there are 1024MB in 1 gigabyte.  So a 2 gigabyte swap
	  composed of 1 MB blocks would replace $COUNT with 2048.

  2.  Run the commands below to allocate the swap space.

    ```
    sudo dd if=/dev/zero of=/swapfile bs=$((1024*1024)) count=$COUNT
    sudo mkswap /swapfile
    # Add a line to the end of /etc/fstab so the swap will be available after a reboot
    sudo sed -i '$ a /swapfile       none    swap    sw      0       0 ' /etc/fstab
    # Enable the newly allocated swap space
    sudo swapon -a
    ```
    
  3.  Use the command "swapon -s" to verify that the swap file you created is in use.

###Installation Instructions

The installation of this tool expects you to have an understanding of basic systems
administration skills, as well as some knowledge surrounding configuring a web server
(such as Apache.)

The instructions below presume that you are logged in to a non-root account ($USER)
that has "sudo" privileges (e.g. in Ubuntu, by assigning $USER to the the "sudoers"
group).  While the instructions may be performed from a root account, doing so runs
the risk of inadvertently leaving security holes.

 1.  Checkout the existing code and change into the root directory of the repository.
     It is recommended that you use the commands below to accomplish this task:

  ```
  sudo mkdir -p /var/www/vhosts/$(hostname --fqdn)
  sudo chown $USER /var/www/vhosts/$(hostname --fqdn)
  # If you have an ssh key installed for GIT, use this command
  git clone git@github.com:chander/nmtk.git /var/www/vhosts/$(hostname --fqdn)
  # To download the repo using your userid/password, use this command
  git clone https://github.com/chander/nmtk.git /var/www/vhosts/$(hostname --fqdn)
  ```
  
 2.  Initialize a virtual environment, using a command such as:

  ```
  pushd /var/www/vhosts/$(hostname --fqdn)
  virtualenv venv
  ```

 3.  Activate the virtual environment using the command:

  ```
  source venv/bin/activate
  ```

 4.  Install numpy and pysqlite by hand using requirements.txt (pip gets it wrong for
     some reason otherwise...):

  ```
  pip install $(cat requirements.txt|grep -i ^numpy)
  pip install --no-install $(grep pysqlite requirements.txt)
  sed -i "s/define=SQLITE_OMIT_LOAD_EXTENSION/#define=SQLITE_OMIT_LOAD_EXTENSION/g" venv/build/pysqlite/setup.cfg
  pip install --no-download pysqlite 
  ```

 5.  Install all the pre-requisite modules (adjust the include paths to point at
     GDAL, especially if you compiled and installed it manually:

  ```
  CPLUS_INCLUDE_PATH=/usr/include/gdal C_INCLUDE_PATH=/usr/include/gdal pip install -r requirements.txt
  ```

  ###### Note
  
  Sometimes the GDAL installation will still fail because pip gets the bindings, but not the entire 
  GDAL library (which GDAL's setup requires.)  This can be handled using the following procedure:

  ```    
  pip install --no-install $(grep GDAL requirements.txt)
  pushd venv/build/GDAL
  python setup.py build_ext --include-dirs=/usr/include/gdal --library-dirs=/usr/lib/gdal
  pip install --no-download GDAL
  popd
  sudo sh -c 'echo "/usr/local/lib" >> /etc/ld.so.conf' # Add the path to gdal libs to system
  sudo ldconfig
  ```
     
 6.  Copy the sample settings file to your own local settings, and edit the required local
     setup parameters according to the instructions in the file:

  ```
  pushd NMTK_apps/NMTK_apps
  cp local_settings.sample local_settings.py
  # edit local_settings.py per instructions contained within using your favorite editor
  # e.g:  nano local_settings.py
  popd
  ```

***
### NMTK Toolkit Modes of Operation

This repository contains two distinct components of the NMTK system, which (by default)
are integrated into a single installation::

  - The NMTK Server and UI components provide the "user facing" components to the
    NMTK system.  These components manage user preferences and data, and coordinate
    configuration and sending tasks to individual NMTK servers for processing.
    
  - The NMTK Tool Server has no UI components, and is not designed to operate as
    a "user facing" service.  Instead, it is designed to be accessed by an NMTK
    Server, which will submit jobs to it (and coordinate the work that the 
    NMTK Tool Server does.)  
    
By default, the NMTK Server and the NMTK Tool Server are enabled, providing
the user that installs this software an NMTK Server and UI, as well as a
set of "Reference Implementation" tools that can be used to exercise/demonstrate
the system.

In the local_settings.py file there are two settings that control this:

  1.  The NMTK_SERVER variable, when set to "True" enables the NMTK Server
      and UI components, as well as the administrative pages for NMTK Server.
  2.  The TOOL_SERVER variable, when set to "True" enables the "reference
      implementation" set of tools, allowing a user to run the system with
      some basic pre-set tools.

If both NMTK_SERVER and TOOL_SERVER are set to "False", then no services will be
provided - this is not a recommended configuration (for obvious reasons.)

If either of these settings are changed, the administrator should re-install the
system, as certain components/dependencies may be missing, or "extraneous"
data that should be purged.

It should be noted that if the NMTK_SERVER is enabled, and the TOOL_SERVER is not,
then the reference set of tools will not be present.  In such cases the administrator
would need to add one or more tool servers in order to have an available set of tools.

It should also be noted that the unit tests (to validate an installation) rely on 
both the NMTK_SERVER and TOOL_SERVER being enabled.  If either is not enabled,
then the test suite will fail to execute successfully.

The two settings (NMTK_SERVER and TOOL_SERVER) work by omitting the Django applications
that are relevant to the two (the design is such that the Tool Server components reside in one
set of applications, and the NMTK Server components reside in another set.)


***     
### Note

> The steps below allow you to manually complete the remainder of the installation.
> However, a script exists (install.sh) that will perform these tasks for you.

> On development sites the install.sh script is typically used to "reset" the server,
> running it on a non-development server (where you have real data) will cause
> the catastrophic loss of data.  You should be cautious as to when/where you run
> install.sh

***

 1.  Install the celery components, a configuration file and init script exists for 
     this in the "celery" directory (celery and apache, respectively), 
     you will need to make several changes:
     
       * Modify celeryd-nmtk.default to contain the path to the NMTK installation.
         this file may then be copied to /etc/default/celeryd-nmtk
       * Copy the celeryd-nmtk.init script to /etc/init.d/celeryd-nmtk
       * Use the appropriate linux commands to ensure that the celery daemon
         is started when the server boots (sudo update-rc.d celeryd-nmtk-dev 
         defaults) 
 
 2.  By default, files for the NMTK server will go in the nmtk_files subdirectory,
     create this directory if it does not exist, and ensure that you have write 
     access to it:
 
  ```
  mkdir nmtk_files
  chown www-data.${USER} nmtk_files
  chmod g+rwxs nmtk_files
  ```
 
 3. Create the initial spatialite database:
     
  ```
  pushd nmtk_files
  spatialite nmtk.sqlite  "SELECT InitSpatialMetaData();"
  # Note: Ignore the "table spatial_ref_sys already exists error"
  chown www-data nmtk.sqlite
  ``` 
     
 5.  Now ensure that the sample fixture data is correct - you need not load this,
     and it will probably go away eventually, but it provides a "default" config
     for the purposes of having a server communicate with the default client.  It's likely
     that you will need to changed the server URL contained in the file to match
     that of your NMTK tool server.

  ```     
  vi NMTK_apps/NMTK_server/fixtures/initial_data.json
  ```
      
 6.  Change to the NMTK_apps subdirectory and initialize the database, and generate static media:

  ```
  pushd NMTK_apps
  python manage.py syncdb # Note: Here you should create an administrative user for yourself
  python manage.py minify # Needed if running in production
  python manage.py collectstatic  # Add -l to this for development systems, -c for production
  popd
  ```

 7.  Change the nmtk_files subdirectory so that it, and all it's subdirectories,
 are writeable by the www-data user (or whatever user the web server runs as.):

  ``` 
  chown -R nmtk_files www-data.www-data
  ```

 8.  Change the database and log locations so that the apache user will be able to access/write to them:

  ```
  sudo chown -R www-data logs
  sudo chmod g+rwxs logs
  sudo g+rw logs/*
  ```

     
 9.  Run the "python manage.py syncdb" command.  This will populate the initial
     database and get things so they are ready to run.  
 
 10.  Restart your apache server
 
 11.  Run the discover_tools command to discover new tools, and remove no-longer
      valid/published tools:

  ```    
  python manage.py discover_tools   
  ```
     
 12.  It is likely you will want to have a superuser you can use to administer 
      the server, this can be done using the following command, then following
      the prompts:
      
  ```
  python manage.py createsuperuser
  ```    
 
Minification/Optimization of UI Components
------------------------------------------
To speed the system and reduce bandwidth consumption when interacting with the NMTK system through its
built-in UI, it is recommended that the Javascript be "minified". However, the Javascript should not be
minified if you plan to work on the UI code for some reason.  Follow these steps to minify:

1.  Run the node/install.sh script to install minification tools.
2.  Activate the virtual environment (source venv/bin/activate)
2.  From the NMTK_apps folder, run "python manage.py minify" to minify code
3.  Run "python manage.py collectstatic -c" to re-install the static media (along with minified stuff.)

## Validating Your Installation

Once NMTK is installed, it makes sense to do some basic validation to ensure 
things are working properly.  Generally, this is done using a core set of
unit tests that exist in the tests/ subdirectory.  Follow the steps below to run 
the tests.  They should all pass.  

The unit tests verify that tool discovery works properly, basic security
is working properly, user account login/logout/creation/passwords work 
properly, file imports work properly, and that jobs can be submitted to 
one of the built-in tools properly.

```
  source venv/bin/activate
  pushd tests
  nosetests -v
  popd
```

Generally, tests will take a few minutes to run.  Be patient.  If any of the tests
fail it could indicate that your server is mis-configured, or otherwise not working
properly (possibly because of insufficient memory -- see the swapfile section above).
A large file import test exists, but is skipped by default, due to the fact that in
some systems it will require more than the allocated amount of memory in order to
successfully complete.

## Managing Tools and Tool Servers

The remainder of configuration (such as creating or authorizing users, removing the
default tool server and/or adding a new tool server) can now be done via the
Administrative pages of the application - via the web.

The administrative server will be available at this URL (change the domain name to
whatever location you are running your server):

  http://nmtk.example.com/server/admin

To add a new tool
-----------------
 
Here we will assume the NMTK server "base" URL is is http://nmtk.example.com):

1.  Ensure your tool server is working (accepting requests via the web) 
    otherwise adding it will be a futile task, since the server will immediately 
    try to query the tool server for a list of tools it provides.
    
2.  Open your browser and point to the administrative page of the server:

  http://nmtk.example.com/server/admin

3.  Login using the credentials you created in step 9 (above)

4.  Click on "Tool Servers"

5.  If you wish to not use the "default" tools, then click the check box next 
	to the "Sample tool server", choose "delete" from the drop down, and 
	press "Go" to delete the tool server.  Note that deleting the tool server 
	will also delete all associated tools supplied by that server.

6.  To add a new tool server, click on "Add Tool Server" (upper right of the page.)

7.  Give your tool server a sensible name, and provide it with a URL (the url
    for the tool server.)  Note that the URL with "/index" appended should return a
    list of the available tools as a JSON string.  

8.  Copy the "auth token", which is the key used to sign requests between the 
    NMTK server and tool server.  This is commonly referred to as a 
    "shared secret" and is used to authenticate requests between the NMTK
    server and tool server.  You will need to share it with the tool server
    admin.

9.  Click "Save" to add the tool server (the NMTK server will immediately go 
    out and query the tool server to get a list of tools!)

10.  Copy the tool server ID that appears on the "Tool Servers" admin page
     and provide it, along with the shared secret you got in step 7 to the
     maintainer of the tool server.  You should also provide the tool admin
     the URL for the NMTK server.
    
Using the NMTK provided tool server
-----------------------------------

If you are using the NMTK provided tool server, you'll need to get a set of
credentials (auth token and a tool server ID) from the NMTK server administrator
(see the previous section on adding a tool server regarding how to generate that
information).

Once you have these credentials, open up NMTK_apps/NMTK_apps/local_settings.py and
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
two options:
  * python manage.py discover_tools
      - This command will re-discover the provided tools for each tool server
        that is configured.
  * Return to the admin page, open the tool server you wish to refresh for editing,
    and hit "save" (no need to make any changes, the act of saving will kick off a 
    refresh for the tools provided by that tool server.)


