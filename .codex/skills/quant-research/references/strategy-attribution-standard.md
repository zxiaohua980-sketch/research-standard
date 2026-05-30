# Strategy Attribution Standard

Do attribution before changing filters, SL, TP, trailing, timeout, sizing, entry timing, or execution assumptions.

## Attribution question

Explain where profits and losses come from:

- entry edge;
- exit design;
- stop/target geometry;
- position sizing;
- cost assumptions;
- session or regime exposure;
- a small number of tail trades.

## Minimum comparisons

Compare:

- winners vs losers;
- TP winners vs SL losers;
- fast losers vs slow losers;
- winners with deep MAE vs clean winners;
- large winners vs typical winners;
- cost-sensitive trades vs cost-insensitive trades;
- session/year/regime buckets.

## Before changing filters

A filter candidate must use only features known at or before `signal_time`. Show the count of removed losers and mistakenly removed winners. Validate on development data that did not create the idea.

## Before changing SL or TP

Report MAE/MFE distributions in R, direct SL losses, give-back losses, winners that never hit TP, and winners with deep MAE. A stop or target change is a strategy change and requires execution re-audit.

## Before changing trailing or breakeven

Show whether the rule can be triggered by completed, realtime-visible information. Do not use eventual MFE/MAE as a rule condition.

## Before changing sizing

Show whether sizing improves risk-adjusted return without hiding tail risk. Sizing changes require portfolio exposure and drawdown analysis.

## Tail dependence

If removing the top 1%, 5%, or 10% winners destroys expectancy, say the edge is tail-dependent. Do not report a smooth alpha story when returns depend on rare outliers.

## Required output

Attribution reports must state whether the proposed change is:

- accepted for Stage 6 proposal;
- rejected;
- exploratory only;
- blocked by missing fields;
- blocked by sample size.
