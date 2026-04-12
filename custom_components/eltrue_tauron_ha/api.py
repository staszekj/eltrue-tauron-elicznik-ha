"""API client for Tauron eLicznik."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
from typing import Any

from aiohttp import ClientSession

from .const import URL_API, URL_LOGIN, URL_LOGOUT, URL_SERVICE

_LOGGER = logging.getLogger(__name__)


class TauronApiError(Exception):
    """Exception for Tauron API errors."""


class TauronAuthError(TauronApiError):
    """Exception for authentication errors."""


@dataclass
class TauronEnergyData:
    """Data class for energy readings."""

    energia_pobrana: float
    energia_oddana: float
    reading_date: datetime
    success: bool


class TauronApiClient:
    """Client for Tauron eLicznik API."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._username = username
        self._password = password
        self._cookies: dict[str, str] = {}

    async def authenticate(self) -> bool:
        """Login to Tauron eLicznik and obtain session cookies."""
        _LOGGER.debug("Authenticating with Tauron eLicznik")

        # GET login page first to obtain PHPSESSID session cookie
        try:
            async with self._session.get(URL_LOGIN, allow_redirects=True):
                pass
        except Exception as err:
            raise TauronApiError(f"Failed to reach login page: {err}") from err

        login_data = {
            "username": self._username,
            "password": self._password,
            "service": URL_SERVICE,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        redirect_url = await self._login_step(login_data, headers)
        await self._get_session_cookies(redirect_url)

        _LOGGER.debug("Successfully authenticated with Tauron eLicznik")
        return True

    async def _login_step(
        self, login_data: dict[str, str], headers: dict[str, str]
    ) -> str:
        """Perform login POST and return redirect URL."""
        try:
            async with self._session.post(
                URL_LOGIN,
                data=login_data,
                headers=headers,
                allow_redirects=False,
            ) as response:
                if response.status not in (302, 303):
                    raise TauronAuthError(  # noqa: TRY301
                        "Login failed - no redirect received"
                    )

                redirect_url = response.headers.get("Location")
                if not redirect_url:
                    raise TauronAuthError(  # noqa: TRY301
                        "Login failed - no redirect URL"
                    )

                # If redirect goes back to /login, authentication failed
                if redirect_url == "/login" or redirect_url.endswith("/login"):
                    raise TauronAuthError(  # noqa: TRY301
                        "Invalid username or password"
                    )

                return redirect_url
        except TauronAuthError:
            raise
        except Exception as err:
            _LOGGER.exception("Authentication error")
            raise TauronApiError(f"Authentication failed: {err}") from err

    async def _get_session_cookies(self, redirect_url: str) -> None:
        """Follow redirect and store session cookies."""
        # Handle relative URLs by making them absolute
        if redirect_url.startswith("/"):
            redirect_url = f"https://logowanie.tauron-dystrybucja.pl{redirect_url}"

        try:
            async with self._session.get(
                redirect_url,
                allow_redirects=True,
            ):
                # Store cookies from response
                self._cookies = {
                    cookie.key: cookie.value for cookie in self._session.cookie_jar
                }

                if not self._cookies:
                    raise TauronAuthError(  # noqa: TRY301
                        "No session cookies received"
                    )
        except TauronAuthError:
            raise
        except Exception as err:
            _LOGGER.exception("Authentication error")
            raise TauronApiError(f"Authentication failed: {err}") from err

    async def fetch_energy_data(
        self, query_date: date | None = None
    ) -> TauronEnergyData:
        """Fetch both energia-pobrana and energia-oddana.

        Queries the last 7 days and returns the most recent reading.
        Today's data is usually not available until after midnight.
        """
        if query_date is None:
            query_date = date.today()

        # Query last 7 days to ensure we get data (today might not be available)
        from_date = query_date - timedelta(days=7)
        from_str = from_date.strftime("%d.%m.%Y")
        to_str = query_date.strftime("%d.%m.%Y")

        _LOGGER.debug("Fetching energy data for %s to %s", from_str, to_str)

        energia_pobrana = await self._fetch_energy_type(from_str, to_str, "energia-pobrana")
        energia_oddana = await self._fetch_energy_type(from_str, to_str, "energia-oddana")

        # Use the reading date from the response (most recent available data)
        reading_date = energia_pobrana.get("date", query_date)

        return TauronEnergyData(
            energia_pobrana=energia_pobrana["counter"],
            energia_oddana=energia_oddana["counter"],
            reading_date=reading_date,
            success=energia_pobrana["success"] and energia_oddana["success"],
        )

    async def _fetch_energy_type(
        self, from_str: str, to_str: str, energy_type: str
    ) -> dict[str, Any]:
        """Fetch a specific energy type from the API."""
        payload = {
            "from": from_str,
            "to": to_str,
            "type": energy_type,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = await self._make_api_request(payload, headers, energy_type)

        if not data.get("success") or not data.get("data"):
            _LOGGER.warning("API returned no data for %s", energy_type)
            return {"success": False, "counter": 0.0}

        # Extract counter value from the LAST record (most recent data)
        # Response format: {"success": true, "data": [{"Date": "09.01.2026 23:59:59", "C": 28969}]}
        try:
            latest_record = data["data"][-1]  # Take last record (most recent)
            counter_value = float(latest_record["C"])

            # Parse the full datetime from the response (e.g. "09.01.2026 23:59:59")
            reading_date = datetime.strptime(latest_record["Date"], "%d.%m.%Y %H:%M:%S")
        except (KeyError, IndexError, TypeError, ValueError) as err:
            raise TauronApiError(f"Invalid API response format: {err}") from err

        return {"success": True, "counter": counter_value, "date": reading_date}

    async def _make_api_request(
        self, payload: dict[str, str], headers: dict[str, str], energy_type: str
    ) -> dict[str, Any]:
        """Make API request and return JSON data."""
        try:
            async with self._session.post(
                URL_API,
                data=payload,
                headers=headers,
            ) as response:
                if response.status != 200:
                    raise TauronApiError(  # noqa: TRY301
                        f"API request failed with status {response.status}"
                    )
                return await response.json()
        except TauronApiError:
            raise
        except Exception as err:
            raise TauronApiError(f"Failed to fetch {energy_type}: {err}") from err

    async def logout(self) -> None:
        """Logout from Tauron eLicznik."""
        try:
            async with self._session.get(URL_LOGOUT, allow_redirects=True):
                pass
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Logout request failed (non-critical)")

        self._cookies = {}
        _LOGGER.debug("Logged out from Tauron eLicznik")

    async def test_connection(self) -> bool:
        """Test the connection by authenticating and fetching data."""
        await self.authenticate()
        await self.fetch_energy_data()
        await self.logout()
        return True
