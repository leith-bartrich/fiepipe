def is_dommain_or_subdomain(to_check: str, against: str) -> bool:
    if against.lower() == to_check.lower():
        return True
    if to_check.lower().endswith("." + against.lower()):
        return True
    return False
