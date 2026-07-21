"""Excepciones controladas de la integración con MediaMTX."""


class MediaMTXError(Exception):
    """Error base de la integración con MediaMTX."""


class MediaMTXConnectionError(MediaMTXError):
    """MediaMTX no está disponible o no acepta conexiones."""


class MediaMTXTimeoutError(MediaMTXError):
    """La consulta a MediaMTX excedió el tiempo permitido."""


class MediaMTXHTTPError(MediaMTXError):
    """MediaMTX respondió con un código HTTP no exitoso."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"MediaMTX HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message


class MediaMTXInvalidResponseError(MediaMTXError):
    """MediaMTX devolvió una respuesta inválida o inesperada."""
