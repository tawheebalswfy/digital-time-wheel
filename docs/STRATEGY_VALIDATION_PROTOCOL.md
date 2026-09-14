# Next research experiment — payoff eligibility

Status: specified on 10 September 2026 after baseline diagnosis; **not executed, not a validated strategy, and not installed in live settings**.

Subsequent user direction prioritized the completed [Time Wheel entry ablation](TIME_WHEEL_ABLATION_REPORT.md). This payoff-eligibility proposal remains deferred; its rules were not combined with the entry experiment.

## Question and fixed arms

Does requiring a viable net reward/risk relationship improve the existing wheel strategy's results when signal generation and the proposed price levels remain fixed?

Compare exactly two research arms:

1. **B0: frozen baseline.** Use the strategy and execution rules from backtest `41ba0ea5-4b9d-4c09-8c2d-7947da46385b` without changes.
2. **R1: target-1 eligibility only.** Generate the same original signal, target 1, and invalidation. At the immediate next bar open, first apply the existing direction/gap checks. Define `reward = direction * (target1 - open)`, `risk = direction * (open - stop)`, and `cost = spread + 2 * slippage + fee`. Enter only when `(reward - cost) / (risk + cost) >= 1`, with positive risk and reward. Otherwise skip the trade. Do not move the target or stop, select a more distant target, change direction, or search other ratio thresholds.

R1 must be simulated sequentially. Filtering the saved trade list is insufficient: skipping a trade may make later signals eligible while B0 is still occupied. Preserve the existing no-overlap, next-open, stop-first, adverse stop-gap, and holding-period semantics. The eligibility decision uses the observed entry open only; that candle's high/low/close cannot affect entry. Record rejected entries with timestamp, original forecast hash, reward, risk, cost, and reason.

Use a separate research runner or explicit research-only extension, keeping the production engine and saved strategy unchanged. Verify that the runner's B0 reproduces the original engine before interpreting R1 results. Add focused correctness checks for skipped-trade scheduling, gap rejection, entry-only information, and exact B0 parity.

## Data boundaries and reporting

The retained 30,170 M1 bars are development data for this hypothesis because both their training and test results have already been inspected. No fresh holdout claim is permitted on any subdivision of that same history. Retain the original split labels only for traceability.

First compare B0 and R1 on the original training segment (ending at index `split_index - 31`, exclusive). Predeclare and report both results even if R1 has no eligible trades. Do not change anchor, increment, cycle, gates, weights, threshold, timeframe, target ranking, or ratio threshold in response to results. Any later modification is a newly disclosed trial.

A final evaluation requires new closed MT5 bars from after this protocol was frozen. Before retrieving them, record a concrete UTC cutoff strictly after protocol publication and collect only bars opening at or after that cutoff for scoring. Earlier candles may supply feature warmup, never scoreable outcomes. Use the existing saved normalization contract and record dataset/strategy/code hashes. Neither create a synthetic continuation nor silently overlap the old dataset. Obtain enough chronological coverage for multiple sessions/regimes; the present six test dates do not provide that coverage.

If future work introduces parameter selection, define chronological train/test windows and purge rules before running it; disclose every candidate and freeze choices before each test window. Multi-timeframe data availability does not establish that an M1 strategy or an H4 strategy has an edge. Multi-timeframe signal filters require a separate causal specification using only closed higher-timeframe bars.

## Fixed evaluation rules

Report trades, opportunity/rejection counts, exposure, gross/net expectancy, profit factor, average win/loss, drawdown, daily P&L, and target/stop outcomes for both arms. Retain the fixed-cost scenarios 0, 0.20, 0.40, and 0.80, explicitly identifying any fixed-ledger sensitivity calculation.

R1 has no demonstrated advantage if it has no eligible trades or if independent-data net expectancy is nonpositive. A higher win rate alone is not success. Positive point estimates require follow-up uncertainty and stability analysis using chronological blocks, with a frozen method that respects serial dependence; no trade-independent significance claim. Profit factor above 1, positive expectancy, and improvement over B0 are necessary screening conditions, not sufficient proof of an edge or authorization for live trading.

The immediate completed checkpoint is the [baseline validation report](VALIDATION_REPORT.md). This protocol defines the next experiment without asserting results that have not been measured.
