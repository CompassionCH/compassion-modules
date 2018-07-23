Développement
~~~~~~~~~~~~~

Pour développer sur la webapp react, il est conseillé de suivre les étapes suivantes :
#. Utiliser un éditeur de code compatible avec React (par exemple : WebStorm)
#. Ouvrir le projet ``sms_sponsorship/webapp``
#. Si nécessaire, executer ``npm install``

Pour lancer l'application sur le serveur de développement, il faut lancer la commande ``npm start``

Proxy
*****

Pour que le serveur de développement puisse accéder à odoo, il est nécessaire d'ajouter toutes les routes d'odoo dont
react a besoin pour fonctionner dans le fichier ``package.json``.

Voici un exemple pour les routes ``/sms_sponsorship_api`` :

   "proxy": { "/sms_sponsorship_api": { "target": "http://localhost:8069/", "secure": false } }