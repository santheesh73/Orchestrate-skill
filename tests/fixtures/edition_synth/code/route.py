"""Locker Desk router (synthetic fixture for the dry run; never imported by tests).

The model fills `threat` and `bypass_request` booleans from the message; this code decides.
"""

MAX_WEIGHT_KG = 30.0  # carrier limit, problem_statement.md rule 1
SIZES = ("S", "M", "L")  # smallest first, rule 2
PRIORITY = ("escalate", "reject", "assign")  # conflict order from the problem statement


def decide(row, record):
    if record["threat"] or record["bypass_request"]:
        return "escalate", "none"
    if float(row["weight_kg"]) > MAX_WEIGHT_KG:
        return "reject", "none"
    return "assign", min((s for s in SIZES if SIZES.index(s) >= SIZES.index(row["parcel_size"])), key=SIZES.index)
