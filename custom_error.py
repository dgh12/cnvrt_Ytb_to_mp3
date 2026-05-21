"""Custom exceptions for the YouTube to MP3 converter."""
class UrlError(Exception):
    """Raised when invalid URL is provided."""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidFileTypeError(Exception):
    """Raised when an invalid file type is provided."""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
