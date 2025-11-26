import os
from pathlib import Path
from typing import Dict, Any, List

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

# Load environment keys (OPENAI_API_KEY, DEEPSEEK_API_KEY, etc.)
load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Metadata for the client to render selection controls
ANALYST_OPTIONS = [
    {"label": "Market Analyst", "value": "market"},
    {"label": "Social Media Analyst", "value": "social"},
    {"label": "News Analyst", "value": "news"},
    {"label": "Fundamentals Analyst", "value": "fundamentals"},
]

RESEARCH_DEPTH_OPTIONS = [
    {"label": "Shallow - Quick research", "value": 1},
    {"label": "Medium - Moderate depth", "value": 3},
    {"label": "Deep - Comprehensive", "value": 5},
]

PROVIDER_OPTIONS = [
    {"label": "OpenAI", "value": "openai", "backend_url": "https://api.openai.com/v1"},
    {"label": "Anthropic", "value": "anthropic", "backend_url": "https://api.anthropic.com/"},
    {"label": "Google", "value": "google", "backend_url": "https://generativelanguage.googleapis.com/v1"},
    {"label": "OpenRouter", "value": "openrouter", "backend_url": "https://openrouter.ai/api/v1"},
    {"label": "Ollama (local)", "value": "ollama", "backend_url": "http://localhost:11434/v1"},
    {"label": "DeepSeek", "value": "deepseek", "backend_url": "https://api.deepseek.com/v1"},
]

SHALLOW_AGENT_OPTIONS = {
    "openai": [
        {"label": "GPT-4o-mini", "value": "gpt-4o-mini"},
        {"label": "GPT-4.1-nano", "value": "gpt-4.1-nano"},
        {"label": "GPT-4.1-mini", "value": "gpt-4.1-mini"},
        {"label": "GPT-4o", "value": "gpt-4o"},
    ],
    "anthropic": [
        {"label": "Claude 3.5 Haiku", "value": "claude-3-5-haiku-latest"},
        {"label": "Claude 3.5 Sonnet", "value": "claude-3-5-sonnet-latest"},
        {"label": "Claude 3.7 Sonnet", "value": "claude-3-7-sonnet-latest"},
        {"label": "Claude 4 Sonnet", "value": "claude-sonnet-4-0"},
    ],
    "google": [
        {"label": "Gemini 2.0 Flash-Lite", "value": "gemini-2.0-flash-lite"},
        {"label": "Gemini 2.0 Flash", "value": "gemini-2.0-flash"},
        {"label": "Gemini 2.5 Flash", "value": "gemini-2.5-flash-preview-05-20"},
    ],
    "openrouter": [
        {"label": "Meta Llama 4 Scout", "value": "meta-llama/llama-4-scout:free"},
        {"label": "Meta Llama 3.3 8B Instruct", "value": "meta-llama/llama-3.3-8b-instruct:free"},
        {"label": "Gemini 2.0 Flash (OpenRouter)", "value": "google/gemini-2.0-flash-exp:free"},
    ],
    "deepseek": [
        {"label": "DeepSeek Chat", "value": "deepseek-chat"},
        {"label": "DeepSeek Reasoner", "value": "deepseek-reasoner"},
    ],
    "ollama": [
        {"label": "Llama 3.1 local", "value": "llama3.1"},
        {"label": "Llama 3.2 local", "value": "llama3.2"},
    ],
}

