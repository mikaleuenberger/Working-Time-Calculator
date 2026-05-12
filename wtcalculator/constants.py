"""Application-wide constants."""

# Comment and name limits
COMMENT_MAX_LENGTH = 30
NAME_MAX_LENGTH = 50
EMAIL_MAX_LENGTH = 254  # RFC 5321
AGE_MIN = 14
AGE_MAX = 100

# Timezone
DEFAULT_TIMEZONE = "Europe/Zurich"

# Valid roles
VALID_ROLES = {"Mitarbeiter", "Vorgesetzter"}

# Work time rules
MIN_LUNCH_BREAK_MINUTES = 30
MAX_WEEKLY_HOURS = 45.0
MAX_DAILY_HOURS = 12.0
MIN_BREAK_FOR_AUTO_DEDUCT_HOURS = 6.0  # Auto-deduct 30min break if work >= this many hours
