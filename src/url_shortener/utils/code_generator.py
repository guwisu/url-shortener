import string
from secrets import choice

ALPHABET = list(string.ascii_letters + string.digits)

def generate_short_code(length: int = 6):
    return "".join(choice(ALPHABET) for _ in range(length))
