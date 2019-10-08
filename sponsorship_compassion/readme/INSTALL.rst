This modules requires en_US, fr_CH, de_DE and it_IT to be installed
on the server.

To check installed locales:

* locale -a

To add a new locale :

* /usr/share/locales/install-language-pack <ISO-locale-name>
* dpkg-reconfigure locales