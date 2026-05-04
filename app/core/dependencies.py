from fastapi import HTTPException, Request


def get_current_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=403, detail="Unauthorized: User not logged in.")
    return user_id
