# Backlog

Tracker: local

## P-1 Referral credit
| Task | Title | Priority | Depends on | Modules | Status | Ticket |
|------|-------|----------|------------|---------|--------|--------|
| T-1 | Credit ledger | high | | credit | done | |
| T-2 | Apply credit at checkout | high | T-3 | credit, checkout | ready | |
| T-3 | Credit balance lookup | medium | T-1 | credit | ready | |
| T-4 | Credit history page | low | T-1 | credit, web | ready | |

Acceptance criteria
- T-2: Given a customer with $10 credit, when they check out, then $10 is deducted from the order total, once
- T-3: Given a customer with ledger entries, when their balance is requested, then it is the sum of their entries
- T-4: Given a customer with ledger entries, when they open the history page, then each entry shows its date and amount

## P-2 Referral links
| Task | Title | Priority | Depends on | Modules | Status | Ticket |
|------|-------|----------|------------|---------|--------|--------|
| T-6 | Share link button | medium | | referrals, web | ready | |

## P-3 Credit payouts
| Task | Title | Priority | Depends on | Modules | Status | Ticket |
|------|-------|----------|------------|---------|--------|--------|
| T-5 | Monthly payout export | high | | credit | ready | |

Acceptance criteria
- T-5: Given a month of credit entries, when finance exports it, then there is one row per customer with their total

## Waiting

## Delivered
