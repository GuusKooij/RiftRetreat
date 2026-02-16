"""API key manager with obfuscation to hide production key in source code."""

import base64
import os


def _decode_key(encoded: str) -> str:
    """Decode an obfuscated API key.

    Args:
        encoded: Base64-encoded API key

    Returns:
        Decoded API key string
    """
    try:
        decoded_bytes = base64.b64decode(encoded.encode('utf-8'))
        return decoded_bytes.decode('utf-8')
    except Exception:
        return ""


def get_production_api_key() -> str:
    """Get the production API key (obfuscated in source code).

    To update the production key:
    1. Get your API key (e.g., "RGAPI-12345678-abcd-1234-efgh-123456789012")
    2. Encode it: base64.b64encode(b"YOUR_KEY_HERE").decode()
    3. Replace the ENCODED_KEY below with the output

    This provides basic obfuscation to prevent casual viewing of the key
    in the source code. It's not encryption - anyone can decode it - but
    it keeps the key from being immediately visible.
    """
    # Production API key (Base64 encoded for obfuscation)
    # This key is usable by all users who download RiftRetreat from GitHub
    # It's encoded to prevent casual viewing, but can be decoded if needed
    # To update: python -c "import base64; print(base64.b64encode(b'YOUR_KEY_HERE').decode())"
    ENCODED_KEY = "UkdBUEktM2ZkYjBlMzMtMDY4Zi00ZjVmLWEzODktNjM4NDdiMzRiZDZi"

    return _decode_key(ENCODED_KEY)


def get_riot_api_key() -> str:
    """Get Riot API key with priority: .env > production key.

    Returns:
        API key string, or empty string if none available
    """
    # First priority: .env file (for development or users who want their own key)
    env_key = os.getenv('RIOT_API_KEY')
    if env_key:
        return env_key

    # Second priority: Production key (obfuscated)
    return get_production_api_key()
