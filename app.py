import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import requests

# 1. 針對手機板進行網頁優化
st.set_page_config(
    page_title="MEXC AI 交易終端", 
    layout="centered", # 手機版適合集中排版，不適合寬版
    initial_sidebar_state="collapsed" # 預設隱藏側邊欄，留給手機更多空間
)

# 讓手機介面更好看的微調樣式
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 100%; padding-top: 1rem; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🏹 MEXC 智能多空終端")
st.caption("📱 iPhone 專屬優化量化交易決策系統")

# 初始化 MEXC
mexc = ccxt.mexc({'enableRateLimit': True})

def fetch_real_crypto_news():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        response = requests.get(url, timeout=5)
        data = response.json()
        return [{"title": item['title'], "source": item['source_info']['name']} for item in data['Data'][:3]]
    except:
        return [{"title": "市場宏觀數據穩定，靜待突破。", "source": "系統"}]

def analyze_technical_indicators(symbol, timeframe):
    try:
        ohlcv = mexc.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.atr(length=14, append=True)
        
        latest = df.iloc[-1]
        return {
            "price": latest['close'], "rsi": latest['RSI_14'],
            "macd": latest['MACD_12_26_9'], "signal": latest['MACDS_12_26_9'], "atr": latest['ATR_14']
        }
    except:
        return None

# 手機版下拉選單改放到主畫面上方，方便點選
target_coin = st.selectbox("🎯 選擇幣種", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"])
time_frame = st.selectbox("⏳ 週期 (長短線)", ["15m", "1h", "4h", "1d"], index=1)

data = analyze_technical_indicators(target_coin, time_frame)
news_list = fetch_real_crypto_news()

# 計算新聞情緒分數 (簡單關鍵字過濾)
news_score = 0.0
for n in news_list:
    text = n['title'].lower()
    if any(w in text for w in ['bull', 'buy', 'surge', 'pump', 'up']): news_score += 0.3
    if any(w in text for w in ['bear', 'sell', 'drop', 'dump', 'down', 'hack']): news_score -= 0.35

if data:
    st.divider()
    # 手機並排顯示重要數據
    col1, col2 = st.columns(2)
    col1.metric("當前價格", f"${data['price']:,}")
    col2.metric("RSI 指標", f"{data['rsi']:.1f}")
    
    # 判斷邏輯
    tech_score = 0.0
    if data['rsi'] < 32: tech_score += 0.4
    if data['rsi'] > 68: tech_score -= 0.4
    if data['macd'] > data['signal']: tech_score += 0.4
    if data['macd'] < data['signal']: tech_score -= 0.4
    
    final_score = (tech_score * 0.6) + (news_score * 0.4)
    atr = data['atr']
    
    st.write("### 🤖 AI 綜合決策")
    if final_score > 0.2:
        st.success("📈 【建議做多 (Long)】")
        st.write(f"🟢 **進場點：** 現價附近 (${data['price']})")
        st.write(f"🛑 **止損點 (SL)：** `${data['price'] - (2*atr):.4f}`")
        st.write(f"💰 **止盈點 (TP)：** `${data['price'] + (4*atr):.4f}`")
    elif final_score < -0.2:
        st.error("📉 【建議做空 (Short)】")
        st.write(f"🔴 **進場點：** 現價附近 (${data['price']})")
        st.write(f"🛑 **止損點 (SL)：** `${data['price'] + (2*atr):.4f}`")
        st.write(f"💰 **止盈點 (TP)：** `${data['price'] - (4*atr):.4f}`")
    else:
        st.warning("⏳ 【訊號不明，建議觀望】")

st.divider()
