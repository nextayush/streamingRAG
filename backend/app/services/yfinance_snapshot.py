from typing import Any

from app.services.stocks import STOCK_MAP


def build_market_snapshot(symbol: str, ticker: Any) -> str:
    name = STOCK_MAP.get(symbol, symbol)
    info = ticker.fast_info

    lines = [f"--- MARKET DATA FOR {name} ({symbol}) ---"]

    price = getattr(info, "last_price", None) or 0
    market_cap = getattr(info, "market_cap", None)
    if market_cap and market_cap > 0:
        if market_cap >= 1e12:
            cap_str = f"Market Cap: ${market_cap / 1e12:.2f}T."
        elif market_cap >= 1e9:
            cap_str = f"Market Cap: ${market_cap / 1e9:.2f}B."
        else:
            cap_str = f"Market Cap: ${market_cap / 1e6:.2f}M."
    else:
        cap_str = ""

    lines.append(f"[CURRENT STATUS]: Trading at ${price:,.2f}. {cap_str}".strip())

    history = ticker.history(period="1mo")
    if history is not None and not history.empty:
        high_1mo = history["High"].max()
        low_1mo = history["Low"].min()
        current_price = history["Close"].iloc[-1]
        start_price = history["Close"].iloc[0]
        pct_change = ((current_price - start_price) / start_price) * 100
        lines.append(
            f"[1-MONTH HISTORY]: High ${high_1mo:.2f}, Low ${low_1mo:.2f}, "
            f"1-Month Return: {pct_change:.2f}%, Latest Close: ${current_price:.2f}."
        )
    else:
        lines.append("[1-MONTH HISTORY]: Unable to load 1-month price history.")

    return "\n".join(lines)
