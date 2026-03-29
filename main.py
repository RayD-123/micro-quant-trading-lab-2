import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import os

def run_quant_ultimate():
    tz_ny = pytz.timezone('America/New_York')
    ny_now = datetime.now(tz_ny)
    ny_time = ny_now.strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 启动量化系统 6.0 | 纽约时间: {ny_time}")
    
    ticker_list = []
    df_targets = pd.DataFrame()

    try:
        from finvizfinance.screener.financial import Financial
        from finvizfinance.screener.overview import Overview

        # 1. 扩大范围：全美股 + 市值 > 20亿
        filters = {'Market Cap.': '+Mid (over $2bln)'} 
        
        print("🌐 抓取 Finviz 数据 (Financial + Overview)...")
        fsf = Financial()
        fsf.set_filter(filters_dict=filters)
        df_fin = fsf.screener_view()
        
        fso = Overview()
        fso.set_filter(filters_dict=filters)
        df_ov = fso.screener_view()
        
        # 2. 智能清洗 ROE
        def smart_clean(x):
            if pd.isna(x) or x == '-': return np.nan
            if isinstance(x, str):
                try: return float(x.replace('%', '')) / 100
                except: return np.nan
            return float(x)

        df_fin['ROE_val'] = df_fin['ROE'].apply(smart_clean)
        
        # 3. 合并数据（加入 Sector 和 Industry）
        # Overview 视图包含：Ticker, Sector, Industry, P/E, Price
        df_merged = pd.merge(
            df_fin[['Ticker', 'ROE_val']], 
            df_ov[['Ticker', 'Sector', 'Industry', 'P/E', 'Price']], 
            on='Ticker'
        )
        
        df_merged['PE_val'] = pd.to_numeric(df_merged['P/E'], errors='coerce')
        
        # 4. 核心筛选逻辑
        df_targets = df_merged[
            (df_merged['ROE_val'] > 0.15) & 
            (df_merged['PE_val'] < 25)
        ].copy()
        
        ticker_list = df_targets['Ticker'].tolist()
        print(f"🎯 选出 {len(ticker_list)} 只基本面标的")

    except Exception as e:
        generate_empty_report(ny_time, f"数据源抓取失败: {str(e)}")
        return

    if not ticker_list:
        generate_empty_report(ny_time, "今日无符合基本面条件的标的")
        return

    # --- 5. 技术面扫描 (YFinance) ---
    print(f"Downloading {len(ticker_list)} tickers...")
    data = yf.download(ticker_list, period="1y", interval="1d", group_by='ticker', threads=True, progress=False)

    results = []
    if len(ticker_list) == 1: data = {ticker_list[0]: data}

    # 计算 20d 动量排名
    all_rets = {}
    for t in ticker_list:
        try:
            close = data[t]['Close'].dropna()
            if len(close) > 21:
                all_rets[t] = (close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]
        except: continue
    
    m_threshold = pd.Series(all_rets).quantile(0.60) if all_rets else 0

    for t in ticker_list:
        try:
            hist = data[t].dropna()
            if len(hist) < 200: continue
            
            close = hist['Close']
            price = float(close.iloc[-1])
            ma200 = close.rolling(200).mean().iloc[-1]
            vol = ((hist['High'] - hist['Low']) / close).tail(14).mean()
            
            # 趋势与动量过滤
            if (price > ma200) and (all_rets.get(t, 0) >= m_threshold) and (vol < 0.05):
                # RSI 计算
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
                
                row = df_targets[df_targets['Ticker'] == t].iloc[0]
                
                results.append({
                    '代码': f"**{t}**",
                    '行业': row['Sector'],
                    'PE': f"{row['PE_val']:.1f}",
                    'ROE': f"{row['ROE_val']:.1%}",
                    '20d动量': f"{all_rets.get(t, 0):.1%}",
                    'RSI': f"{rsi:.1f}",
                    '动作建议': "🟢 超卖买入" if rsi < 40 else ("🔴 超买止盈" if rsi > 75 else "🟡 趋势持有")
                })
        except: continue

    save_report(ny_time, results)

def save_report(ny_time, results):
    report = f"# 🦅 量化狙击手 6.0 报告\n\n"
    report += f"**🗽 纽约时间: {ny_time}** (开盘/收盘自动更新)\n"
    report += f"> 策略：全美股 + 绩优(ROE>15%) + 估值(PE<25) + 趋势(RSI/MA)\n\n"
    
    if results:
        # 按动量排序
        df_res = pd.DataFrame(results).sort_values(by='20d动量', ascending=False)
        report += df_res.to_markdown(index=False)
        report += "\n\n### 💡 交易指南\n- **🟢 超卖买入**：基本面强劲但短期回调，适合建仓。\n- **🟡 趋势持有**：上涨趋势健康，继续持有。\n- **🔴 超买止盈**：短期涨幅过大，建议减仓或分批止盈。"
    else:
        report += "### ⚠️ 今日技术面暂无最佳切入点。"

    with open("report_smart.md", "w", encoding="utf-8") as f:
        f.write(report)

def generate_empty_report(ny_time, reason):
    report = f"# 🦅 量化狙击手 6.0 报告\n\n**🗽 纽约时间: {ny_time}**\n\n❌ {reason}"
    with open("report_smart.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    run_quant_ultimate()
