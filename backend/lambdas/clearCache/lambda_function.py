import ssl
from pymemcache.client.base import Client

elasticache_config_endpoint = "orderandorderitems-tftbcd.serverless.use1.cache.amazonaws.com"
target_port = 11211

context = ssl.create_default_context()

memcached_client = Client((elasticache_config_endpoint, target_port), tls_context=context)

def lambda_handler(event, context):
    # get the item (UUID) from the cache
    result = memcached_client.get(event['key'])
    print(result)
    decoded_result = result.decode("utf-8") if result else None
    
    if decoded_result:
        # Clearing the item from the cache
        memcached_client.delete(event['key'])
        return True
    else:
        return False
