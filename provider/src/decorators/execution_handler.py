import time
from functools import wraps
import random

def calculate_exe_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):

        print(f"PROCESSING_DELAY: {random.randrange(3,6)}")

        start = time.time()

        result = await func(*args, **kwargs)
        end = time.time()
        print(f"Execution time - {end - start}")
        return {'response':result, 'execution_time': end - start}

    return wrapper