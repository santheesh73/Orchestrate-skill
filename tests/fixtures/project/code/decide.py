"""Fixture: decision module with documented constants and no coupled literals."""

MIN_BUFFER = 50.0
STATUSES = ("approved", "wait", "declined")


def decide(balance, amount):
    if balance - amount < MIN_BUFFER:
        return "wait"
    return "approved"
