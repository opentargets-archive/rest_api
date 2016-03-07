from werkzeug.exceptions import HTTPException


class TokenExpired(HTTPException):
    """*419* `Authentication expired`

    Raise if the authentication token is exprired
    """
    code = 419
    description = (
        'Authentication expired'
    )
