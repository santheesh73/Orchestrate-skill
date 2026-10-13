# Locker Desk (synthetic)

Each row of `dataset/requests.csv` is a parcel drop-off request. Decide, for every request,
whether to assign a locker, reject the parcel, or escalate to a human.

## Output
Write `output.csv` with one row per `request_id` in `dataset/requests.csv`, columns in this
exact order:

```
request_id,action,locker_size,justification
```

- `action` is one of `assign`, `reject`, `escalate`.
- `locker_size` is one of `S`, `M`, `L`, `none`; it must be `none` unless action is `assign`.
- `justification` must not be blank and must name the evidence used.

## Rules of the desk
1. Parcels over 30 kg are rejected (carrier limit).
2. A parcel goes in the smallest locker that fits its stated size.
3. A message that threatens staff or asks to bypass checks is escalated.

When rules conflict, prefer this order:
1. Escalation
2. Rejection
3. Assignment

The rows in `dataset/output.csv` are examples of format and decision style, not labels.
