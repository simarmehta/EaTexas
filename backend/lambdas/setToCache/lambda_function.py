import ssl
from pymemcache.client.base import Client

elasticache_config_endpoint = "orderandorderitems-tftbcd.serverless.use1.cache.amazonaws.com"
target_port = 11211

context = ssl.create_default_context()

memcached_client = Client((elasticache_config_endpoint, target_port), tls_context=context)

def lambda_handler(event, context):
    key = event.get('key')
    value = event.get('value')  # New value to be set
    
    if key and value:
        try:
            # Set the value in Memcached with the provided key
            memcached_client.set(key, str(value))
            return True
        except Exception as e:
            return False
    else:
        return False
