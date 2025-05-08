from django.core.cache import cache, caches
from django.utils.encoding import force_str
from django.conf import settings
from functools import wraps
import hashlib
import time
import logging

logger = logging.getLogger(__name__)

def generate_cache_key(prefix, *args, **kwargs):
    """
    Generate a unique cache key based on the prefix and arguments.
    
    Args:
        prefix: String prefix for the cache key
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key
        
    Returns:
        A unique cache key string
    """
    key_parts = [prefix]
    
    # Add positional arguments to the key
    for arg in args:
        if arg is not None:
            key_parts.append(force_str(arg))
    
    # Add keyword arguments to the key, sorted by key name
    for key in sorted(kwargs.keys()):
        value = kwargs[key]
        if value is not None:
            key_parts.append(f"{key}:{force_str(value)}")
    
    # Create a base key
    base_key = "_".join(key_parts)
    
    # Hash the key if it might be too long
    if len(base_key) > 200:
        hashed = hashlib.md5(base_key.encode('utf-8')).hexdigest()
        return f"{prefix}_{hashed}"
    
    return base_key

def cache_response(timeout=None, key_prefix='view', cache_alias='default'):
    """
    Decorator for caching view responses.
    
    Args:
        timeout: Cache timeout in seconds (default: None, using the default cache timeout)
        key_prefix: Prefix for the cache key
        cache_alias: Cache backend to use
        
    Example:
        @cache_response(timeout=60, key_prefix='user_posts')
        def get_user_posts(request, user_id):
            # Function logic here
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Skip cache for authenticated requests unless explicitly allowed
            if hasattr(request, 'user') and request.user.is_authenticated and getattr(view_func, 'cache_authenticated', False) is False:
                return view_func(request, *args, **kwargs)
            
            # Get the appropriate cache backend
            cache_backend = caches[cache_alias]
            
            # Generate a cache key based on the request and arguments
            key = generate_cache_key(
                key_prefix,
                request.path,
                request.GET.urlencode(),
                *args,
                **kwargs
            )
            
            # Try to get the response from cache
            response = cache_backend.get(key)
            if response is not None:
                return response
            
            # Generate the response
            response = view_func(request, *args, **kwargs)
            
            # Cache the response if it's cacheable
            if hasattr(response, 'render') and callable(response.render):
                response.add_post_render_callback(
                    lambda r: cache_backend.set(key, r, timeout)
                )
            else:
                cache_backend.set(key, response, timeout)
            
            return response
        
        # Add a flag to explicitly allow caching of authenticated requests
        def cache_authenticated():
            _wrapped_view.cache_authenticated = True
            return _wrapped_view
        
        _wrapped_view.cache_authenticated = False
        _wrapped_view.cache_authenticated = cache_authenticated
        
        return _wrapped_view
    
    return decorator

def cache_model_method(timeout=None, key_prefix=None):
    """
    Decorator for caching model method results.
    
    Args:
        timeout: Cache timeout in seconds (default: None, using the default cache timeout)
        key_prefix: Prefix for the cache key (default: model name + method name)
    
    Example:
        @cache_model_method(timeout=300)
        def get_stats(self):
            # Expensive calculation here
    """
    def decorator(method):
        @wraps(method)
        def wrapped(self, *args, **kwargs):
            # Generate the prefix if not provided
            prefix = key_prefix
            if prefix is None:
                prefix = f"{self.__class__.__name__.lower()}_{method.__name__}"
            
            # Create a key that includes the model's primary key
            key = generate_cache_key(prefix, self.pk, *args, **kwargs)
            
            # Try to get the result from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Call the method and cache the result
            result = method(self, *args, **kwargs)
            cache.set(key, result, timeout)
            
            return result
        
        return wrapped
    
    return decorator

def invalidate_model_cache(instance, method_name=None):
    """
    Invalidate cache for a specific model instance or method.
    
    Args:
        instance: The model instance
        method_name: Optional method name to invalidate specific method cache
    """
    model_name = instance.__class__.__name__.lower()
    
    if method_name is None:
        # Invalidate all caches for this instance by using a pattern
        pattern = f"{model_name}_*_{instance.pk}_*"
        keys = cache.keys(pattern)
        for key in keys:
            cache.delete(key)
    else:
        # Invalidate a specific method cache
        key_prefix = f"{model_name}_{method_name}"
        key_pattern = f"{key_prefix}_{instance.pk}_*"
        keys = cache.keys(key_pattern)
        for key in keys:
            cache.delete(key)

class QuerySetCacheMixin:
    """
    Mixin to add caching capabilities to QuerySets.
    
    Example:
        class PostQuerySet(QuerySetCacheMixin, models.QuerySet):
            pass
            
        class Post(models.Model):
            objects = PostQuerySet.as_manager()
    """
    
    def cached(self, timeout=None, key_prefix=None):
        """
        Cache the results of a QuerySet.
        
        Args:
            timeout: Cache timeout in seconds
            key_prefix: Custom prefix for the cache key
        """
        if not key_prefix:
            key_prefix = f"{self.model.__name__.lower()}_queryset"
        
        # Generate a query signature based on the query's SQL
        query_sql = str(self.query)
        query_sig = hashlib.md5(query_sql.encode()).hexdigest()
        
        key = f"{key_prefix}_{query_sig}"
        
        # Try to get results from cache
        results = cache.get(key)
        if results is not None:
            return results
        
        # Execute the query and cache the results
        results = list(self)
        cache.set(key, results, timeout)
        
        return results

def rate_limit(key_pattern, limit=10, period=60, raise_exception=True):
    """
    Rate limiting decorator that uses Redis cache.
    
    Args:
        key_pattern: Pattern for the rate limit key (e.g., 'rate_limit:{user_id}:{action}')
        limit: Maximum number of calls allowed within the period
        period: Time period in seconds
        raise_exception: Whether to raise an exception (True) or return False (False) when rate limit is exceeded
    
    Example:
        @rate_limit('message:{request.user.id}', limit=5, period=60)
        def send_message(request):
            # Function logic here
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Format the key with request attributes
            key = key_pattern.format(request=request, **kwargs)
            
            # Check if rate is limited
            current = cache.get(key, 0)
            
            if current >= limit:
                if raise_exception:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("Rate limit exceeded")
                return False
            
            # Increment the counter
            pipe = cache.client.pipeline()
            pipe.incr(key)
            # If this is the first request, set an expiration
            if current == 0:
                pipe.expire(key, period)
            pipe.execute()
            
            # Call the view function
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    return decorator

