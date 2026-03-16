# market-events

Reports upcoming earnings, dividends, and stock splits for a watchlist of tickers using the [Financial Modeling Prep](https://financialmodelingprep.com/) API.

See [SKILL.md](SKILL.md) for full usage documentation.

## Setup

```bash
pip install -r requirements.txt
export FMP_API_KEY="your_api_key"
```

## Examples

```bash
python market-events.py --tickers AAPL,MSFT,GOOG
python market-events.py --file watchlist.txt --range 14d
python market-events.py --tickers NVDA --types earnings --format json
```
