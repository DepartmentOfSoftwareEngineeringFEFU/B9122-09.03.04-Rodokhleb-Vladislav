class AppException(Exception):
    pass

class NotFoundError(AppException):
    pass

class ValidationError(AppException):
    pass

class AuthError(AppException):
    pass

class VideoProcessingError(AppException):
    pass

class ModelError(AppException):
    pass