

def normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://", "file://", "about:")):
        url = f"https://{url}"

    return url
