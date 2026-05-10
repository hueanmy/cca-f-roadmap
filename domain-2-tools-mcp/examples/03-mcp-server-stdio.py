"""Minimal MCP server (stdio transport) — what the exam means by "MCP server".

Run this script directly and it will speak the MCP protocol over stdin/stdout.
Then in your Claude Code project, register it in `.mcp.json`:

    {
      "mcpServers": {
        "cca-f-demo": {
          "command": "uv",
          "args": ["run", "domain-2-tools-mcp/examples/03-mcp-server-stdio.py"]
        }
      }
    }

After registering, restart Claude Code and the `add_to_watchlist` and
`get_watchlist` tools become available. This is the same pattern every
production MCP server uses — the difference is just how many tools they expose.

Install MCP: `uv sync --group mcp`

CCA-F notes:
  - stdio = local subprocess, simplest to develop, can't be shared across machines
  - SSE is deprecated; use streamable HTTP for remote
  - Each tool description here lives on the SERVER; the client (Claude Code)
    fetches them on connect. Same description-quality rules apply.
"""
import json
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise SystemExit(
        "MCP not installed. Run: uv sync --group mcp\n"
        "Or: uv pip install mcp"
    )


WATCHLIST_FILE = Path(__file__).resolve().parent / ".watchlist.json"


def _load() -> list[dict]:
    if not WATCHLIST_FILE.exists():
        return []
    return json.loads(WATCHLIST_FILE.read_text())


def _save(items: list[dict]) -> None:
    WATCHLIST_FILE.write_text(json.dumps(items, indent=2))


mcp = FastMCP("cca-f-demo")


@mcp.tool()
def add_to_watchlist(ticker: str, reason: str) -> str:
    """Add a stock ticker to the user's personal watchlist with the reason for watching it.

    Use when the user says things like 'add NVDA to my watchlist' or 'I want to keep
    an eye on TSLA because of the earnings report'. The reason field is required so
    the user can recall their thesis later.
    """
    items = _load()
    items.append({"ticker": ticker.upper(), "reason": reason})
    _save(items)
    return f"Added {ticker.upper()} ({len(items)} items total)"


@mcp.tool()
def get_watchlist() -> str:
    """Return the user's current stock watchlist as a list of tickers and reasons.

    Use when the user asks 'what's on my watchlist', 'show me what I'm tracking',
    or before recommending stocks (so you don't suggest something they already track).
    """
    items = _load()
    if not items:
        return "Watchlist is empty."
    return "\n".join(f"- {it['ticker']}: {it['reason']}" for it in items)


if __name__ == "__main__":
    # FastMCP picks up the stdio transport automatically when launched
    # without args. Claude Code's MCP client speaks to us over stdin/stdout.
    mcp.run()
