from fastapi import Request, Header, HTTPException
from helpers.types import PcPlatform


def get_user_platform(request: Request, user_agent: str = Header(None)) -> PcPlatform:
    """
    pass this function to the dependencies parameter of a route to set the user's platform
    """
    platform: PcPlatform

    if "Windows" in user_agent:
        platform = PcPlatform.WINDOWS
    elif "Macintosh" in user_agent:
        platform = PcPlatform.MAC
    elif "Linux" in user_agent:
        platform = PcPlatform.LINUX
    else:
        raise HTTPException(status_code=400, detail={"error": "Invalid platform"})

    return platform
