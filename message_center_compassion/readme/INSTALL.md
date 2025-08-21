You need to have the OCA repository rest-framework and web-api for having the FastAPI
available.

First install the requirements from rest-framework repository :
```bash
pip install -r ./rest-framework/requirements.txt
```

On your server instance, you need to install the odoo-addon-fastapi Python package. This package's dependencies include Odoo itself, which can cause installation errors as Odoo is typically not installed as a standard Python package via pip. Using the --no-deps flag prevents this dependency check, allowing the addon to install correctly, provided Odoo is already present in your environment.
```bash
pip install odoo-addon-fastapi==17.0.3.2.0 --no-deps
```