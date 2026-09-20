import json

import time
from functools import wraps

def response_formatter(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):

        result = await func(*args, **kwargs)

        response = {
            'data': result['response'].body,
            'request': kwargs.get('payload'),
            'time_stamp': time.time(),
            'execution_time': result['execution_time'],
        }
        return response

    return wrapper