# Referral Credit Specification

## Purpose
How referral credit is recorded and spent.

## Requirements

### Requirement: Credit is recorded per customer
The ledger SHALL record each credit entry against the customer it belongs to. `P-1` `T-1 AC-1`

#### Scenario: One entry
- **WHEN** $10 of credit is added for customer c1
- **THEN** c1 has one ledger entry
