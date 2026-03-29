# micro-quant-trading-lab-2
(Since the first lab crushed by error 128, the route error. The existed branch and the yml path is messed up.  I decided to create this new one.)
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
