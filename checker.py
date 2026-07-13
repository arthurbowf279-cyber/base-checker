"""
Base Network Airdrop Activity Checker
======================================
Checks wallet activity on Base (L2) and scores airdrop eligibility.
Data source: BaseScan API (free key at basescan.org/apis)
"""

import sys
import requests
from datetime import datetime, timezone

BASESCAN_API = "https://api.basescan.org/api"

# Get free API key at https://basescan.org/apis
API_KEY = "YourApiKeyToken"  # replace with your key or leave for low-rate access


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_transactions(address):
    """Fetches all normal transactions for address on Base."""
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": API_KEY,
    }
    r = requests.get(BASESCAN_API, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data["status"] == "1":
        return data["result"]
    return []


def get_eth_balance(address):
    """Returns ETH balance in ETH."""
    params = {
        "module": "account",
        "action": "balance",
        "address": address,
        "tag": "latest",
        "apikey": API_KEY,
    }
    r = requests.get(BASESCAN_API, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data["status"] == "1":
        return int(data["result"]) / 1e18
    return 0.0


def get_token_transfers(address):
    """Fetches ERC-20 token transfers."""
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": API_KEY,
    }
    r = requests.get(BASESCAN_API, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data["status"] == "1":
        return data["result"]
    return []


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze(address, txs, token_txs, eth_balance):
    """Computes activity metrics from transaction history."""
    if not txs:
        return None

    # Timeline
    timestamps = [int(tx["timeStamp"]) for tx in txs]
    first_ts = min(timestamps)
    last_ts  = max(timestamps)
    first_dt = datetime.fromtimestamp(first_ts, tz=timezone.utc)
    last_dt  = datetime.fromtimestamp(last_ts,  tz=timezone.utc)
    age_days = (datetime.now(tz=timezone.utc) - first_dt).days

    # Unique active days
    active_days = len(set(
        datetime.fromtimestamp(ts, tz=timezone.utc).date()
        for ts in timestamps
    ))

    # Unique active weeks / months
    active_weeks  = len(set(
        (datetime.fromtimestamp(ts, tz=timezone.utc).isocalendar()[:2])
        for ts in timestamps
    ))
    active_months = len(set(
        (datetime.fromtimestamp(ts, tz=timezone.utc).year,
         datetime.fromtimestamp(ts, tz=timezone.utc).month)
        for ts in timestamps
    ))

    # Unique contracts interacted with
    contracts = set(
        tx["to"].lower() for tx in txs
        if tx.get("to") and tx["to"] != address.lower()
    )

    # Volume: total ETH sent (outgoing)
    vol_eth = sum(
        int(tx["value"]) / 1e18
        for tx in txs
        if tx["from"].lower() == address.lower()
    )

    # Token diversity
    unique_tokens = set(t.get("tokenSymbol", "") for t in token_txs)
    unique_tokens.discard("")

    # Failed tx count
    failed = sum(1 for tx in txs if tx.get("isError") == "1")

    return {
        "address":       address,
        "tx_count":      len(txs),
        "failed_txs":    failed,
        "first_tx":      first_dt.strftime("%Y-%m-%d"),
        "last_tx":       last_dt.strftime("%Y-%m-%d"),
        "wallet_age_days": age_days,
        "active_days":   active_days,
        "active_weeks":  active_weeks,
        "active_months": active_months,
        "unique_contracts": len(contracts),
        "volume_eth":    round(vol_eth, 4),
        "eth_balance":   round(eth_balance, 4),
        "unique_tokens": len(unique_tokens),
        "token_list":    sorted(unique_tokens)[:10],
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

CRITERIA = [
    ("tx_count",          10,   "10+ transactions",          1),
    ("tx_count",          50,   "50+ transactions",          2),
    ("tx_count",         100,   "100+ transactions",         3),
    ("active_days",        7,   "7+ active days",            1),
    ("active_days",       30,   "30+ active days",           2),
    ("active_weeks",       4,   "4+ active weeks",           2),
    ("active_months",      3,   "3+ active months",          2),
    ("active_months",      6,   "6+ active months",          3),
    ("wallet_age_days",   30,   "Wallet age 30+ days",       1),
    ("wallet_age_days",  180,   "Wallet age 180+ days",      2),
    ("unique_contracts",   5,   "5+ unique contracts",       2),
    ("unique_contracts",  20,   "20+ unique contracts",      3),
    ("volume_eth",       0.01,  "Sent 0.01+ ETH",            1),
    ("volume_eth",       0.1,   "Sent 0.1+ ETH",             2),
    ("unique_tokens",     3,    "3+ different tokens used",  1),
    ("unique_tokens",    10,    "10+ different tokens used", 2),
]

MAX_SCORE = sum(c[3] for c in CRITERIA)


def score(metrics):
    """Returns (total_score, max_score, list of (passed, points, label))."""
    results = []
    total = 0
    for field, threshold, label, pts in CRITERIA:
        passed = metrics[field] >= threshold
        if passed:
            total += pts
        results.append((passed, pts, label))
    return total, MAX_SCORE, results


def rating(total, max_score):
    """Returns emoji rating label."""
    pct = total / max_score
    if pct >= 0.80: return "🟢 EXCELLENT"
    if pct >= 0.55: return "🟡 GOOD"
    if pct >= 0.30: return "🟠 MODERATE"
    return "🔴 LOW"


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_report(metrics):
    """Prints the full analysis report to terminal."""
    total, max_s, checks = score(metrics)
    pct = round(total / max_s * 100)
    rat = rating(total, max_s)

    W = 58
    print()
    print("═" * W)
    print("  🔍 BASE NETWORK AIRDROP CHECKER")
    print("═" * W)
    print(f"  Address:      {metrics['address'][:20]}...{metrics['address'][-6:]}")
    print(f"  ETH Balance:  {metrics['eth_balance']} ETH")
    print()
    print("  📊 ACTIVITY METRICS")
    print("  " + "─" * (W - 2))
    print(f"  Transactions:     {metrics['tx_count']}  (failed: {metrics['failed_txs']})")
    print(f"  First tx:         {metrics['first_tx']}  ({metrics['wallet_age_days']} days ago)")
    print(f"  Last tx:          {metrics['last_tx']}")
    print(f"  Active days:      {metrics['active_days']}")
    print(f"  Active weeks:     {metrics['active_weeks']}")
    print(f"  Active months:    {metrics['active_months']}")
    print(f"  Unique contracts: {metrics['unique_contracts']}")
    print(f"  Volume sent:      {metrics['volume_eth']} ETH")
    print(f"  Tokens used:      {metrics['unique_tokens']}")
    if metrics['token_list']:
        print(f"  Token list:       {', '.join(metrics['token_list'])}")
    print()
    print("  ✅ AIRDROP CRITERIA")
    print("  " + "─" * (W - 2))
    for passed, pts, label in checks:
        icon = "✅" if passed else "❌"
        pts_str = f"+{pts}pt" if passed else f"  {pts}pt"
        print(f"  {icon}  {pts_str}  {label}")
    print()
    print("═" * W)
    print(f"  SCORE:  {total}/{max_s}  ({pct}%)   {rat}")
    print("═" * W)
    print()
    print("  ⚠️  Score is estimated. Actual eligibility depends on")
    print("     each project's specific snapshot criteria.")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point — reads address from args or prompts user."""
    if len(sys.argv) > 1:
        address = sys.argv[1].strip()
    else:
        address = input("Enter Base wallet address (0x...): ").strip()

    if not address.startswith("0x") or len(address) != 42:
        print("❌ Invalid address. Must be 0x... (42 chars)")
        sys.exit(1)

    print(f"\n  Fetching data for {address[:10]}... please wait")

    try:
        txs        = get_transactions(address)
        token_txs  = get_token_transfers(address)
        eth_bal    = get_eth_balance(address)
    except Exception as e:
        print(f"❌ API error: {e}")
        sys.exit(1)

    if not txs:
        print("  No transactions found on Base for this address.")
        sys.exit(0)

    metrics = analyze(address, txs, token_txs, eth_bal)
    print_report(metrics)


if __name__ == "__main__":
    main()
