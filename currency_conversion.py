import requests
import time

class CurrencyConverter:
    """
    Fixer.io rates (free tier) are typically EUR-based.
    This class caches rates for 1 hour to avoid rate limits / slowness.
    """
    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self.rates: dict[str, float] = {}
        self.last_updated = 0.0
        self.base = "EUR"

    def update_rates(self):
        # If we already have rates updated within the last hour, reuse them.
        if self.rates and (time.time() - self.last_updated < 3600):
            return

        if not self.api_key:
            raise RuntimeError("FIXER_API_KEY is not set (needed for non-USD conversions).")

        url = f"https://data.fixer.io/api/latest?access_key={self.api_key}"
        res = requests.get(url, timeout=10).json()

        if not res.get("success"):
            # Fixer often returns an "error" object with details
            err = res.get("error", {})
            msg = err.get("info") or err.get("type") or "Currency API failed"
            raise RuntimeError(msg)

        self.rates = res.get("rates", {})
        self.last_updated = time.time()

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        self.update_rates()

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return round(amount, 2)

        if from_currency not in self.rates:
            raise RuntimeError(f"Missing rate for {from_currency}")
        if to_currency not in self.rates:
            raise RuntimeError(f"Missing rate for {to_currency}")

        # Convert from 'from_currency' -> EUR (base)
        amount_in_eur = amount / self.rates[from_currency]
        # Convert EUR -> 'to_currency'
        converted = amount_in_eur * self.rates[to_currency]
        return round(converted, 2)
