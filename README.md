# Airdrop Discovery System

A system that leverages the DeFilLama API to automatically discover and rank promising DeFi projects with high airdrop potential.

## Features

- 🪂 **Tokenless Detection** - Automatically identifies projects that haven't launched a token yet.
- 💰 **VC Analysis** - Prioritizes projects backed by Tier-1 VCs like a16z, Dragonfly, and Binance Labs.
- 📊 **Smart Scoring** - Calculates airdrop probabilities based on TVL growth, funding amount, VC quality, and project stage.
- 💎 **Hidden Gem Discovery** - Highlights early-stage, low-TVL projects with strong backing.
- 🎨 **HTML Dashboard** - Generates a visual dashboard to explore and filter rankings.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Generate dashboard and open in browser
python main.py

# View top 20 candidates in console
python main.py --console --top 20

# Test API connectivity
python main.py --test-api

# Clear cache and fetch fresh data
python main.py --clear-cache
```

## Scoring Criteria (v2.1)

| Criterion | Max Points | Description |
|-----------|------------|-------------|
| Tier 1: Core Signal | 40 | Tokenless (+12), Points (+15), High Airdrop VC (+13) |
| Tier 2: Quality | 35 | Funding Amount (+15), Tier-1 VC (+12), Tier-2 VC (+8) |
| Tier 3: Timing | 25 | Recency (+10), Project Stage - Seed/Series A (+10) |
| Tier 4: Bonus | 30 | TVL Growth (+8), Hidden Gem (+10), Category (+5) |

## File Structure

```
├── main.py              # Entry point
├── defillama_client.py  # DeFilLama API Client
├── airdrop_scorer.py    # Scoring Engine
├── dashboard.py         # HTML Dashboard Generator
├── requirements.txt     # Dependencies
└── output/              # Generated Dashboards
```

## Data Source

- [DeFilLama](https://defillama.com/) - DeFi Protocol TVL & Funding Data
