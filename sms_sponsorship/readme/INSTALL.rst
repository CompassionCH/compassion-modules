To install the module, you need to cd to ``sms_sponsorship/webapp`` and run the following commands :

   npm install && npm run build

Then, a new ``build`` folder will appear into ``webapp``. If there is no ``sms_sponsorship/static/react`` symbolic link, run this command :

   ln -s sms_sponsorship/webapp/build sms_sponsorship/static/react
