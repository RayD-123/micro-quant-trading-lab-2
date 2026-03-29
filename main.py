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
    
    # --- 2. 筛选标普 500 基本面 (高效合并版) ---
    try:
        from finvizfinance.screener.overview import Overview
        from finvizfinance.screener.valuation import Valuation # 引入估值视图

        # 1. 抓取 Overview (获取 P/E)
        fso = Overview()
        fso.set_filter(filters_dict={'Index': 'S&P 500'})
        df_overview = fso.screener_view()
        
        # 2. 抓取 Valuation (ROE 通常在这里)
        fsv = Valuation()
        fsv.set_filter(filters_dict={'Index': 'S&P 500'})
        df_valuation = fsv.screener_view()

        # 打印列名调试 (只运行这一次，稳了以后可以删掉)
        print(f"📊 Valuation 视图列名: {df_valuation.columns.tolist()}")

        # 3. 本地 Merge (根据 Ticker 对齐)
        # 我们只需要 Valuation 里的 Ticker 和 ROE 相关列
        # 匹配包含 'ROE' 或 'Return on Equity' 的列名
        roe_col = [c for c in df_valuation.columns if 'ROE' in c or 'Equity' in c]
        
        if not roe_col:
            raise ValueError("❌ 在 Valuation 视图中依然没找到 ROE 列，Finviz 可能又改版了")

        df_base = pd.merge(
            df_overview[['Ticker', 'P/E', 'Price']], 
            df_valuation[['Ticker', roe_col[0]]], 
            on='Ticker'
        )

        # 4. 严谨清洗
        df_base['ROE'] = pd.to_numeric(df_base[roe_col[0]].str.replace('%',''), errors='coerce') / 100
        df_base['P/E'] = pd.to_numeric(df_base['P/E'], errors='coerce')
        
        # 最终筛选：ROE > 15% 且 P/E < 25
        df_final = df_base[(df_base['ROE'] > 0.15) & (df_base['P/E'] < 25)]
        ticker_list = df_final['Ticker'].tolist()
        
        print(f"✅ 筛选完成！从 500 只中选出 {len(ticker_list)} 只符合双指标的绩优股")

    except Exception as e:
        print(f"\n‼️ 数据合并失败:\n{str(e)}")
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
