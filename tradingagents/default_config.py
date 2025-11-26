import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "deepseek",
    "deep_think_llm": "deepseek-reasoner",
    "quick_think_llm": "deepseek-chat",
    "backend_url": "https://api.deepseek.com/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: yfinance, alpha_vantage, local
        "technical_indicators": "yfinance",  # Options: yfinance, alpha_vantage, local
        "fundamental_data": "alpha_vantage", # Options: openai, alpha_vantage, local
        "news_data": "alpha_vantage",        # Options: openai, alpha_vantage, google, local
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_news": "openai",               # Override category default
    },
    # Optional paper-trading integration (Alpaca)
    "alpaca_paper_trading": {
        "enabled": True,  # Set True to place paper trades, otherwise False
        "api_key": os.getenv("ALPACA_API_KEY_ID"),
        "api_secret": os.getenv("ALPACA_API_SECRET_KEY"),
        "base_url": os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets"),
        "order_notional": float(os.getenv("ALPACA_ORDER_NOTIONAL", "1000")),  # USD notional per BUY/SELL
        "order_qty": float(os.getenv("ALPACA_ORDER_QTY", "1")),  # Share quantity per order
        "time_in_force": os.getenv("ALPACA_TIME_IN_FORCE", "day"),
        "extended_hours": os.getenv("ALPACA_EXTENDED_HOURS", "false").lower() == "true",
    },
}
