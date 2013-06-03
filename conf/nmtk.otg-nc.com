<VirtualHost *:80>
  ServerAdmin chander@otg-nc.com
  ServerName nmtk.otg-nc.com
  WSGIDaemonProcess nmtk threads=3 processes=10 display-name=nmtk  \
                    python-path=/var/www/vhosts/nmtk.otg-nc.com/venv/lib/python2.7/site-packages:/var/www/vhosts/nmtk.otg-nc.com/NMTK_apps
  WSGIProcessGroup nmtk
  WSGIPassAuthorization On
    
  WSGIScriptAlias /nmtk /var/www/vhosts/nmtk.otg-nc.com/NMTK_apps/NMTK_apps/wsgi.py
  DirectoryIndex index.html
  DocumentRoot /var/www/vhosts/nmtk.otg-nc.com/htdocs
  <Directory />
    Options FollowSymLinks
    AllowOverride None
  </Directory>
  <Directory /var/www/vhosts/nmtk.otg-nc.com/htdocs>
    Options Indexes FollowSymLinks MultiViews
    AllowOverride None
    Order allow,deny
    allow from all
  </Directory>

  ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
  <Directory "/usr/lib/cgi-bin">
    AllowOverride None
    Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
    Order allow,deny
    Allow from all
  </Directory>

  ErrorLog /var/www/vhosts/nmtk.otg-nc.com/logs/error.log
  CustomLog /var/www/vhosts/nmtk.otg-nc.com/logs/access.log combined

  # Possible values include: debug, info, notice, warn, error, crit,
  # alert, emerg.
  LogLevel warn
</VirtualHost>
