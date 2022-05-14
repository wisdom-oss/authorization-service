import logging

import fastapi

from . import handlers
from . import user_api, scope_api, oauth_api

_logger = logging.getLogger(__name__)
"""The logger for all API activity"""

# %% API Setup
service = fastapi.FastAPI()


# %% API Endpoints
service.mount("/oauth", oauth_api.oauth_api)
service.mount("/users", user_api.user_api)
service.mount("/scopes", scope_api.scope_api)
