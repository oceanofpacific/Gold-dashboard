import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests

# --- 新增：设置伪装浏览器的 Session ---
def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

# 设置页面
st.set_page_config(page_title="黄金驱动力看板", layout="wide")
st.title("🏆 黄金驱动力实时热力图")

factors = {
    "黄金现货": ["GC=F", 1, 1.5],
    "美元指数": ["DX-Y.NYB", -1, 1.2],
    "10Y美债收益率": ["^TNX", -1, 1.5],
    "原油价格": ["CL=F", 1, 1.0],
    "VIX恐慌指数": ["^VIX", 1, 0.8]
}

@st.cache_data(ttl=300) # 建议把缓存时间稍微调长一点（5分钟），减少请求频率
def fetch_data():
    results = []
    session = get_session() # 获取伪装的 Session
    
    for name, info in factors.items():
        ticker_symbol = info[0]
        corr = info[1]
        weight_base = info[2]
        
        try:
            # 关键：在 Ticker 中传入 session
            ticker = yf.Ticker(ticker_symbol, session=session)
            data = ticker.history(period="5d") # 稍微多取几天确保有数据
            
            if not data.empty and len(data) >= 2:
                change = (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]
                impact = change * corr
                results.append({
                    "因子": name,
                    "涨跌幅": change,
                    "影响值": impact,
                    "绝对强度": abs(impact) * weight_base,
                    "方向": "利多 (Green)" if impact > 0 else "利空 (Red)"
                })
        except Exception as e:
            st.warning(f"无法获取 {name} 的数据: {e}")
            
    return pd.DataFrame(results)

# 后面绘图的代码保持不变...
df = fetch_data()
if not df.empty:
    fig = px.treemap(df, path=["因子"], values="绝对强度", color="影响值",
                     color_continuous_scale=["#FF0000", "#FFFFFF", "#00FF00"],
                     color_continuous_midpoint=0)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("所有因子数据获取失败，请稍后再试或检查网络。")
