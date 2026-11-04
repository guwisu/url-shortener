class AppException(Exception):
    pass


class UserAlreadyExists(AppException):
    pass


class InvalidCredentials(AppException):
    pass


class LinkNotFound(AppException):
    pass


class LinkDeactivated(AppException):
    pass


class ServiceUnavailable(AppException):
    pass
