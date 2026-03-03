"""Auth service — wraps /auth/login and /auth/register API endpoints."""

from __future__ import annotations

from typing import Any

from src.ui.services.api_client import ApiError, ApiUnauthorizedError, get, post


def login(email: str, password: str) -> tuple[bool, str, dict[str, Any] | None]:
    """Authenticate against the API.

    Returns:
        (success, message, user_info)

        On success, user_info is a dict with keys:
            token, email, first_name, last_name, global_role
        On failure, user_info is None.
    """
    try:
        token_data = post("/auth/login", {"email": email, "password": password})
    except ApiError as exc:
        if exc.status == 401:
            return False, "Feil e-post eller passord.", None
        return False, f"Innlogging feilet: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    access_token = token_data.get("access_token", "") if isinstance(token_data, dict) else ""
    if not access_token:
        return False, "Innlogging feilet: ugyldig svar fra serveren.", None

    return True, "Du er nå logget inn.", {"token": access_token}


def current_user(token: str) -> tuple[bool, str, dict[str, Any] | None]:
    """Fetch the authenticated user's profile from /auth/me."""
    try:
        data = get("/auth/me", token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        return False, f"Kunne ikke hente brukerprofil: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None
    return True, "", data


def register(
    email: str,
    password: str,
    password_confirm: str,
    first_name: str,
    last_name: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Register a new user account via the API.

    Returns:
        (success, message, user_info)

        On success, user_info is a dict with keys:
            email, first_name, last_name, global_role
        On failure, user_info is None.
    """
    if password != password_confirm:
        return False, "Passordene er ikke like.", None

    try:
        user_data = post(
            "/auth/register",
            {
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
    except ApiError as exc:
        if exc.status == 409:
            return False, "En konto med denne e-postadressen finnes allerede.", None
        if exc.status == 422:
            return False, "Ugyldig inndata. Kontroller e-post og passord (minimum 8 tegn).", None
        return False, f"Registrering feilet: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(user_data, dict):
        return False, "Registrering feilet: ugyldig svar fra serveren.", None

    return True, "Registrering fullført.", user_data
