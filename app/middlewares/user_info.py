from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request
import re

# import core
from app.core.dashboard_database import DashboardSessionLocal
from app.core.config import get_settings

# import models
from app.models.user_profile import UserProfile

# import services
from app.services.user_profile import UserProfileService

# import utils
from app.utils.misc import get_user_info_from_google


settings = get_settings()

MODE = settings.MODE
SKIP_AUTH_PATHS = {"/health", "/api/v1/auth/google/callback", "/server/api/v1/auth/google/callback"}
access_token_header = (
    "X-Amzn-Oidc-Accesstoken" if MODE == "production" else "X-Auth-Request-Access-Token"
)


class UserInfoMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_AUTH_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # Extract user info from request headers
        # user_info = {
        #     "email": request.headers.get("X-Auth-Request-Email"),
        #     "username": request.headers.get("X-Auth-Request-Preferred-Username"),
        #     "name": request.headers.get("X-Auth-Request-User"),
        #     "picture": request.headers.get("X-Auth-Request-Picture", None),
        #     "token": request.headers.get("X-Auth-Request-Access-Token", None),
        # }
        access_token = request.headers.get(access_token_header, None)

        if not access_token:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "No access token found",
                    "data": None,
                },
            )

        pattern = re.compile(r"^/api/v1/([^/]+)/user-profiles/my-profile$")

        # Check if the request path matches the pattern
        match = pattern.match(request.url.path)

        user_response = get_user_info_from_google(access_token)

        if user_response.status_code != 200:
            return JSONResponse(
                status_code=user_response.status_code, content=user_response.text
            )

        user_details = user_response.json()

        email = user_details.get("email")
        name = user_details.get("name") or ""
        picture = user_details.get("picture") or ""

        # If user info is not present, return an error response
        if not email:
            return JSONResponse(
                status_code=400,
                content={"detail": "User information missing in request headers"},
            )

        db = DashboardSessionLocal()
        try:
            # check if a user with the email is present in the profiles table
            user_profiles_response = (
                db.query(UserProfile)
                .filter(
                    UserProfile.email == email,
                )
                .all()
            )

            user_id = None

            if len(user_profiles_response) > 0:
                # user is present in the profiles table
                user_profile = user_profiles_response[0]
                user_id = user_profile.id
                user_profile_status = user_profile.status

                # if url_path != "/api/v1/user-profiles/my-profile" and user_profile_status == "pending".
                # means if the profile of the user is already created and user is trying to access data other than his own profile
                # but the profile status is pending, then return data = None
                if not match and user_profile_status == "pending":
                    if request.method == "GET":
                        return JSONResponse(status_code=200, content=[])
                    else:
                        return JSONResponse(
                            status_code=403, content={"detail": "Unauthorized"}
                        )
            else:
                # user is signing in first time to the application, hence
                # create new personal workspace and profile for the new user
                user_id = UserProfileService(db).create_new_user(email, name, picture)

                # if url_path != "/api/v1/user-profiles/my-profile":
                # means if the url matches above path only then we should forward the request to respective endpoint
                # if the url does not matches above path (means user is accessing data other than his own profile),
                # then we should send the data as empty array
                if not match:
                    return JSONResponse(status_code=200, content=[])
        finally:
            db.close()

        # Attach user_info and user_id to the request state so it's accessible later
        request.state.user_id = user_id
        # request.state.user_info = user_info

        # Call the next middleware or route handler
        response = await call_next(request)
        return response
