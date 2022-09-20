# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Account related classes and functions."""

from typing import Optional, Dict
from urllib.parse import urlparse
from .exceptions import InvalidAccountError
from .configuration import ProxyConfiguration


class Account:
    """Class that represents an account."""

    def __init__(
        self,
        token: Optional[str] = None,
        url: Optional[str] = None,
        channel: Optional[str] = None,
        proxies: Optional[ProxyConfiguration] = None,
        verify: Optional[bool] = True,
        preferences: Optional[Dict] = None,
        local: Optional[bool] = False,
    ):
        """Account constructor.

        Args:
            token: Account token to use.
            url: Authentication URL.
            channel: Authentication channel (ibm_cloud/ibm_quantum)
            proxies: Proxy configuration.
            verify: Whether to verify server's TLS certificate.
        """
        self.token = token
        self.url = url
        self.channel = channel
        self.proxies = proxies
        self.verify = verify
        self.preferences = preferences
        self.local = local

    def to_saved_format(self) -> dict:
        """Returns a dictionary that represents how the account is saved on disk."""
        result = {k: v for k, v in self.__dict__.items() if v is not None}
        if self.proxies:
            result["proxies"] = self.proxies.to_dict()
        return result

    @classmethod
    def from_saved_format(cls, data: dict) -> "Account":
        """Creates an account instance from data saved on disk."""
        proxies = data.get("proxies")
        return cls(
            url=data.get("url"),
            token=data.get("token"),
            channel=data.get("channel"),
            proxies=ProxyConfiguration(**proxies) if proxies else None,
            verify=data.get("verify", True),
            preferences=data.get("preferences"),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Account):
            return False
        return all(
            [
                self.token == other.token,
                self.url == other.url,
                self.channel == other.channel,
                self.proxies == other.proxies,
                self.verify == other.verify,
                self.preferences == other.preferences,
                self.local == other.local,
            ]
        )

    def validate(self) -> "Account":
        """Validates the account instance.

        Raises:
            InvalidAccountError: if the account is invalid

        Returns:
            This Account instance.
        """
        if self.local:
            return True
        self._assert_valid_token(self.token)
        self._assert_valid_url(self.url)
        self._assert_valid_proxies(self.proxies)
        return self

    @staticmethod
    def _assert_valid_token(token: str) -> None:
        """Assert that the token is valid."""
        if not (isinstance(token, str) and len(token) > 0):
            raise InvalidAccountError(
                f"Invalid `token` value. Expected a non-empty string, got '{token}'."
            )

    @staticmethod
    def _assert_valid_url(url: str) -> None:
        """Assert that the URL is valid."""
        try:
            urlparse(url)
        except Exception as err:
            raise InvalidAccountError(
                f"Invalid `url` value. Failed to parse '{url}' as URL."
            ) from err

    @staticmethod
    def _assert_valid_proxies(config: ProxyConfiguration) -> None:
        """Assert that the proxy configuration is valid."""
        if config is not None:
            config.validate()