def clear_user_cache(user_id):
    """
    Clear all cache entries related to a specific user.
    
    Args:
        user_id: The ID of the user
    """
    patterns = [
        f"*_user_{user_id}_*",
        f"*_user:{user_id}_*",
        f"user_{user_id}_*",
    ]
    
    for pattern in patterns:
        keys = cache.keys(pattern)
        if keys:
            cache.delete_many(keys)
            logger.info(f"Cleared {len(keys)} cache entries for user {user_id}")

def clear_model_cache(model_name, object_id=None):
    """
    Clear cache for a model or specific model instance.
    
    Args:
        model_name: The name of the model (lowercase)
        object_id: Optional ID of the specific object
    """
    if object_id:
        pattern = f"{model_name}_*_{object_id}_*"
    else:
        pattern = f"{model_name}_*"
    
    keys = cache.keys(pattern)
    if keys:
        cache.delete_many(keys)
        logger.info(f"Cleared {len(keys)} cache entries for model {model_name}")

def timed_cache(timeout=300):
    """
    Simple in-memory cache decorator with timeout.
    Useful for methods that are called frequently with the same arguments.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
    """
    def decorator(func):
        _cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a key from the function arguments
            key = str(args) + str(sorted(kwargs.items()))
            key = hashlib.md5(key.encode()).hexdigest()
            
            # Check if the result is cached and not expired
            current_time = time.time()
            if key in _cache:
                result, timestamp = _cache[key]
                if current_time - timestamp < timeout:
                    return result
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            _cache[key] = (result, current_time)
            
            # Clean old entries periodically (1% chance on each call)
            if random.random() < 0.01:
                for k in list(_cache.keys()):
                    if current_time - _cache[k][1] > timeout:
                        del _cache[k]
            
            return result
        
        return wrapper
    
    return decorator

def cached_property_with_ttl(ttl=None):
    """
    Decorator for caching expensive property calculations with a TTL.
    Similar to @property and @functools.cached_property but with expiration.
    
    Args:
        ttl: Time-to-live in seconds (default: None - no expiration)
    """
    def decorator(func):
        @property
        def wrapper(self):
            # Use the function name as the cache attribute name
            attr_name = f"_{func.__name__}_cached_result"
            timestamp_name = f"_{func.__name__}_cached_timestamp"
            
            # Check if we have a cached result and it's not expired
            if hasattr(self, attr_name) and (
                ttl is None or 
                time.time() - getattr(self, timestamp_name, 0) < ttl
            ):
                return getattr(self, attr_name)
            
            # Calculate and cache the result
            result = func(self)
            setattr(self, attr_name, result)
            setattr(self, timestamp_name, time.time())
            
            return result
        
        return wrapper
    
    return decorator