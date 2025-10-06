from functools import wraps
from typing import Callable


class SessionRequired:
    def __init__(self, async_mode: bool = False):
        self.async_mode = async_mode

    def __call__(self, func: Callable) -> Callable:
        if self.async_mode:
            @wraps(func)
            async def async_wrapper(instance, *args, **kwargs):
                if 'session' not in kwargs:
                    session = getattr(instance, '_session', None)
                    if session is None:
                        raise RuntimeError(
                            f"Session not found. Use model with DBContext or pass session explicitly."
                        )
                    kwargs['session'] = session
                return await func(instance, *args, **kwargs)

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(instance, *args, **kwargs):
                if 'session' not in kwargs:
                    session = getattr(instance, '_session', None)
                    if session is None:
                        raise RuntimeError(
                            f"Session not found. Use model with DBContext or pass session explicitly."
                        )
                    kwargs['session'] = session
                return func(instance, *args, **kwargs)

            return sync_wrapper