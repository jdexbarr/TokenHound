"""Masking of secret values for display (spec section 4: secrets are never printed in full)."""

MASK_CHAR = "*"


def mask(secret: str) -> str:
    """Return ``secret`` with its middle replaced by ``*``.

    Long values keep 4 characters at each end so a human can recognise the key
    (``sk-a****************xYz9``, as in the spec). Shorter values reveal less, and values of
    9 characters or fewer are fully masked. The masked string has the same length as the secret.
    """
    length = len(secret)
    if length >= 20:
        visible = 4
    elif length >= 10:
        visible = 2
    else:
        visible = 0
    if visible == 0:
        return MASK_CHAR * length
    return secret[:visible] + MASK_CHAR * (length - 2 * visible) + secret[-visible:]
