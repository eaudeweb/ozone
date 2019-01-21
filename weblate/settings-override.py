import os

AUTHENTICATION_BACKENDS += ("social_core.backends.ozone.OzoneOAuth2",)
SOCIAL_AUTH_OZONE_KEY = os.environ.get("SOCIAL_AUTH_OZONE_KEY")
SOCIAL_AUTH_OZONE_SECRET = os.environ.get("SOCIAL_AUTH_OZONE_SECRET")
SOCIAL_AUTH_OZONE_SCOPE = ["read"]
SOCIAL_AUTH_OZONE_HOST = os.environ.get("SOCIAL_AUTH_OZONE_HOST")
SOCIAL_AUTH_OZONE_API_HOST = os.environ.get("SOCIAL_AUTH_OZONE_API_HOST")
ENABLE_SHARING = False
