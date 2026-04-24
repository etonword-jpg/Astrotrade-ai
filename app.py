import streamlit as st
import yfinance as yf
import pandas_ta as ta
import google.generativeai as genai
import ephem
import math
from datetime import datetime, timedelta

# ============================================================
# ตั้งค่าหน้าเว็บ
# ============================================================
st.set_page_config(
    page_title="AstroTrade",
    page_icon="🌟",
    layout="centered"
)

st.markdown("""
<style>
    .brand-title {
        font-size: 2.8em;
        font-weight: 900;
        background: linear-gradient(90deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: 3px;
    }
    .brand-sub {
        text-align: center;
        color: #aaaacc;
        font-size: 0.95em;
        margin-top: -10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-title">✦ AstroTrade</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Where the Stars Meet the Market 🌌📈🪙</div>', unsafe_allow_html=True)
st.divider()

# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ ตั้งค่า")
    gemini_key = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="รับฟรีที่ https://aistudio.google.com/app/apikey"
    )
    st.divider()
    st.markdown("**📌 วิธีใช้**")
    st.markdown("1. ใส่ Gemini API Key")
    st.markdown("2. เลือกประเภท: หุ้น / Crypto")
    st.markdown("3. ป้อนชื่อหรือเลือกจากรายการ")
    st.markdown("4. ใส่วันเกิด")
    st.markdown("5. กด **วิเคราะห์**")
    st.divider()
    st.markdown("**🌟 AstroTrade**")
    st.caption("Where the Stars Meet the Market")
    st.caption("⚠️ ไม่ใช่คำแนะนำทางการเงิน")

# ============================================================
# รายการ Crypto
# ============================================================
CRYPTO_LIST = {
    "-- พิมพ์เอง --"         : "",
    "Bitcoin (BTC)"          : "BTC-USD",
    "Ethereum (ETH)"         : "ETH-USD",
    "Solana (SOL)"           : "SOL-USD",
    "XRP"                    : "XRP-USD",
    "BNB"                    : "BNB-USD",
    "Dogecoin (DOGE)"        : "DOGE-USD",
    "Cardano (ADA)"          : "ADA-USD",
    "Avalanche (AVAX)"       : "AVAX-USD",
    "Chainlink (LINK)"       : "LINK-USD",
    "Polygon (POL)"          : "POL-USD",
    "Polkadot (DOT)"         : "DOT-USD",
    "Litecoin (LTC)"         : "LTC-USD",
    "Uniswap (UNI)"          : "UNI-USD",
    "Cosmos (ATOM)"          : "ATOM-USD",
    "Shiba Inu (SHIB)"       : "SHIB-USD",
    "Pepe (PEPE)"            : "PEPE-USD",
    "Toncoin (TON)"          : "TON-USD",
    "Near Protocol (NEAR)"   : "NEAR-USD",
    "Aptos (APT)"            : "APT-USD",
    "Sui (SUI)"              : "SUI-USD",
}

STOCK_SUGGESTIONS = {
    "-- พิมพ์เอง --" : "",
    "NVIDIA"         : "NVDA",
    "Apple"          : "AAPL",
    "Tesla"          : "TSLA",
    "Microsoft"      : "MSFT",
    "Meta"           : "META",
    "Amazon"         : "AMZN",
    "Google"         : "GOOGL",
    "CPALL (ไทย)"    : "CPALL.BK",
    "PTT (ไทย)"      : "PTT.BK",
    "SCB (ไทย)"      : "SCB.BK",
    "KBANK (ไทย)"    : "KBANK.BK",
    "AOT (ไทย)"      : "AOT.BK",
}

# ============================================================
# ฟังก์ชันดึงข้อมูล
# ============================================================
def get_stock_data(symbol: str, is_crypto: bool = False):
    try:
        df = yf.Ticker(symbol).history(period="3mo")
        if df.empty:
            return None

        df["RSI"]  = ta.rsi(df["Close"], length=14)
        df["MA20"] = df["Close"].rolling(20).mean()
        df["MA50"] = df["Close"].rolling(50).mean()
        df["ATR"]  = ta.atr(df["High"], df["Low"], df["Close"], length=14)
        bb = ta.bbands(df["Close"], length=20)
        df["BB_upper"] = bb["BBU_20_2.0"]
        df["BB_lower"] = bb["BBL_20_2.0"]

        price      = df["Close"].iloc[-1]
        prev_price = df["Close"].iloc[-2]
        rsi        = df["RSI"].iloc[-1]
        ma20       = df["MA20"].iloc[-1]
        ma50       = df["MA50"].iloc[-1]
        atr        = df["ATR"].iloc[-1]
        bb_upper   = df["BB_upper"].iloc[-1]
        bb_lower   = df["BB_lower"].iloc[-1]
        change     = price - prev_price
        change_pct = (change / prev_price) * 100
        support    = df["Low"].tail(20).min()
        resistance = df["High"].tail(20).max()

        # สัญญาณ
        if rsi <= 35 and price <= bb_lower and ma20 > ma50 * 0.98:
            signal      = "🟢 BUY"
            entry       = round(price, 2)
            stop_loss   = round(price - (atr * 1.5), 2)
            take_profit = round(price + (atr * 3), 2)
        elif rsi >= 65 and price >= bb_upper:
            signal      = "🔴 SELL"
            entry       = round(price, 2)
            stop_loss   = round(price + (atr * 1.5), 2)
            take_profit = round(price - (atr * 3), 2)
        else:
            signal      = "🟡 WAIT"
            entry       = round(bb_lower, 2)
            stop_loss   = round(bb_lower - (atr * 1.5), 2)
            take_profit = round(bb_upper, 2)

        rr = round(abs(take_profit - entry) / abs(entry - stop_loss), 2) if entry != stop_loss else 0

        # format ราคา crypto (ถ้าน้อยกว่า 1 ใช้ทศนิยมมากขึ้น)
        decimals = 6 if is_crypto and price < 0.01 else (4 if is_crypto and price < 1 else 2)

        return {
            "symbol"      : symbol,
            "price"       : round(price, decimals),
            "change_pct"  : round(change_pct, 2),
            "arrow"       : "▲" if change >= 0 else "▼",
            "rsi"         : round(rsi, 2),
            "rsi_signal"  : "Overbought" if rsi >= 70 else ("Oversold" if rsi <= 30 else "Neutral"),
            "ma20"        : round(ma20, decimals),
            "ma50"        : round(ma50, decimals),
            "ma_signal"   : "Golden Cross ☀️" if ma20 > ma50 else "Death Cross 💀",
            "support"     : round(support, decimals),
            "resistance"  : round(resistance, decimals),
            "signal"      : signal,
            "entry"       : round(entry, decimals),
            "stop_loss"   : round(stop_loss, decimals),
            "take_profit" : round(take_profit, decimals),
            "rr_ratio"    : rr,
            "is_crypto"   : is_crypto,
            "close_series": df["Close"],
        }
    except Exception as e:
        st.error(f"❌ ดึงข้อมูลไม่ได้: {e}")
        return None

# ============================================================
# ฟังก์ชันดาว
# ============================================================
def get_zodiac(lon_deg):
    signs = [
        ("Aries","เมษ"), ("Taurus","พฤษภ"), ("Gemini","เมถุน"),
        ("Cancer","กรกฎ"), ("Leo","สิงห์"), ("Virgo","กันย์"),
        ("Libra","ตุลย์"), ("Scorpio","พิจิก"), ("Sagittarius","ธนู"),
        ("Capricorn","มกร"), ("Aquarius","กุมภ์"), ("Pisces","มีน"),
    ]
    return signs[int(lon_deg // 30) % 12]

def get_planet_positions(date_utc):
    bkk = ephem.Observer()
    bkk.lat, bkk.lon, bkk.elevation = "13.75", "100.517", 0
    bkk.date = date_utc
    planets = {
        "Sun": ephem.Sun(), "Moon": ephem.Moon(),
        "Mercury": ephem.Mercury(), "Venus": ephem.Venus(),
        "Mars": ephem.Mars(), "Jupiter": ephem.Jupiter(),
        "Saturn": ephem.Saturn(),
    }
    result = {}
    for name, planet in planets.items():
        planet.compute(bkk)
        lon = math.degrees(ephem.Ecliptic(planet).lon) % 360
        en, th = get_zodiac(lon)
        result[name] = {"lon": round(lon, 1), "en": en, "th": th}
    return result

def get_astro_today():
    now_utc = datetime.now() - timedelta(hours=7)
    pos = get_planet_positions(now_utc)
    lines = []
    for name, d in pos.items():
        lines.append(f"{name:8s} → ราศี{d['th']} / {d['en']} ({d['lon']}°)")
    return "\n".join(lines), pos

def get_birth_sign(birth_str):
    try:
        bd = datetime.strptime(birth_str, "%d/%m/%Y") - timedelta(hours=7)
        pos = get_planet_positions(bd)
        return pos["Sun"]["en"], pos["Sun"]["th"]
    except:
        return None, None

def get_weekly_days():
    now      = datetime.now()
    monday   = now - timedelta(days=now.weekday())
    days     = ["จันทร์","อังคาร","พุธ","พฤหัส","ศุกร์","เสาร์","อาทิตย์"]
    fire_air = ["Aries","Leo","Sagittarius","Gemini","Libra","Aquarius"]
    result   = []
    for i in range(7):
        day = monday + timedelta(days=i)
        pos = get_planet_positions(day - timedelta(hours=7))
        score = sum([
            pos["Mercury"]["en"] in fire_air,
            pos["Moon"]["en"]    in fire_air,
            day.weekday() in [0, 3, 4],
        ])
        verdict = "🟢 ดีมาก" if score >= 3 else ("🟡 พอใช้" if score == 2 else "🔴 ระวัง")
        result.append({
            "date"    : day.strftime("%d/%m"),
            "day"     : days[i],
            "verdict" : verdict,
            "moon"    : pos["Moon"]["en"],
            "is_today": day.date() == now.date(),
        })
    return result

# ============================================================
# ฟังก์ชัน Gemini
# ============================================================
def analyze(stock, astro_str, sign_th, sign_en, weekly, birth_date, api_key):
    genai.configure(api_key=api_key)
    model      = genai.GenerativeModel("gemini-1.5-flash")
    weekly_str = "\n".join(
        [f"  {d['date']} ({d['day']}) → {d['verdict']} | Moon: {d['moon']}" for d in weekly]
    )
    asset_type = "Cryptocurrency" if stock["is_crypto"] else "หุ้น"

    prompt = f"""คุณคือ "AstroTrade AI" ผู้เชี่ยวชาญด้านกราฟเทคนิคและโหราศาสตร์การเงิน
มีสไตล์การพูดที่มั่นใจ ฉลาด และมีเสน่ห์

=== ข้อมูลเทคนิค {asset_type}: {stock['symbol']} ===
ราคา: {stock['price']} USD ({stock['arrow']}{abs(stock['change_pct'])}%)
RSI: {stock['rsi']} ({stock['rsi_signal']}) | {stock['ma_signal']}
Support: {stock['support']} | Resistance: {stock['resistance']}
{"⚡ หมายเหตุ: Crypto เปิด 24 ชม. ความผันผวนสูงกว่าหุ้นปกติ" if stock['is_crypto'] else ""}

=== สัญญาณเทรด ===
สัญญาณ: {stock['signal']}
ราคาเข้า: {stock['entry']} | SL: {stock['stop_loss']} | TP: {stock['take_profit']}
Risk/Reward: 1:{stock['rr_ratio']}

=== ดาววันนี้ ===
{astro_str}

=== ดวงชะตาเจ้าของพอร์ต ===
วันเกิด: {birth_date} | ราศี: {sign_th} ({sign_en})

=== วันดี/วันร้ายสัปดาห์นี้ ===
{weekly_str}

วิเคราะห์ครบทุกหัวข้อ:
1. 📊 สรุปเทคนิค RSI + MA บอกอะไร
2. 🎯 ฟันธง BUY / SELL / WAIT พร้อมราคาเข้า SL TP ชัดเจน
3. 🪐 ดาวพฤหัส+พุธวันนี้เอื้อต่อการเทรด{asset_type}ไหม
4. 🔮 ราศี{sign_th}เข้ากับ {stock['symbol']} ไหม วิเคราะห์แบบสนุกๆ มีลูกเล่น
5. 📅 วันที่ดีที่สุดในสัปดาห์นี้สำหรับ{asset_type}ตัวนี้
6. 💬 คำคมปิดท้ายสไตล์ AstroTrade

ตอบภาษาไทย มีบุคลิก กระชับ ฟังดูเท่และน่าเชื่อถือ"""

    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return f"❌ Gemini error: {e}"

# ============================================================
# UI หลัก
# ============================================================

# เลือกประเภท
asset_type = st.radio(
    "เลือกประเภทสินทรัพย์",
    ["📈 หุ้น (Stock)", "🪙 Crypto"],
    horizontal=True
)
is_crypto = asset_type == "🪙 Crypto"

# เลือกสินทรัพย์
if is_crypto:
    col1, col2 = st.columns([1, 1])
    with col1:
        crypto_select = st.selectbox("🪙 เลือก Crypto", list(CRYPTO_LIST.keys()))
    with col2:
        crypto_manual = st.text_input("หรือพิมพ์เอง", placeholder="เช่น SOL-USD")

    if CRYPTO_LIST[crypto_select]:
        symbol = CRYPTO_LIST[crypto_select]
    else:
        symbol = crypto_manual.upper().strip()
else:
    col1, col2 = st.columns([1, 1])
    with col1:
        stock_select = st.selectbox("📈 เลือกหุ้น", list(STOCK_SUGGESTIONS.keys()))
    with col2:
        stock_manual = st.text_input("หรือพิมพ์เอง", placeholder="เช่น NVDA หรือ CPALL.BK")

    if STOCK_SUGGESTIONS[stock_select]:
        symbol = STOCK_SUGGESTIONS[stock_select]
    else:
        symbol = stock_manual.upper().strip()

# วันเกิด
birth = st.text_input("🎂 วันเกิดของคุณ", placeholder="DD/MM/YYYY เช่น 15/06/1990")

# ปุ่มวิเคราะห์
run = st.button("✦ วิเคราะห์ด้วย AstroTrade", use_container_width=True, type="primary")

if run:
    if not gemini_key:
        st.warning("⚠️ กรุณาใส่ Gemini API Key ที่ sidebar ก่อนครับ")
    elif not symbol:
        st.warning("⚠️ กรุณาเลือกหรือพิมพ์ชื่อสินทรัพย์")
    elif not birth:
        st.warning("⚠️ กรุณาใส่วันเกิด")
    else:
        label = "Crypto" if is_crypto else "หุ้น"
        with st.spinner(f"⏳ กำลังดึงข้อมูล {symbol}..."):
            stock = get_stock_data(symbol, is_crypto)

        if not stock:
            st.error(f"❌ ไม่พบข้อมูล '{symbol}'")
            if not is_crypto:
                st.info("💡 หุ้นไทยต่อท้าย .BK เช่น CPALL.BK | หุ้นสหรัฐใช้ชื่อตรง เช่น NVDA")
            else:
                st.info("💡 Crypto ต้องต่อท้าย -USD เช่น BTC-USD, ETH-USD")
        else:
            # กราฟ
            icon = "🪙" if is_crypto else "📊"
            st.subheader(f"{icon} {stock['symbol']}")
            st.line_chart(stock["close_series"])

            # เมตริก
            m1, m2, m3 = st.columns(3)
            m1.metric("ราคา (USD)", stock["price"], f"{stock['arrow']}{abs(stock['change_pct'])}%")
            m2.metric("RSI", stock["rsi"], stock["rsi_signal"])
            m3.metric("สัญญาณ", stock["signal"])

            if is_crypto:
                st.info("⚡ Crypto เปิดตลาด 24 ชม. ความผันผวนสูง ควรใช้ Position Size เล็กกว่าหุ้นปกติ")

            # Signal Box
            clr = "#00c853" if "BUY" in stock["signal"] else ("#ff1744" if "SELL" in stock["signal"] else "#ffa000")
            st.markdown(f"""
            <div style='background:#111133; border-left:5px solid {clr};
                        padding:18px; border-radius:10px; margin:12px 0'>
                <h3 style='color:{clr}; margin:0 0 10px 0'>{stock['signal']}</h3>
                <table style='width:100%; color:#eee; font-size:0.95em'>
                    <tr><td>🎯 ราคาเข้า</td><td><b>{stock['entry']}</b></td></tr>
                    <tr><td>🛑 Stop Loss</td><td><b style='color:#ff6b6b'>{stock['stop_loss']}</b></td></tr>
                    <tr><td>✅ Take Profit</td><td><b style='color:#69f0ae'>{stock['take_profit']}</b></td></tr>
                    <tr><td>⚖️ Risk/Reward</td><td><b>1 : {stock['rr_ratio']}</b></td></tr>
                    <tr><td>🔵 Support</td><td>{stock['support']}</td></tr>
                    <tr><td>🔴 Resistance</td><td>{stock['resistance']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

            # ดาว
            with st.spinner("🔭 คำนวณตำแหน่งดาว..."):
                astro_str, today_pos = get_astro_today()
            with st.expander("🪐 ตำแหน่งดาววันนี้"):
                st.code(astro_str)

            # ดวงชะตา
            sign_en, sign_th = get_birth_sign(birth)
            if sign_th:
                st.markdown(f"""
                <div style='background:#1a1a2e; border:1px solid #FFD700;
                            padding:12px; border-radius:10px; text-align:center'>
                    <b style='color:#FFD700; font-size:1.1em'>
                        ♈ ราศีเกิดของคุณ: {sign_th} ({sign_en})
                    </b>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ รูปแบบวันเกิดไม่ถูกต้อง ใช้ DD/MM/YYYY")
                sign_en, sign_th = "Unknown", "ไม่ทราบ"

            # วันดี/วันร้าย
            st.subheader("📅 วันดี/วันร้ายสัปดาห์นี้")
            weekly = get_weekly_days()
            cols   = st.columns(7)
            for i, d in enumerate(weekly):
                with cols[i]:
                    st.markdown(f"**{'📍' if d['is_today'] else ''}{d['day']}**")
                    st.caption(d["date"])
                    st.markdown(d["verdict"])

            # AI วิเคราะห์
            st.subheader("🤖 AstroTrade AI Analysis")
            with st.spinner("✨ กำลังอ่านดวงและวิเคราะห์ตลาด..."):
                result = analyze(stock, astro_str, sign_th, sign_en, weekly, birth, gemini_key)
            st.markdown(result)

            st.divider()
            st.markdown(
                "<div style='text-align:center; color:#666; font-size:0.8em'>"
                "✦ AstroTrade — Where the Stars Meet the Market 🌌<br>"
                "⚠️ เป็นข้อมูลประกอบการตัดสินใจเท่านั้น ไม่ใช่คำแนะนำทางการเงิน"
                "</div>",
                unsafe_allow_html=True
            )
