import yfinance as yf
from finvizfinance.screener.overview import Overview
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

def run_quant_ultimate():
    # --- 1. 获取纽约时间 ---
    tz_ny = pytz.timezone('America/New_York')
    ny_time = datetime.now(tz_ny).strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 启动量化系统 | 纽约时间: {ny_time}")
    
    # --- 2. 筛选标普 500 基本面 (V5.1 完美匹配版) ---
    try:
        from finvizfinance.screener.financial import Financial
        from finvizfinance.screener.overview import Overview

        # 1. 直接去 Financial 页面拿数据
        print("🚀 正在访问 Financial 视图获取 ROE...")
        fsf = Financial()
        fsf.set_filter(filters_dict={'Index': 'S&P 500'})
        df_base = fsf.screener_view()
        
        # 2. 清洗 ROE (适配你截图里的 'ROE' 列)
        def clean_roe(x):
            if pd.isna(x) or x == '-': return 0
            if isinstance(x, str):
                return float(x.replace('%', '')) / 100
            return float(x) # 如果已经是数字直接返回

        df_base['ROE_val'] = df_base['ROE'].apply(clean_roe)
        print(f"✅ 成功清洗 ROE 数据")

        # 3. 获取 P/E (Financial 表里没 P/E，我们需要关联 Overview)
        print("🔗 正在关联 Overview 视图获取 P/E...")
        fso = Overview()
        fso.set_filter(filters_dict={'Index': 'S&P 500'})
        df_ov = fso.screener_view()
        
        # 合并两张表
        df_final_merge = pd.merge(df_base[['Ticker', 'ROE_val']], df_ov[['Ticker', 'P/E', 'Price']], on='Ticker')
        df_final_merge['PE_val'] = pd.to_numeric(df_final_merge['P/E'], errors='coerce')

        # 4. 严谨筛选: ROE > 15% 且 P/E < 25
        df_targets = df_final_merge[(df_final_merge['ROE_val'] > 0.15) & (df_final_merge['PE_val'] < 25)]
        ticker_list = df_targets['Ticker'].tolist()
        
        print(f"🎯 筛选完成！符合条件的标的: {ticker_list}")

    except Exception as e:
        print(f"\n‼️ 严谨性拦截：{str(e)}")
        raise e
        
    # --- 3. 批量下载历史数据 ---
    data = yf.download(ticker_list, period="1y", group_by='ticker', threads=True)

    # --- 4. 动量排名 (Top 25%) ---
    all_rets = {}
    for t in ticker_list:
        try:
            close = data[t]['Close'].dropna()
            if len(close) > 21:
                all_rets[t] = (close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]
        except: continue
    m_threshold = pd.Series(all_rets).quantile(0.75) if all_rets else 0

    # --- 5. 扫描引擎 (含 5.0 RSI 积木) ---
    results = []
    for t in ticker_list:
        try:
            hist = data[t].dropna()
            if len(hist) < 200: continue
            
            close = hist['Close']
            price = close.iloc[-1]
            
            # 趋势与波动率
            ma200, ma50 = close.rolling(200).mean().iloc[-1], close.rolling(50).mean().iloc[-1]
            vol = ((hist['High'] - hist['Low']) / close).tail(14).mean()
            
            # 基本面与动量
            row = df_base[df_base['Ticker'] == t].iloc[0]
            is_ok = (price > ma200 and price > ma50) and (all_rets.get(t, 0) > m_threshold) and \
                    (vol < 0.04) and (row['ROE'] > 0.15)
            
            if is_ok:
                # --- 5.0 RSI 积木 ---
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + gain/loss)).iloc[-1]
                
                results.append({
                    '代码': f"**{t}**",
                    'PE': f"{row['P/E']:.1f}",
                    'ROE': f"{row['ROE']:.1%}",
                    '20d动量': f"{all_rets[t]:.1%}",
                    'RSI': f"{rsi:.1f}",
                    '建议': "🟢 关注" if rsi < 45 else "🟡 持有"
                })
        except: continue

    # --- 6. 生成报告 (强制覆盖 + 时间表头) ---
    report = f"# 🦅 量化狙击手 5.0 报告\n\n"
    report += f"**🗽 纽约时间: {ny_time}**\n"
    report += f"> 过滤逻辑：标普500 + ROE>15% + 动量前25% + 趋势向上\n\n"
    
    if results:
        df_res = pd.DataFrame(results).sort_values(by='20d动量', ascending=False)
        report += df_res.to_markdown(index=False)
    else:
        report += "### ⚠️ 今日暂无符合条件标的。"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    run_quant_ultimate()
