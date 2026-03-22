def validate_message(msg):
    return isinstance(msg, str) and bool(msg.strip())
