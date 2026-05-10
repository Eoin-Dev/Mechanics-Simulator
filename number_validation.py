import re

def is_valid_number(
    s: str
) -> bool:
    return bool(re.fullmatch(r'-?\d+(\.\d+)?', s))