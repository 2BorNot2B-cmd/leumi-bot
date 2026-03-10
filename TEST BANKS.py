import yfinance as yf
import telebot
from telebot import types
import requests
import warnings
import os

warnings.filterwarnings("ignore")

# ─── CONFIGURATION ───────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GM_TOKEN = os.getenv("GM_TOKEN")

PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.leumi.iLeumiTrade.UI"

bot = telebot.TeleBot(BOT_TOKEN)

MARKET_INDEX_SYMBOL = "^TA125.TA"

BANKS = {
    "POLI.TA": {"name": "Hapoalim", "weight": 0.335},
    "LUMI.TA": {"name": "Leumi",    "weight": 0.285},
    "MZTF.TA": {"name": "Mizrahi", "weight": 0.175},
    "DSCT.TA": {"name": "Discount", "weight": 0.135},
    "FIBI.TA": {"name": "First Intl","weight": 0.070},
}

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def call_gemini(prompt: str) -> str | None:
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1200, "temperature": 0.85},
    }

    for model in GEMINI_MODELS:
        url = (
            f"https://generativelanguage.googleapis.com"
            f"/v1beta/models/{model}:generateContent"
            f"?key={GM_TOKEN}"
        )
        try:
            print(f"⏳ Trying: {model}")
            resp = requests.post(url, headers=headers, json=payload, timeout=20)

            if resp.status_code == 200:
                data = resp.json()
                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
                )
                if text:
                    print(f"✅ Success with: {model}")
                    return text
            elif resp.status_code == 404:
                print(f"❌ 404 on {model}, trying next...")
            else:
                print(f"❌ {resp.status_code}: {resp.text[:150]}")

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout on {model}")
        except Exception as e:
            print(f"❌ Exception: {e}")

    return None


def get_gemini_analysis(bank_results: list, bank_trend: float, market_change: float) -> str | None:
    summary = ", ".join([f"{b['name']} {b['change']:.2f}%" for b in bank_results])
    prompt = (
        f"Context: Today the Israeli banking sector moved {bank_trend:+.2f}% while the broader TA-125 index moved {market_change:+.2f}%. "
        f"Bank data: {summary}. "
        f"Write exactly 2 sentences of high-level financial analysis in English. "
        f"DO NOT use numbers or percentages. Focus on relative performance between banks and the market index. "
        f"Name the primary laggard, identify a macro cause, and provide a forward-looking sentiment. "
        f"Bloomberg style. Must end with a period. Keep it under 50 words."
    )
    return call_gemini(prompt)


def get_accurate_change(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="1d")
        if len(df) >= 2:
            prev = float(df["Close"].iloc[-2])
            curr = float(df["Close"].iloc[-1])
            change = ((curr - prev) / prev) * 100
            return curr, change
    except Exception as e:
        print(f"⚠️ yfinance error for {symbol}: {e}")
    return None, None


def run():
    print("🚀 Starting Israel Banking Sector Bot...")

    # משיכת מדד ת"א 125
    _, market_change = get_accurate_change(MARKET_INDEX_SYMBOL)

    results, weighted_sum = [], 0.0
    for symbol, info in BANKS.items():
        price, change = get_accurate_change(symbol)
        if price is not None:
            results.append({"name": info["name"], "change": change})
            weighted_sum += change * info["weight"]

    if not results or market_change is None:
        print("❌ No data. Aborting.")
        return

    ai_insight = get_gemini_analysis(results, weighted_sum, market_change)

    if not ai_insight:
        leader = max(results, key=lambda x: abs(x["change"]))
        direction = "advances" if weighted_sum > 0 else "declines"
        ai_insight = (
            f"The Israeli banking sector {direction}, "
            f"with {leader['name']} leading the move, "
            f"reflecting broader market sentiment shifts."
        )

    # חיתוך בנקודה האחרונה
    if "." in ai_insight:
        ai_insight = ai_insight[:ai_insight.rfind(".") + 1]

    # HTML encoding
    ai_insight_safe = (
        ai_insight
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    icon   = "🟢" if weighted_sum > 0 else "🔴"
    m_icon = "📈" if market_change > 0 else "📉"

    lines = [
        "🏛 <b>ISRAEL BANKING SECTOR: INTELLIGENCE REPORT</b>",
        f"📊 Sector Trend: <b>{weighted_sum:+.2f}%</b> {icon}",
        f"{m_icon} TA-125 Index: <code>{market_change:+.2f}%</code>",
        "──────────────────",
    ]

    sorted_results = sorted(results, key=lambda x: x["change"], reverse=True)
    for b in sorted_results:
        b_icon = "🟢" if b["change"] > 0 else "🔴"
        lines.append(f"{b_icon} {b['name']}: <code>{b['change']:+.2f}%</code>")

    lines += [
        "──────────────────",
        "🤖 <b>AI STRATEGIC INSIGHT (Gemini 2.5):</b>",
        ai_insight_safe,
    ]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Open Leumi Trade", url=PLAY_STORE_URL))

    try:
        bot.send_message(
            CHAT_ID,
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=markup,
        )
        print("✅ Message sent!")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")


if __name__ == "__main__":
    run()
