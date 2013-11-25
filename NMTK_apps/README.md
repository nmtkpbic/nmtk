/*
 * Chander Ganesan, 2013 <chander@otg-nc.com>
 */

This is the main directory for all the Django applications that make up 
this project.  A few notes:

1.  NMTK_apps is the "overriding" application component, containing the
    settings for the project as a whole, as well as the default URL patterns.
    
2.  The NMTK components can exist either together or apart.  Tools can be installed
    on their own without need/regard for the NMTK server.
    
3.  The API and user management occur via the NMTK_server component, but it does
    not contain the UI for interacting with the server.  Since the API is a 
    RESTful one, any client can interact with it, and it's possible that a
    developer might not want the "default" UI.  However, to manage users,
    interact with tool servers, submit jobs, etc. you must install the
    NMTK_server component.
    
4.  The NMTK_ui component contains ONLY the UI componets for the default (web) 
    client used with NMTK.  The UI is a browser-based tool using a variety of
    contributed libraries (AngularJS/Restangular/Angular-Bootstrap/Underscorejs/
    Requirejs - to name a few).  If the UI component is installed, the NMTK server
    will automatically redirect users upon login to this default UI.  If the
    UI is not installed, users will be returned to the landing page once 
    they log in.
 
5.  The NTMK_tools application provide the "index" URI that lists all the available 
    tools.  If NMTK_tools is not installed, then the index will be unavailable.
    	- Note that NMTK_server relies on the index to get a list of available
    	  tools from a server.  Without it, auto-tool-discovery and auto-tool-updates
    	  will not work.  Basically, if you are serving up tools, you need this.
    	  If you omit it, chances are your tools will periodically be marked as inactive
    	  whenever new tool scans occur.  Maybe other bad things too - like Karma.
    	      
6.  The tools that are provide by default are:
 		- SF_model - Reference the API/Tool docs for information
 		- MN_model - Reference the API/Tool docs for information
 		
Note that tool/other processing happens out-of-line with web requests (via celery)
and most actions are tied to changes in the data model (so adding/removing data 
will automagically kick of the requisite tasks.)
 		