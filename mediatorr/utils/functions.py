from functools import wraps


def cached(func: callable) -> object:
    func.keys = []
    func.values = []

    @wraps(func)
    def wrapper(*args, **kwargs):
        if (args, kwargs) in func.keys:
            return func.values[func.keys.index((args, kwargs))]
        else:
            func.keys.append((args, kwargs))
            result = func(*args, **kwargs)
            func.values.append(result)
            return result

    return wrapper
