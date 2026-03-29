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
    
    # --- 2. 筛选标普 500 基本面 (严谨版) ---
    try:
        fso = Overview()
        fso.set_filter(filters_dict={'Index': 'S&P 500'})
        df_base = fso.screener_view()
        
        # 核心：精准匹配。如果没有这个指标，直接抛出异常，不继续运行。
        # 我们在这里搜寻包含 'Return on Equity' 的列
        actual_columns = df_base.columns.tolist()
        roe_matches = [c for c in actual_columns if 'Return on Equity' in c]
        
        if not roe_matches:
            # 这里的报错会直接显示在你的 GitHub Action 日志里
            error_msg = f"❌ 严重错误：在 Finviz 返回的列中未找到 'Return on Equity'。\n当前可用列名为: {actual_columns}"
            raise ValueError(error_msg)
            
        target_roe_col = roe_matches[0]
        df_base['ROE'] = pd.to_numeric(df_base[target_roe_col].str.replace('%',''), errors='coerce') / 100
        
        # 同样的逻辑检查 P/E
        if 'P/E' not in df_base.columns:
            raise ValueError(f"❌ 未找到 P/E 列。当前列名: {actual_columns}")
            
        df_base['P/E'] = pd.to_numeric(df_base['P/E'], errors='coerce')
        ticker_list = df_base['Ticker'].tolist()
        print(f"✅ 成功匹配指标: {target_roe_col}")

    except Exception as e:
        # 这里我们不再创建空的 report.md，直接让 Python 抛出错误
        # 这样 GitHub Action 的 'Run Script' 这一步会变红，你会收到报错邮件
        print(f"\n‼️ 脚本由于数据结构变更停止运行:\n{str(e)}")
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
