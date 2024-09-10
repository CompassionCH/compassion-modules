To configure this module, follow these steps:

1. **Odoo Configuration**:
   - Add the following settings in the `.conf` file of Odoo:
     - `connect_url`: URL to the entry point of GMC Onramp
     - `connect_token_server`: Base URL of the token server
     - `connect_token_cert`: Comma-separated list of full URLs of the public keys of the token server

2. **Odoo Settings**:
   - Navigate to `Settings -> General Settings -> Compassion -> Message Center` and set the following:
     - `connect_gpid`: Your GPA ID for using GMC message services
     - `connect_gp_name`: Your GPA name for using GMC message services
     - `connect_api_key`: API key for using GMC message services
     - `connect_client`: Username for token requests
     - `connect_secret`: Password for token requests

3. **User Setup**:
   - Create a user with the required access rights and set the login credentials to match those sent by GMC in tokens.
   - Assign the "GMC Manager" access rights to users responsible for managing messages.
