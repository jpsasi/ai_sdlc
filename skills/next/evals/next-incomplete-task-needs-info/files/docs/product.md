# Product: Referral

Synced: 2026-10-20

## Sources
| Ref | Type | Location | Version |
|-----|------|----------|---------|
| S-1 | local | docs/requirements/referral.md | 5e1f0c2a |

## Problem and goals
Customers refer friends; both earn checkout credit, which grows repeat purchases.

## Users
Customers of the shop.

## Capabilities
### P-1 Referral credit · S-1
A referred friend's first purchase gives both customers $10 of checkout credit.
Acceptance hints:
- credit is applied at checkout, at most once per order

### P-2 Referral links · S-1
Each customer has a shareable referral link.
Acceptance hints:
- the link is unique per customer

### P-3 Credit payouts · S-1 · Blocked by REF-7
Finance exports monthly credit totals.
Acceptance hints:
- one row per customer per month

## Non-functional requirements
NFR-1 Applying credit adds at most 50 ms to checkout.

## Constraints
- Node.js, no external services in tests.

## Out of scope
- Withdrawing credit as cash

## Clarifications
C-1 Can credit be withdrawn as cash? → No. Credit is spent at checkout only. (session, Sasi, 2026-10-20) · folded

## Known gaps

## Open questions
