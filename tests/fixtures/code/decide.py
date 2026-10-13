"""Fixture: a tiny decision module for the interview drill test."""
import statistics

MIN_BALANCE_BUFFER = 50.0
MAX_STEPS = 8


def decide(balance, history, options, client):
    spend = statistics.median(history)
    if balance - spend < MIN_BALANCE_BUFFER * 1.5:
        return "wait"
    if spend > 0.35 * balance:
        return "partial"
    best = sorted(options, key=lambda o: (o["total"], o["start"]))[0]
    client.create(model="x", temperature=0, max_tokens=512)
    return best
