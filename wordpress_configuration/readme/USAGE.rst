The `get_config` method fetch the config for the current company or the one passed through `company_id`

```python
wp_config = env['wordpress.configuration'].get_config()
# use: wp_config.host, wp_config.user, wp_config.password
```
