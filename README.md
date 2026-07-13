# 🔍 Base Network Airdrop Checker

Check your wallet activity on Base (L2) and score your airdrop eligibility.

> ⚠️ Not financial advice. Scores are estimates based on common airdrop criteria.

## What it checks

- Total transactions & failed tx count
- Wallet age (days since first tx)
- Active days / weeks / months
- Unique smart contracts interacted with
- ETH volume sent
- ERC-20 token diversity
- Combined score with 🟢🟡🟠🔴 rating

## Setup

```bash
# 1. Get a free API key at https://basescan.org/apis
# 2. Open checker.py and set your key:
#    API_KEY = "your_key_here"

# 3. Install dependencies
pip install requests

# 4. Run
python checker.py 0xYOUR_WALLET_ADDRESS
```

## Example output

```
══════════════════════════════════════════════════════════
  🔍 BASE NETWORK AIRDROP CHECKER
══════════════════════════════════════════════════════════
  Address:      0x1234567890...a1b2c3
  ETH Balance:  0.2341 ETH

  📊 ACTIVITY METRICS
  ──────────────────────────────────────────────────────
  Transactions:     142  (failed: 3)
  First tx:         2023-08-15  (304 days ago)
  Active days:      47
  Active weeks:     21
  Active months:    9
  Unique contracts: 38
  Volume sent:      0.8412 ETH
  Tokens used:      12

  ✅ AIRDROP CRITERIA
  ──────────────────────────────────────────────────────
  ✅  +1pt  10+ transactions
  ✅  +2pt  50+ transactions
  ✅  +3pt  100+ transactions
  ✅  +2pt  30+ active days
  ✅  +2pt  4+ active weeks
  ...

══════════════════════════════════════════════════════════
  SCORE:  24/31  (77%)   🟢 EXCELLENT
══════════════════════════════════════════════════════════
```

## Stack

- **Python 3.8+**
- **requests** — HTTP calls to BaseScan API
- BaseScan API (free tier, no credit card)
