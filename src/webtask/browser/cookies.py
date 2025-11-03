"""Cookie data structures and utilities."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class Cookie:
    """
    Represents a single HTTP cookie.

    Attributes:
        name: Cookie name
        value: Cookie value
        domain: Domain for the cookie
        path: Path for the cookie
        expires: Expiration timestamp (Unix time)
        httpOnly: Whether cookie is HTTP only
        secure: Whether cookie requires HTTPS
        sameSite: SameSite attribute ('Strict', 'Lax', or 'None')
    """

    name: str
    value: str
    domain: Optional[str] = None
    path: str = "/"
    expires: Optional[int] = None
    httpOnly: bool = False
    secure: bool = False
    sameSite: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert cookie to dictionary format (for Playwright, Selenium, etc.).

        Returns:
            Dictionary representation of the cookie
        """
        result = {
            "name": self.name,
            "value": self.value,
            "path": self.path,
            "httpOnly": self.httpOnly,
            "secure": self.secure,
        }

        if self.domain is not None:
            result["domain"] = self.domain

        if self.expires is not None:
            result["expires"] = self.expires

        if self.sameSite is not None:
            result["sameSite"] = self.sameSite

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cookie":
        """
        Create a Cookie from dictionary format.

        Args:
            data: Dictionary with cookie data

        Returns:
            Cookie instance
        """
        return cls(
            name=data["name"],
            value=data["value"],
            domain=data.get("domain"),
            path=data.get("path", "/"),
            expires=data.get("expires"),
            httpOnly=data.get("httpOnly", False),
            secure=data.get("secure", False),
            sameSite=data.get("sameSite"),
        )


class Cookies:
    """
    Utility class for cookie conversions and operations.

    Handles conversion between different cookie formats (string, dict list, etc.).
    """

    @staticmethod
    def from_string(cookie_string: str, domain: str) -> List[Cookie]:
        """
        Parse cookie string to list of Cookie objects.

        Args:
            cookie_string: Cookie string (e.g., "name1=value1; name2=value2")
            domain: Domain for all cookies (e.g., ".google.com", "example.com")

        Returns:
            List of Cookie objects

        Example:
            >>> cookies = Cookies.from_string("session_id=abc123; user_pref=dark", domain=".example.com")
            >>> len(cookies)
            2
            >>> cookies[0].domain
            '.example.com'
        """
        cookies = []
        for pair in cookie_string.split(";"):
            pair = pair.strip()
            if "=" in pair:
                name, value = pair.split("=", 1)
                cookies.append(
                    Cookie(
                        name=name.strip(),
                        value=value.strip(),
                        domain=domain,
                    )
                )

        return cookies

    @staticmethod
    def to_string(cookies: List[Cookie]) -> str:
        """
        Convert list of cookies to cookie string format.

        Args:
            cookies: List of Cookie objects

        Returns:
            Cookie string (e.g., "name1=value1; name2=value2")

        Example:
            >>> cookies = [Cookie(name="session", value="123")]
            >>> Cookies.to_string(cookies)
            'session=123'
        """
        return "; ".join(f"{cookie.name}={cookie.value}" for cookie in cookies)

    @staticmethod
    def to_dict_list(cookies: List[Cookie]) -> List[Dict[str, Any]]:
        """
        Convert list of cookies to list of dictionaries.

        Args:
            cookies: List of Cookie objects or dictionaries

        Returns:
            List of cookie dictionaries

        Example:
            >>> cookies = [Cookie(name="session", value="123")]
            >>> Cookies.to_dict_list(cookies)
            [{'name': 'session', 'value': '123', 'path': '/', 'httpOnly': False, 'secure': False}]
        """
        # Handle both Cookie objects and dictionaries
        result = []
        for cookie in cookies:
            if isinstance(cookie, dict):
                # Already a dictionary, use as-is
                result.append(cookie)
            else:
                # Cookie object, convert to dict
                result.append(cookie.to_dict())
        return result

    @staticmethod
    def from_dict_list(data: List[Dict[str, Any]]) -> List[Cookie]:
        """
        Create list of cookies from list of dictionaries.

        Args:
            data: List of cookie dictionaries

        Returns:
            List of Cookie objects
        """
        return [Cookie.from_dict(d) for d in data]
