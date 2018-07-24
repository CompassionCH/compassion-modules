Development
~~~~~~~~~~~

To develop for the react webapp, please follow these steps :
#. Use a code editor compatible with react (for exemple : WebStorm)
#. Open the project ``sms_sponsorship/webapp``
#. If not already done, execute ``npm install``

To launch the app on the development server, run ``npm start``.

Proxy
~~~~~


In order for the development server to access odoo, it is necessary to add all
the odoo routes react needs in the file ``package.json``.

Here is an exemple for ``/sms_sponsorship_api`` :

   "proxy": { "/sms_sponsorship_api": { "target": "http://localhost:8069/", "secure": false } }