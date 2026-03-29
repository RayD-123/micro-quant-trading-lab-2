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
    print(f"🚀 启动量化系统 6.1 (带数据存档) | 纽约时间: {ny_time}")
    
    ticker_list = []
    df_targets = pd.DataFrame()

    try:
        from finvizfinance.screener.financial import Financial
        from finvizfinance.screener.overview import Overview

        filters = {'Market Cap.': '+Mid (over $2bln)'} 
        
        print("🌐 抓取 Finviz 数据...")
        fsf = Financial()
        fsf.set_filter(filters_dict=filters)
        df_fin = fsf.screener_view()
        
        fso = Overview()
        fso.set_filter(filters_dict=filters)
        df_ov = fso.screener_view()
        
        def smart_clean(x):
            if pd.isna(x) or x == '-': return np.nan
            if isinstance(x, str):
                try: return float(x.replace('%', '')) / 100
                except: return np.nan
            return float(x)

        df_fin['ROE_val'] = df_fin['ROE'].apply(smart_clean)
        
        df_merged = pd.merge(
            df_fin[['Ticker', 'ROE_val']], 
            df_ov[['Ticker', 'Sector', 'Industry', 'P/E', 'Price']], 
            on='Ticker'
        )
        
        df_merged['PE_val'] = pd.to_numeric(df_merged['P/E'], errors='coerce')
        
        # 核心过滤
        df_targets = df_merged[(df_merged['ROE_val'] > 0.15) & (df_merged['PE_val'] < 25)].copy()
        ticker_list = df_targets['Ticker'].tolist()

    except Exception as e:
        generate_empty_report(ny_time, f"抓取失败: {str(e)}")
        return

    if not ticker_list:
        generate_empty_report(ny_time, "今日无标的")
        return

    # 技术面扫描
    print(f"Scanning {len(ticker_list)} tickers...")
    data = yf.download(ticker_list, period="1y", interval="1d", group_by='ticker', threads=True, progress=False)

    results = []
    if len(ticker_list) == 1: data = {ticker_list[0]: data}

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
            
            if (price > ma200) and (all_rets.get(t, 0) >= m_threshold) and (vol < 0.05):
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
                
                row = df_targets[df_targets['Ticker'] == t].iloc[0]
                
                results.append({
                    'Date': ny_time.split(' ')[0],  # 存入日期供CSV回测
                    'Ticker': t,
                    'Sector': row['Sector'],
                    'PE': round(row['PE_val'], 2),
                    'ROE': f"{row['ROE_val']:.1%}",
                    'Momentum': round(all_rets.get(t, 0), 4),
                    'RSI': round(rsi, 1),
                    'Action': "🟢 买入" if rsi < 40 else ("🔴 止盈" if rsi > 75 else "🟡 持有")
                })
        except: continue

    # 保存报告 (MD) 和 数据库 (CSV)
    save_outputs(ny_time, results)

def save_outputs(ny_time, results):
    # 1. 保存为 MD 报告
    report = f"# 🦅 量化狙击手 6.1 报告\n\n**纽约时间: {ny_time}**\n\n"
    if results:
        df_res = pd.DataFrame(results).sort_values(by='Momentum', ascending=False)
        report += df_res.to_markdown(index=False)
    else:
        report += "### ⚠️ 今日无符合条件标的。"
    
    with open("report_smart.md", "w", encoding="utf-8") as f:
        f.write(report)

    # 2. 保存/追加到当月 CSV 数据库
    if results:
        folder = "history_database"
        if not os.path.exists(folder): os.makedirs(folder)
        
        month_str = datetime.now().strftime('%Y_%m')
        file_path = f"{folder}/data_{month_str}.csv"
        
        df_to_save = pd.DataFrame(results)
        file_exists = os.path.isfile(file_path)
        
        # 追加模式写入
        df_to_save.to_csv(file_path, mode='a', index=False, header=not file_exists, encoding='utf-8')
        print(f"✅ 数据已存入: {file_path}")

def generate_empty_report(ny_time, reason):
    with open("report_smart.md", "w", encoding="utf-8") as f:
        f.write(f"# 🦅 报告中断\n\n时间: {ny_time}\n原因: {reason}")

if __name__ == "__main__":
    run_quant_ultimate()
