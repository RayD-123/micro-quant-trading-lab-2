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
    
    # --- 2. 筛选全美股基本面 (范围扩大版) ---
    try:
        from finvizfinance.screener.financial import Financial
        from finvizfinance.screener.overview import Overview

        # 如果你想放宽到全美股，去掉 'Index': 'S&P 500' 即可
        # 这里我设置一个较宽的过滤：全美股 + 市值 > Mid (20亿美金以上)，避免垃圾股
        filters = {'Market Cap.': '+Mid (over $2bln)'} 
        
        print("🌐 正在从 Finviz 获取全美股财务数据 (ROE > 15%)...")
        fsf = Financial()
        fsf.set_filter(filters_dict=filters)
        df_base = fsf.screener_view()
        
        # 清洗 ROE
        df_base['ROE_val'] = pd.to_numeric(df_base['ROE'].str.replace('%',''), errors='coerce') / 100
        # 严谨基本面过滤：ROE > 15%
        df_base = df_base[df_base['ROE_val'] > 0.15].copy()
        print(f"✅ ROE 过滤完成，剩余 {len(df_base)} 只标的")

        print("🔗 正在关联 Overview 获取 P/E 和 价格...")
        fso = Overview()
        fso.set_filter(filters_dict=filters)
        df_ov = fso.screener_view()
        
        # 合并
        df_merged = pd.merge(df_base[['Ticker', 'ROE_val']], df_ov[['Ticker', 'P/E', 'Price']], on='Ticker')
        df_merged['PE_val'] = pd.to_numeric(df_merged['P/E'], errors='coerce')
        
        # 严谨筛选：ROE > 15% 且 PE < 25 (你可以在这里放宽 PE 到 30)
        df_targets = df_merged[(df_merged['ROE_val'] > 0.15) & (df_merged['PE_val'] < 25)]
        ticker_list = df_targets['Ticker'].tolist()
        
        print(f"🎯 基本面海选完成！进入技术面复试: {len(ticker_list)} 只")

    except Exception as e:
        print(f"\n‼️ 抓取中断：{str(e)}")
        raise e
        
    if not ticker_list:
        generate_empty_report(ny_time, "基本面初筛未通过")
        return

    # --- 3. 批量下载历史数据 (性能优化) ---
    # 如果标的超过 100 个，yfinance 可能会很慢，我们增加处理逻辑
    print(f"📥 正在下载 {len(ticker_list)} 只标的历史行情...")
    data = yf.download(ticker_list, period="1y", interval="1d", group_by='ticker', threads=True, progress=False)

    # --- 4. 技术面扫描引擎 ---
    results = []
    # 如果只有一只股票，yfinance 返回的数据结构会不同，这里做个转换
    if len(ticker_list) == 1:
        single_t = ticker_list[0]
        data = {single_t: data}

    # 计算动量阈值
    all_rets = {}
    for t in ticker_list:
        try:
            close = data[t]['Close'].dropna()
            if len(close) > 21:
                all_rets[t] = (close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]
        except: continue
    
    # 放宽要求：从前 25% 放宽到 前 40%
    m_threshold = pd.Series(all_rets).quantile(0.60) if all_rets else 0

    for t in ticker_list:
        try:
            hist = data[t].dropna()
            if len(hist) < 200: continue
            
            close = hist['Close']
            price = float(close.iloc[-1])
            
            # 指标计算
            ma200 = close.rolling(200).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            vol = ((hist['High'] - hist['Low']) / close).tail(14).mean()
            
            # 技术面过滤逻辑
            # 1. 价格在 200 日线之上 (趋势向上)
            # 2. 动量在前 40%
            # 3. 波动率不太离谱
            is_ok = (price > ma200) and (all_rets.get(t, 0) >= m_threshold) and (vol < 0.05)
            
            if is_ok:
                # RSI 模块
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                
                # 获取原基本面数据
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
    report = f"# 🦅 量化狙击手 5.2 报告\n\n"
    report += f"**🗽 纽约时间: {ny_time}**\n"
    report += f"> 过滤逻辑：全美股(市值>20亿) + ROE>15% + 动量前40% + 站上200日线\n\n"
    
    if results:
        df_res = pd.DataFrame(results).sort_values(by='20d动量', ascending=False)
        report += df_res.to_markdown(index=False)
    else:
        report += "### ⚠️ 今日复试阶段暂无符合条件标的。\n\n*可能原因：市场整体处于均线下方或波动率过高。*"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("🚩 报告已更新至 report.md")

def generate_empty_report(ny_time, reason):
    report = f"# 🦅 量化狙击手 5.2 报告\n\n**🗽 纽约时间: {ny_time}**\n\n### ❌ 运行中断: {reason}"
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    run_quant_ultimate()
