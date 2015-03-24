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

# NMTK Server Windows Installation
This document explains how to install the NMTK Server and reference implementation of tools under the Windows platform.

1. Download & Install Git
    - Download from: http://www.git-scm.com/download/win
    - When using the installer, be sure to choose "Windows Explorer integration"; and "Git bash here" and "Git GUI Here"
    - Select the default "Use Git from Git Bash only"
2. Download and install Python 2.7 (note: 3.x versions of Python are unsupported with NMTK):
    - The following packages should be downloaded from the URLs provided below. Be sure to choose binaries that are consistent (for example, all 32 bit (x86) or all 64 bit (amd64)).
    - https://www.python.org/download 
3. Add Python to the system path:
    - Click on the start menu, go to "Computer", right-click on it and choose "Properties" Click on "Advanced System Settings"
    - Choose the "Advanced" tab
    - Click on "Environment Variables"
    - Under "System Variables" choose "Path", and the press "Edit"
    - In the "Variable value" field, scroll to the end of the field and append 
    
            ;C:\Python27;C: \Python27\scripts;C:\Program Files\PostgreSQL\9.3\bin
            
        - **Note**: The leading ; separates this new set of directories from the existing ones, and is required.)
    - Choose "OK" to save the settings.
4.  Download and install the OSGeo4W Installer, and install.
    - http://trac.osgeo.org/osgeo4w/
    - Choose the "Advanced Install"
    - Choose "Download from Internet"
    - Choose the default values/options until you get to the "Select Packages" page.
    - On the "Select Packages" dialog expand "All", then expand "Web", then choose "mapserver" by clicking on the word "Skip" next to it.
    - Continue to choose the default options to complete the installer.
5.  Download and install PostgreSQL:
    - http://www.postgresql.org/download/windows/
    - Choose a suitable password for the postgres user, and remember it (youÕll need it later.)
    - Launch the "Stack Builder Installer" at the end of your installation
      - Choose the PostgreSQL server you just installed (there should only be a single option.)
        - Expand the "Spatial Extensions" tree, and choose to install PostGIS
        - Continue to choose "Next" until the install completes (you will eventually need to enter your PostgreSQL user password.)
        - Do not install/enable the GDAL Raster support in PostGIS, it is not needed.
6.  Create a database in PostgreSQL for NMTK:
    1. Choose Start -> All Programs -> PostgreSQL 9.3 -> SQL Shell (psql)
    2. Press enter until prompted for a password, then enter the PostgreSQL password you
chose earlier
    3. Issue the following commands at the postgres> prompt:
    
            Create database nmtk;
            -- Responds with CREATE DATABASE
            \c nmtk
            -- Responds with "you are now connected to database "nmtk" as user "postgres" "
            create extension postgis;
            -- responds with CREATE EXTENSION
            \q
            
7. Right click on the desktop and choose "Git Bash here"
    - **Note**: You need not checkout/install the NMTK code in your desktop (it just happens to be convenient.) You can create a "Git bash" shell on any folder, then NMTK will be installed within that folder.
    - **Note**: It is advisable to ensure the full path to the NMTK code contains no spaces.
8. Now check out the NMTK Code:
        git clone https://github.com/chander/nmtk
9. Change to the NMTK windows installation directory using the command:
        cd nmtk/windows
10. Run the installer script for Windows:
        bash nmtk_win_install_prereqs.sh
    - This script will do the following:
    - Rename C:\Python27\dlls\sqlite.dll to C:\Python27\dlls\sqlite.dll.old
    - Set the PATH so that the proper libraries are found for NMTK server when the Virtual Environment is activated
    - Create the virtual environment and load all the pre-requisite modules.
    - Prompt you to download various software packages (follow the on-screen instructions, and use the browser windows it opens to download pre-requisites.)
11. Download the following pre-requisite modules, using the same "bit-ness" as your platform, as prompted by the script, then press "enter" to complete the installation process.
12. Change to the NMTK_apps/NMTK_apps directory and copy local_settings.sample to local_settings.py
    - **Note**: For Windows the "DEBUG" setting must be set to "True" 
13. Edit the local_settings.py file:
    - Enter the database name you chose in the previous step (nmtk) in the database name field.
    - Follow the NMTK Directions for the remainder of the settings.
14. Setup the database:
    1. First, activate the Venv 
    
            source venv/scripts/activate
            
    2. Change to the NMTK_apps directory 
    
            cd NMTK_apps
            
    3. Run the syncdb command (this creates the database tables): 
    
            python manage.py syncdb
       
       - **Note**: When prompted, do not create a superuser (it will be removed when fixtures are loaded.)
            
    4. Create an account for yourself: 
    
            python manage.py createsuperuser
            
    5. Generate the legend graphics - color ramps:
    
            python manage.py refresh_colorramps
            
15. Start the server:
    1. First, activate the Venv:
    
            source venv/scripts/activate
            
    2. Change to the NMTK_apps directory:
    
            cd NMTK_apps
            
    3. Run the celeryd command: 
    
            start python manage.py celery worker
            
    4. Run the server command: 
    
            start python manage.py runserver
            
16. Update the tool server location
    1. Open a browser and navigate to http://127.0.0.1:8000
    2. Click on "Site Administration"
    3. Click on "Tool Servers"
    4. Edit the single tool server that exists.
    5. Update the URL to contain a ":8000" after "127.0.0.1"
    6. Wait a few seconds for the tool configuration to be loaded by the server.
17. Start using the NMTK Server (http://127.0.0.1:8000)
