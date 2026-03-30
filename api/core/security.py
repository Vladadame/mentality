def hmac_md5_hex(message: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.md5,
    ).hexdigest()