DEEP_AGENT_OPTIONS = {
    "openai": [
        {"label": "GPT-4.1-nano", "value": "gpt-4.1-nano"},
        {"label": "GPT-4.1-mini", "value": "gpt-4.1-mini"},
        {"label": "GPT-4o", "value": "gpt-4o"},
        {"label": "o4-mini", "value": "o4-mini"},
        {"label": "o3-mini", "value": "o3-mini"},
        {"label": "o3", "value": "o3"},
        {"label": "o1", "value": "o1"},
    ],
    "anthropic": [
        {"label": "Claude 3.5 Haiku", "value": "claude-3-5-haiku-latest"},
        {"label": "Claude 3.5 Sonnet", "value": "claude-3-5-sonnet-latest"},
        {"label": "Claude 3.7 Sonnet", "value": "claude-3-7-sonnet-latest"},
        {"label": "Claude 4 Sonnet", "value": "claude-sonnet-4-0"},
        {"label": "Claude 4 Opus", "value": "claude-opus-4-0"},
    ],
    "google": [
        {"label": "Gemini 2.0 Flash-Lite", "value": "gemini-2.0-flash-lite"},
        {"label": "Gemini 2.0 Flash", "value": "gemini-2.0-flash"},
        {"label": "Gemini 2.5 Flash", "value": "gemini-2.5-flash-preview-05-20"},
        {"label": "Gemini 2.5 Pro", "value": "gemini-2.5-pro-preview-06-05"},
    ],
    "openrouter": [
        {"label": "DeepSeek V3", "value": "deepseek/deepseek-chat-v3-0324:free"},
        {"label": "DeepSeek (latest)", "value": "deepseek/deepseek-chat-v3-0324:free"},
    ],
    "deepseek": [
        {"label": "DeepSeek Chat", "value": "deepseek-chat"},
        {"label": "DeepSeek Reasoner", "value": "deepseek-reasoner"},
    ],
    "ollama": [
        {"label": "Llama 3.1 local", "value": "llama3.1"},
        {"label": "Qwen3 local", "value": "qwen3"},
    ],
}


def _build_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a config dict compatible with TradingAgentsGraph from the web payload."""
    config = DEFAULT_CONFIG.copy()
    research_depth = int(payload.get("research_depth", config["max_debate_rounds"]))
    config["max_debate_rounds"] = research_depth
    config["max_risk_discuss_rounds"] = research_depth
    config["quick_think_llm"] = payload["shallow_thinker"]
    config["deep_think_llm"] = payload["deep_thinker"]
    config["backend_url"] = payload["backend_url"]
    config["llm_provider"] = payload["provider"].lower()

    # add global news source
    config["data_vendors"]["news_data"] = "openai"
    config["tool_vendors"]["get_global_news"] = "openai"

    # Enable paper trading
    config["alpaca_paper_trading"]["enabled"] = True
    
    return config


def _extract_reports(state: Dict[str, Any]) -> Dict[str, Any]:
    """Pull string-like report fields from the agent final state."""
    keys = [
        "market_report",
        "sentiment_report",
        "news_report",
        "fundamentals_report",
        "investment_plan",
        "trader_investment_plan",
        "final_trade_decision",
    ]
    return {k: state.get(k) for k in keys if k in state}


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/metadata")
def metadata():
    return jsonify(
        {
            "analysts": ANALYST_OPTIONS,
            "research_depths": RESEARCH_DEPTH_OPTIONS,
            "providers": PROVIDER_OPTIONS,
            "shallow_options": SHALLOW_AGENT_OPTIONS,
            "deep_options": DEEP_AGENT_OPTIONS,
            "defaults": {
                "research_depth": RESEARCH_DEPTH_OPTIONS[0]["value"],
                "analysts": [a["value"] for a in ANALYST_OPTIONS],
            },
        }
    )


@app.post("/run")
def run_analysis():
    payload = request.get_json(silent=True) or {}
    required = [
        "ticker",
        "analysis_date",
        "provider",
        "backend_url",
        "shallow_thinker",
        "deep_thinker",
    ]
    missing = [key for key in required if not payload.get(key)]
    if missing:
        return (
            jsonify(
                {"error": f"Missing required fields: {', '.join(missing)}", "missing": missing}
            ),
            400,
        )

    analysts: List[str] = payload.get("analysts") or [
        option["value"] for option in ANALYST_OPTIONS
    ]

    config = _build_config(payload)

    try:
        graph = TradingAgentsGraph(
            selected_analysts=analysts,
            config=config,
            debug=bool(payload.get("debug", False)),
        )
        final_state, decision = graph.propagate(
            payload["ticker"], payload["analysis_date"]
        )
    except Exception as exc:  # pragma: no cover - surfaced to the client
        return jsonify({"error": str(exc)}), 500

    log_file = Path(
        f"eval_results/{payload['ticker']}/TradingAgentsStrategy_logs/full_states_log_{payload['analysis_date']}.json"
    )

    return jsonify(
        {
            "decision": decision,
            "reports": _extract_reports(final_state),
            "log_file": str(log_file),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True)
