import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# 设置页面标题
st.set_page_config(page_title="黄金多空驱动力看板", layout="wide")
st.title("🏆 黄金驱动力实时热力图 (Beta)")

# 1. 定义因子和获取数据的 Ticker
# 逻辑：{'名称': [yfinance_ticker, 逻辑系数, 权重比例]}
# 逻辑系数: 1 表示正相关，-1 表示负相关
factors = {
    "黄金现货": ["GC=F", 1, 1.5],
    "美元指数": ["DX-Y.NYB", -1, 1.2],
    "10Y美债收益率": ["^TNX", -1, 1.5],
    "原油价格": ["CL=F", 1, 1.0],
    "VIX恐慌指数": ["^VIX", 1, 0.8],
    "日元汇率": ["JPY=X", -1, 0.7],  # 美元/日元，上升代表日元贬值，对黄金通常负向
    "标普500": ["^GSPC", -0.5, 0.6]
}

@st.cache_data(ttl=60) # 每 60 秒清理一次缓存
def fetch_data():
    results = []
    for name, info in factors.items():
        ticker = info[0]
        corr = info[1]
        weight_base = info[2]
        
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) >= 2:
            change = (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]
            impact = change * corr
            results.append({
                "因子": name,
                "涨跌幅": change,
                "影响值": impact,
                "绝对强度": abs(impact) * weight_base,
                "方向": "利多 (Green)" if impact > 0 else "利空 (Red)"
            })
    return pd.DataFrame(results)

# 获取数据
df = fetch_data()

# 2. 绘制热力图
fig = px.treemap(
    df,
    path=["因子"],
    values="绝对强度",
    color="影响值",
    color_continuous_scale=["#FF0000", "#FFFFFF", "#00FF00"], # 红-白-绿
    color_continuous_midpoint=0,
    hover_data=["涨跌幅", "方向"]
)

fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), height=600)

# 3. 展示
st.plotly_chart(fig, use_container_width=True)

# 自动刷新逻辑 (提示)
st.info("数据每 1 分钟自动刷新一次。")
