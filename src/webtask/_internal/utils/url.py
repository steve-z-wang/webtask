"""URL utility functions."""


def normalize_url(url: str) -> str:
    """Normalize a URL by adding https:// if no protocol is specified."""
    if not url.startswith(("http://", "https://", "file://", "about:")):
        url = f"https://{url}"

    return url
