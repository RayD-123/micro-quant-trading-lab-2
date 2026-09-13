
# micro-quant-trading-lab-2
(Since the first lab was crushed by error 128, which caused a route error, and the existing branches and yml paths were messed up, I decided to create this new repository.)
# 🦅 Quant Sniper v6.1 (Global Edition)

[![Stock Market Analysis](https://img.shields.io/badge/Market-US_Equities-blue.svg)](https://finviz.com/)
[![Auto-Trading-Scan](https://img.shields.io/badge/Automation-GitHub_Actions-orange.svg)](https://github.com/features/actions)

**Quant Sniper 6.1** is an automated US stock quantitative scanning system based on dual filtering of fundamental screening and technical screening. The system runs automatically twice daily, aiming to capture high-quality stocks with "high profitability, low valuation, and in an upward trend" from the entire US stock market.

---

## 🚀 Core Strategy Logic (Investment Strategy)

This system follows the **"Quality at a Reasonable Price" (GARP)** investment philosophy, combined with momentum factors for multi-dimensional screening:

### 1. Fundamental Filters
* **Universe**: US Stock Market (NYSE/NASDAQ), excluding low-liquidity targets with a market cap below $2 billion (Mid-Cap+).
* **Profitability**: **ROE (Return on Equity) > 15%** — Ensures the company has strong capital return capabilities.
* **Valuation**: **P/E (Price-to-Earnings) < 25** — Avoids chasing premiums and seeks reasonably priced high-quality assets.

### 2. Technical Screening
* **Trend Filter**: The stock price must be above the **200-day Moving Average (MA200)**, ensuring a long-term bull trend.
* **Relative Momentum**: Calculates the 20-day price change rate, retaining only strong stocks ranked in the top **40%** of momentum.
* **Volatility Monitoring**: Excludes abnormally volatile targets with excessive daily volatility (ATR/Price > 5%) to reduce drawdown risk.

---

## 🛠️ System Architecture

The system adopts a modular design to achieve a closed loop from data acquisition to decision-making:

* **Data Layer**: Calls `finvizfinance` to obtain financial snapshots, and uses `yfinance` to fetch real-time OHLCV quotes.
* **Execution Layer**: Deployed on **GitHub Actions**, using Cron Jobs to achieve on-time scanning at US stock **market open (9:35 AM)** and **close (4:05 PM)**.
* **Storage Layer**:
    * `report_smart.md`: Generates an easy-to-read Markdown decision report.
    * `history_database/`: Automatically maintains monthly-sliced CSV databases, providing Point-in-Time data for future backtesting systems.

---

## 📊 Report Dictionary

| Field | Description | Decision Reference |
| :--- | :--- | :--- |
| **ROE** | Return on Equity | Measures the "core temperature" of a company's profitability |
| **PE** | Static Price-to-Earnings | A "scale" reflecting whether the current stock price is cheap |
| **20d Momentum** | 20-day Price Change Rate | An "accelerometer" to judge the strength of capital inflow |
| **RSI** | 14-day Relative Strength Index | `<40` hints at oversold attention; `>75` hints at overbought profit-taking |

---

## 📈 Getting Started

1.  **Auto Run**: The system is configured for automatic triggering. View historical run records under the `Actions` tab.
2.  **Manual Trigger**: Under `Actions` -> `Smart Timing Quant Scan`, click `Run workflow` to get immediate scan results.
3.  **Outputs**:
    *   View the latest sniper suggestions: `report_smart.md`
    *   Access historical archived data: `history_database/`

---

## ⚠️ Disclaimer

This repository is for technical research and quantitative experiments only, and does not constitute any investment advice. The stock market is risky, so be cautious when entering.

---

# micro-quant-trading-lab-2
(Since the first lab was crushed by error 128, the route error. The existed branch and the yml path is messed up.  I decided to create this new one.)
# 🦅 Quant Sniper v6.1 (Global Edition)

[![Stock Market Analysis](https://img.shields.io/badge/Market-US_Equities-blue.svg)](https://finviz.com/)
[![Auto-Trading-Scan](https://img.shields.io/badge/Automation-GitHub_Actions-orange.svg)](https://github.com/features/actions)

**Quant Sniper 6.1** 是一款基于基本面海选与技术面双重过滤的自动化美股量化扫描系统。系统每日两次自动执行，旨在从全美股市场中捕捉“高盈利能力、低估值、且处于上升趋势”的绩优标的。

---

## 🚀 核心策略逻辑 (Investment Strategy)

本系统遵循 **"Quality at a Reasonable Price" (GARP)** 投资哲学，结合动量因子进行多维度筛选：

### 1. 基本面海选 (Fundamental Filters)
* **资产池**：全美股市场 (NYSE/NASDAQ)，排除市值小于 20 亿美元的低流动性标的（Mid-Cap+）。
* **盈利能力**：**ROE (净资产收益率) > 15%** —— 确保公司具备强大的资本回报能力。
* **估值水平**：**P/E (市盈率) < 25** —— 避免追高溢价，寻找定价合理的优良资产。

### 2. 技术面扫描 (Technical Screening)
* **趋势过滤**：股价必须位于 **200 日均线 (MA200)** 之上，确保处于长期牛市趋势。
* **相对动量**：计算 20 日价格变化率，仅保留动量排名在前 **40%** 的强势股。
* **波动率监控**：排除日均波动率过大 (ATR/Price > 5%) 的异常波动标的，降低回撤风险。

---

## 🛠️ 系统架构 (System Architecture)

系统采用模块化设计，实现数据从获取到决策的闭环：

* **数据层**：调用 `finvizfinance` 获取财务快照，使用 `yfinance` 抓取实时 OHLCV 行情。
* **执行层**：部署于 **GitHub Actions**，通过 Cron Job 实现美股**开盘 (9:35 AM)** 与 **收盘 (4:05 PM)** 的准点扫描。
* **存储层**：
    * `report_smart.md`: 生成易于阅读的 Markdown 决策报告。
    * `history_database/`: 自动维护按月切片的 CSV 数据库，为未来的回测系统提供 Point-in-Time 数据。

---

## 📊 报告字段说明 (Report Dictionary)

| 字段 | 说明 | 决策参考 |
| :--- | :--- | :--- |
| **ROE** | 净资产收益率 | 衡量公司赚钱效率的“核心体温” |
| **PE** | 静态市盈率 | 反映当前股价是否便宜的“体重计” |
| **20d动量** | 近 20 交易日涨幅 | 判断资金流入强度的“加速规” |
| **RSI** | 14 日强弱指标 | `<40` 提示超卖关注；`>75` 提示超买止盈 |

---

## 📈 运行指南 (Getting Started)

1.  **自动运行**：系统已配置自动化触发，可在 `Actions` 标签页查看历史运行记录。
2.  **手动触发**：在 `Actions` -> `Smart Timing Quant Scan` 中点击 `Run workflow` 即可获取即时扫描结果。
3.  **结果产出**：
    * 查看最新的狙击建议：`report_smart.md`
    * 访问历史存盘数据：`history_database/`

---

## ⚠️ 免责声明 (Disclaimer)

本仓库仅用于技术研究与量化实验，不构成任何投资建议。股市有风险，入市需谨慎。
