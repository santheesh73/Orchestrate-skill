"""Fixture: rules keyed on dataset values (what corpus_literals must catch)."""

SPECIAL_USERS = {"u_7Q2"}
LAPTOP = "buy laptop"
LIMITS = (1200.50, 90)
STATUS = "approved"
SHORT = "rent"


def rule(row):
    return row["user_id"] in SPECIAL_USERS
