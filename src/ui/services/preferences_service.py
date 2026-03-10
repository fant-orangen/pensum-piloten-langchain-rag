"""Preferences service for updating user tutoring mode."""

from __future__ import annotations

from src.ui.services.api_client import ApiError, ApiUnauthorizedError, patch


def update_system_prompt_mode(token: str, mode: int) -> tuple[bool, str]:
    """Update the authenticated user's system prompt mode preference."""
    try:
        data = patch("/preferences/system-prompt", {"mode": mode}, token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        return False, f"Kunne ikke oppdatere veiledningsmodus: {exc.detail}"
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren."
    if not bool(data.get("success")):
        return False, str(data.get("message") or "Kunne ikke oppdatere veiledningsmodus.")
    return True, str(data.get("message") or "Veiledningsmodus oppdatert.")
