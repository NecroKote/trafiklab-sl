from sys import version_info

if version_info >= (3, 13):
    from warnings import deprecated
else:
    from warnings import warn

    def deprecated(message: str):
        """polyfill for 3.13 deprecation decorator"""

        def decorator(cls):
            warn(message, DeprecationWarning, stacklevel=2)
            return cls

        return decorator
