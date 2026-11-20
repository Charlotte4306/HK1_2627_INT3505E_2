import logging
from datetime import datetime, timezone
from email.utils import format_datetime
from functools import wraps

from flask import make_response, request

log = logging.getLogger("sunset")


def deprecate_at(sunset_date, replacement=None):
    """Announce retirement and return 410 once the deadline is reached."""
    if sunset_date.utcoffset() is None:
        raise ValueError("sunset_date must include a timezone")
    sunset_date = sunset_date.astimezone(timezone.utc)
    sunset_header = format_datetime(sunset_date, usegmt=True)

    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            log.warning("deprecated_call %s %s", request.path, request.remote_addr)

            if datetime.now(timezone.utc) >= sunset_date:
                response = make_response({
                    "error": "gone",
                    "sunset": sunset_header,
                    "use_instead": replacement,
                }, 410)
            else:
                response = make_response(fn(*args, **kwargs))

            response.headers["Sunset"] = sunset_header
            response.headers["Deprecation"] = "true"
            if replacement:
                response.headers.add("Link", f'<{replacement}>; rel="successor-version"')
            return response

        return wrapped

    return decorate
