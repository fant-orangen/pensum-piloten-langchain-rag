import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from src.api.dependencies import get_current_app_user, get_current_user
from src.api.models.user import User
from src.api.routers import admin, auth, conversations, courses, preferences


def _route_dependency_calls(route: APIRoute) -> set[object]:
    return {dependency.call for dependency in route.dependant.dependencies}


@pytest.mark.asyncio
async def test_get_current_app_user_rejects_forced_password_users() -> None:
    user = User(
        email="imported@student.test",
        hashed_password="",
        first_name="Imported",
        last_name="Student",
        must_change_password=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_app_user(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Password change required before using this endpoint."


@pytest.mark.asyncio
async def test_get_current_app_user_allows_users_with_password_set() -> None:
    user = User(
        email="student@test.com",
        hashed_password="hash",
        first_name="Ready",
        last_name="Student",
        must_change_password=False,
    )

    assert await get_current_app_user(user) is user


def test_normal_app_routes_require_password_setup_completion() -> None:
    for router in (admin.router, conversations.router, courses.router, preferences.router):
        for route in router.routes:
            if not isinstance(route, APIRoute):
                continue

            assert get_current_app_user in _route_dependency_calls(route)


def test_auth_setup_routes_remain_available_to_forced_password_users() -> None:
    auth_dependency_calls_by_path = {
        route.path: _route_dependency_calls(route)
        for route in auth.router.routes
        if isinstance(route, APIRoute)
    }

    assert get_current_user in auth_dependency_calls_by_path["/auth/me"]
    assert get_current_app_user not in auth_dependency_calls_by_path["/auth/me"]
    assert get_current_user in auth_dependency_calls_by_path["/auth/change-password"]
    assert get_current_app_user not in auth_dependency_calls_by_path["/auth/change-password"]
