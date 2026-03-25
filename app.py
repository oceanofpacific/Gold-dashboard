import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# 1. 页面配置
st.set_page_config(page_title="Gold Logic Dashboard", layout="wide")
st.title("🏆 黄金驱动力实时热力图 (波动率加权版)")

# 2. 因子配置：Ticker, 逻辑相关性(1正/-1负), 基础权重
# 相关性逻辑：1表示同向波动利多黄金，-1表示反向波动利多黄金
FACTOR_CONFIG = {
    "黄金现货": {"ticker": "GC=F", "corr": 1, "base": 1.5},
    "美元指数": {"ticker": "DX-Y.NYB", "corr": -1, "base": 1.2},
    "10Y美债收益率": {"ticker": "^TNX", "corr": -1, "base": 1.4},
    "原油价格": {"ticker": "CL=F", "corr": 1, "base": 0.8},
    "VIX恐慌指数": {"ticker": "^VIX", "corr": 1, "base": 0.6},
    "日元汇率": {"ticker": "JPY=X", "corr": -1, "base": 0.5}
}

@st.cache_data(ttl=600)
def get_gold_data():
    results = []
    for name, cfg in FACTOR_CONFIG.items():
        try:
            # 获取5天数据计算波动率
            df_ticker = yf.Ticker(cfg['ticker']).history(period="5d")
            if len(df_ticker) < 2: continue
            
            # 计算指标
            last_close = df_ticker['Close'].iloc[-1]
            prev_close = df_ticker['Close'].iloc[-2]
            daily_return = (last_close - prev_close) / prev_close
            
            # 核心算法：面积由 (当日波动幅度 / 历史波动均值) * 基础权重 决定
            # 这里简化为：当日波动的绝对值 * 基础权重
            volatility_factor = abs(daily_return) * 100 
            area_weight = volatility_factor * cfg['base']
            
            # 计算对黄金的影响方向
            impact_value = daily_return * cfg['corr']
            
            results.append({
                "因子": name,
                "当前价": f"{last_close:.2f}",
                "涨跌幅": daily_return,
                "影响值": impact_value,
                "权重面积": area_weight,
                "逻辑状态": "利多 (Bullish)" if impact_value > 0 else "利空 (Bearish)"
            })
        except Exception as e:
            st.error(f"{name} 数据获取失败: {e}")
    return pd.DataFrame(results)

# 3. 运行逻辑
data = get_gold_data()

if not data.empty:
    # 绘制热力图
    fig = px.treemap(
        data,
        path=["因子"],
        values="权重面积", # 决定方块大小
        color="影响值",    # 决定颜色深度
        color_continuous_scale=["#FF4B4B", "#31333F", "#00CC66"], # 红-灰-绿
        color_continuous_midpoint=0,
        hover_data=["当前价", "涨跌幅", "逻辑状态"]
    )
    
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=500)
    st.plotly_chart(fig, use_container_width=True)

    # 数据表补充
    st.subheader("📊 详细因子列表")
    st.dataframe(data[["因子", "当前价", "逻辑状态", "权重面积"]].sort_values(by="权重面积", ascending=False))
else:
    st.info("数据加载中，请稍后...")

# 提示栏
st.caption("注：面积越大代表该因子目前的市场波动贡献度越高。")