import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import os

def run_quant_ultimate():
    # --- 1. 获取纽约时间 ---
    tz_ny = pytz.timezone('America/New_York')
    ny_now = datetime.now(tz_ny)
    ny_time = ny_now.strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 启动量化系统 5.2 | 纽约时间: {ny_time}")
    
    # 初始化变量，防止后续引用报错
    ticker_list = []
    df_targets = pd.DataFrame()

    # --- 2. 筛选全美股基本面 ---
    try:
        from finvizfinance.screener.financial import Financial
        from finvizfinance.screener.overview import Overview

        filters = {'Market Cap.': '+Mid (over $2bln)'} 
        
        print("🌐 正在获取财务数据...")
        fsf = Financial()
        fsf.set_filter(filters_dict=filters)
        df_base = fsf.screener_view()
        
        def smart_clean_roe(x):
            if pd.isna(x) or x == '-': return np.nan
            if isinstance(x, str):
                try: return float(x.replace('%', '')) / 100
                except: return np.nan
            return float(x)

        df_base['ROE_val'] = df_base['ROE'].apply(smart_clean_roe)
        df_base = df_base[df_base['ROE_val'] > 0.15].dropna(subset=['ROE_val']).copy()

        print("🔗 关联 Overview 获取 P/E...")
        fso = Overview()
        fso.set_filter(filters_dict=filters)
        df_ov = fso.screener_view()
        
        df_merged = pd.merge(df_base[['Ticker', 'ROE_val']], df_ov[['Ticker', 'P/E', 'Price']], on='Ticker')
        df_merged['PE_val'] = pd.to_numeric(df_merged['P/E'], errors='coerce')
        
        # 结果存入 df_targets 供后面扫描引擎使用
        df_targets = df_merged[(df_merged['ROE_val'] > 0.15) & (df_merged['PE_val'] < 25)]
        ticker_list = df_targets['Ticker'].tolist()
        print(f"🎯 基本面海选完成: {len(ticker_list)} 只")

    except Exception as e:
        print(f"‼️ 抓取中断：{str(e)}")
        generate_empty_report(ny_time, f"数据源抓取失败: {str(e)}")
        return # 报错直接退出

    if not ticker_list:
        generate_empty_report(ny_time, "今日无符合基本面条件的标的")
        return

    # --- 3. 批量下载历史数据 ---
    # 注意：这一段现在在 try 块外面，可以正常读取 ticker_list 了
    print(f"Downloading history for {len(ticker_list)} tickers...")
    data = yf.download(ticker_list, period="1y", interval="1d", group_by='ticker', threads=True, progress=False)

    # --- 4. 技术面扫描引擎 ---
    results = []
    if len(ticker_list) == 1:
        data = {ticker_list[0]: data}

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
            
            # 趋势逻辑：价格 > 200日线 且 动量达标
            if (price > ma200) and (all_rets.get(t, 0) >= m_threshold) and (vol < 0.05):
                # RSI 模块
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
                
                # 从 df_targets 匹配原数据
                row_base = df_targets[df_targets['Ticker'] == t].iloc[0]
                
                results.append({
                    '代码': f"**{t}**",
                    'PE': f"{row_base['PE_val']:.1f}",
                    'ROE': f"{row_base['ROE_val']:.1%}",
                    '20d动量': f"{all_rets.get(t, 0):.1%}",
                    'RSI': f"{rsi:.1f}",
                    '建议': "🟢 超卖关注" if rsi < 40 else ("🟡 趋势持有" if rsi < 70 else "🔴 超买警示")
                })
        except: continue

    # --- 5. 生成报告 ---
    save_report(ny_time, results)

def save_report(ny_time, results):
    report = f"# 🦅 量化狙击手 5.2 报告 (Global)\n\n"
    report += f"**🗽 纽约时间: {ny_time}**\n"
    report += f"> 筛选范围：全美股(>20亿) | 基本面：ROE>15%, PE<25 | 技术面：200日线之上, 动量前40%\n\n"
    
    if results:
        df_res = pd.DataFrame(results).sort_values(by='20d动量', ascending=False)
        report += df_res.to_markdown(index=False)
    else:
        report += "### ⚠️ 今日技术面复试暂无符合条件标的。"

    # 统一存为 report_global.md
    with open("report_global.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("🚩 全球扫描报告已更新")

def generate_empty_report(ny_time, reason):
    report = f"# 🦅 量化狙击手 5.2 报告 (Global)\n\n**🗽 纽约时间: {ny_time}**\n\n### ❌ 运行中断: {reason}"
    with open("report_global.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    run_quant_ultimate()
