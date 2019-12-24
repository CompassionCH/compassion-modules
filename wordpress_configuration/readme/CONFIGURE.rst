One configuration record should be created for each company.
(in Settings/Technical menu/Wordpress configuration)

Upon installation, the module tries to create a default configuration for the current company by reading the following
values in Odoo's config file:

* ``wordpress_host`` : the server url of your wordpress installation (ex: wordpress.local)
* ``wordpress_user`` : a wordpress user which have read/write access to the childpool
* ``wordpress_pwd`` : the password of the wordpress user
