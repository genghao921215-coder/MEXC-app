import streamlit as st
import ccxt
import pandas as pd
import requests
import ta  # 更換為更穩定的技術指標庫

# 1. 針對手機板進行網頁優化
st.set_page_config(
    page_title="MEXC AI 交易終端", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

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
        
        # 使用 ta 庫計算指標
        df['RSI_14'] = ta.momentum.rsi(df['close'], window=14)
        
        macd_obj = ta.trend.MACD(df['close'], window_fast=12, window_slow=26, window_sign=9)
        df['MACD'] = macd_obj.macd()
        df['MACD_Signal'] = macd_obj.macd_signal()
        
        df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        
        latest = df.iloc[-1]
        return {
            "price": latest['close'], "rsi": latest['RSI_14'],
            "macd": latest['MACD'], "signal": latest['MACD_Signal'], "atr": latest['ATR']
        }
    except:
        return None

# 下拉選單
target_coin = st.selectbox("🎯 選擇幣種", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"])
time_frame = st.selectbox("⏳ 週期 (長短線)", ["15m", "1h", "4h", "1d"], index=1)

data = analyze_technical_indicators(target_coin, time_frame)
news_list = fetch_real_crypto_news()

# 計算新聞情緒分數
news_score = 0.0
for n in news_list:
    text = n['title'].lower()
    if any(w in text for w in ['bull', 'buy', 'surge', 'pump', 'up']): news_score += 0.3
    if any(w in text for w in ['bear', 'sell', 'drop', 'dump', 'down', 'hack']): news_score -= 0.35

if data:
    st.divider()
    col1, col2 = st.columns(2)
    col1.metric("當前價格", f"${data['price']:,}")
    
    # 處理 RSI 可能為空值的情況
    rsi_val = data['rsi'] if pd.notna(data['rsi']) else 50.0
    col2.metric("RSI 指標", f"{rsi_val:.1f}")
    
    # 判斷邏輯
    tech_score = 0.0
    if rsi_val < 32: tech_score += 0.4
    if rsi_val > 68: tech_score -= 0.4
    
    if pd.notna(data['macd']) and pd.notna(data['signal']):
        if data['macd'] > data['signal']: tech_score += 0.4
        if data['macd'] < data['signal']: tech_score -= 0.4
    
    final_score = (tech_score * 0.6) + (news_score * 0.4)
    atr = data['atr'] if pd.notna(data['atr']) else (data['price'] * 0.01)
    
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
st.write("### 📰 即時情報與情緒評分")
st.metric("消息綜合得分", f"{news_score:.2f}")
for n in news_list:
    st.caption(f"📌 {n['title']} ({n['source']})")
