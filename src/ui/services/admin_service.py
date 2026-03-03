"""Admin service — wraps /admin/* API endpoints."""

from __future__ import annotations

from typing import Any

from src.ui.services.api_client import ApiError, ApiUnauthorizedError, get, post


def list_users(token: str) -> tuple[list[dict[str, Any]], str]:
    """Fetch all users visible to an admin."""
    try:
        data = get("/admin/users", token=token)
    except ApiUnauthorizedError:
        return [], "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return [], "Ikke tillatt."
        return [], f"Kunne ikke hente brukere: {exc.detail}"
    except Exception as exc:
        return [], f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, list):
        return [], "Uventet svar fra serveren."
    return [u for u in data if isinstance(u, dict)], ""


def promote_user_to_teacher(token: str, user_id: str) -> tuple[bool, str]:
    """Promote one user to global teacher role."""
    try:
        post(f"/admin/users/{user_id}/promote-teacher", token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 400:
            return False, "Ikke tillatt."
        if exc.status == 403:
            return False, "Ikke tillatt."
        if exc.status == 404:
            return False, "Fant ikke brukeren."
        if exc.status == 409:
            return False, "Brukeren er allerede lærer."
        return False, f"Kunne ikke oppgradere bruker: {exc.detail}"
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}"

    return True, "Brukeren er oppgradert til lærer."
