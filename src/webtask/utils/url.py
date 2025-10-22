"""URL utility functions."""


def normalize_url(url: str) -> str:
    """
    Normalize a URL by adding https:// if no protocol is specified.

    Args:
        url: URL to normalize (e.g., "google.com" or "https://google.com")

    Returns:
        Normalized URL with protocol

    Examples:
        >>> normalize_url("google.com")
        'https://google.com'
        >>> normalize_url("https://google.com")
        'https://google.com'
        >>> normalize_url("http://example.com")
        'http://example.com'
        >>> normalize_url("file:///path/to/file.html")
        'file:///path/to/file.html'
    """
    # Add https:// if no protocol specified
    if not url.startswith(('http://', 'https://', 'file://', 'about:')):
        url = f'https://{url}'

    return url
