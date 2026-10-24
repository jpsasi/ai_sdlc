# Architecture

## Modules
### credit
- Responsibility: the credit ledger, balances, spending credit
- Interface: `addEntry`, `balanceOf`
- May depend on: (nothing)
### checkout
- Responsibility: order totals
- May depend on: credit
### referrals
- Responsibility: referral links and sign-ups
- May depend on: credit
### web
- Responsibility: pages
- May depend on: credit, checkout, referrals

## Dependency rules
- credit depends on nothing; checkout, referrals → credit; web → any

## Capability map
| Capability | Modules |
|---|---|
| P-1 | credit, checkout |
| P-2 | referrals, web |
| P-3 | credit |
