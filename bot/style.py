"""Style constants for consistent bot appearance."""

# Color palette - Soft cold colors
COLOR_INFO = "#5BA4E8"        # Sky blue - General information
COLOR_HELP = "#9B7EED"        # Soft purple - Help commands
COLOR_SUCCESS = "#7DD3C0"     # Mint - Success messages
COLOR_WARNING = "#FF8B7A"     # Coral - Warnings
COLOR_ERROR = "#F47A7A"       # Soft red - Errors
COLOR_FUN = "#E6A4B4"         # Soft pink - Fun/entertainment
COLOR_USER = "#B4A7D6"        # Lavender - User information
COLOR_SERVER = "#8DA3E8"      # Periwinkle - Server information

# Custom emoji IDs
EMOJI_YES = "01KK7EC8VP8CMKZW8SB64TCVTC"
EMOJI_NO = "01KK7ECH9ES9SRSB9REFGKZMFB"
EMOJI_WARNING = "01KK7ECQ187S2FZ2X3JS65R9PW"


def emoji(emoji_id: str) -> str:
    """Format an emoji ID for use in messages."""
    return f":{emoji_id}:"


def yes_emoji() -> str:
    """Get the formatted yes emoji."""
    return emoji(EMOJI_YES)


def no_emoji() -> str:
    """Get the formatted no emoji."""
    return emoji(EMOJI_NO)


def warning_emoji() -> str:
    """Get the formatted warning emoji."""
    return emoji(EMOJI_WARNING)
