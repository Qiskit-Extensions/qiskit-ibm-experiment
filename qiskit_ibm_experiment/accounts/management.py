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

"""Account management related classes and functions."""

import os
from typing import Optional, Dict
from .exceptions import AccountNotFoundError
from .account import Account
from .configuration import ProxyConfiguration
from .storage import save_config, read_config, delete_config
from ..service.constants import (
    DEFAULT_ACCOUNT_CONFIG_JSON_FILE,
    DEFAULT_ACCOUNT_NAME,
    ACCOUNT_CHANNEL,
)


class AccountManager:
    """Class that bundles account management related functionality."""

    @classmethod
    def save(
        cls,
        token: Optional[str] = None,
        url: Optional[str] = None,
        name: Optional[str] = DEFAULT_ACCOUNT_NAME,
        proxies: Optional[ProxyConfiguration] = None,
        verify: Optional[bool] = None,
        overwrite: Optional[bool] = False,
    ) -> None:
        """Save account on disk."""
        config_key = name or cls._get_default_account_name()
        return save_config(
            filename=DEFAULT_ACCOUNT_CONFIG_JSON_FILE,
            name=config_key,
            overwrite=overwrite,
            config=Account(
                token=token,
                url=url,
                channel=ACCOUNT_CHANNEL,
                proxies=proxies,
                verify=verify,
            )
            # avoid storing invalid accounts
            .validate().to_saved_format(),
        )

    @staticmethod
    def list(
        default: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Account]:
        """List all accounts saved on disk."""

        def _matching_name(account_name: str) -> bool:
            return name is None or name == account_name

        def _matching_default(account_name: str) -> bool:
            default_accounts = [
                DEFAULT_ACCOUNT_NAME,
            ]
            if default is None:
                return True
            elif default is False:
                return account_name not in default_accounts
            else:
                return account_name in default_accounts

        # load all accounts
        all_accounts = map(
            lambda kv: (kv[0], Account.from_saved_format(kv[1])),
            read_config(filename=DEFAULT_ACCOUNT_CONFIG_JSON_FILE).items(),
        )

        # filter based on input parameters
        filtered_accounts = dict(
            list(
                filter(
                    lambda kv: _matching_default(kv[0]) and _matching_name(kv[0]),
                    all_accounts,
                )
            )
        )

        return filtered_accounts

    @classmethod
    def get(cls, name: Optional[str] = None) -> Optional[Account]:
        """Read account from disk.

        Args:
            name: Account name.

        Returns:
            Account information.

        Raises:
            AccountNotFoundError: If the input value cannot be found on disk.
        """
        if name:
            saved_account = read_config(
                filename=DEFAULT_ACCOUNT_CONFIG_JSON_FILE, name=name
            )
            if not saved_account:
                raise AccountNotFoundError(
                    f"Account with the name {name} does not exist on disk."
                )
            return Account.from_saved_format(saved_account)

        env_account = cls._from_env_variables()
        if env_account is not None:
            return env_account

        all_config = read_config(filename=DEFAULT_ACCOUNT_CONFIG_JSON_FILE)
        account_name = cls._get_default_account_name()
        if account_name in all_config:
            return Account.from_saved_format(all_config[account_name])

        raise AccountNotFoundError("Unable to find account.")

    @classmethod
    def delete(
        cls,
        name: Optional[str] = None,
    ) -> bool:
        """Delete account from disk."""

        config_key = name or cls._get_default_account_name()
        return delete_config(name=config_key, filename=DEFAULT_ACCOUNT_CONFIG_JSON_FILE)

    @classmethod
    def _from_env_variables(cls) -> Optional[Account]:
        """Read account from environment variable."""
        token = os.getenv("QISKIT_IBM_EXPERIMENT_TOKEN")
        url = os.getenv("QISKIT_IBM_EXPERIMENT_URL")
        if not (token and url):
            return None
        return Account(token=token, url=url)

    @classmethod
    def _get_default_account_name(cls) -> str:
        return DEFAULT_ACCOUNT_NAME
