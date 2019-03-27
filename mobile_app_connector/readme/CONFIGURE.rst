Make sure the following variables are defined in your odoo.conf file:

- `wordpress_host`: host URL for the Wordpress website where the blog posts will be fetched.
- `wordpress_user`: user login for the Wordpress website where the blog posts will be fetched.
- `wordpress_pwd`: user password for the Wordpress website where the blog posts will be fetched.

The login info allows the fetching of attached media which main post isn't published.
The plugin `wp-api-jwt-auth` must be installed on Wordpress so that
the requests can be authenticated.
