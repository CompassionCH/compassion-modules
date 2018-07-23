To install the module, you need to cd to ``sms_sponsorship/webapp`` and run the following commands :

.. code-block:: sh

    npm install
    npm run build

Then, a new ``build`` folder will appear into ``webapp``. If there is no ``sms_sponsorship/static`` symbolic link, run this command :

.. code-block:: sh

    ln -s sms_sponsorship/webapp/build sms_sponsorship/static
