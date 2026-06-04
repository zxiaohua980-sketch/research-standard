# Repository Map

This map records the currently known Git layout for the local `D:\MT5` workspace.
It exists to prevent accidentally pushing the wrong scope.

## Portable Governance Repo

```text
Path:   D:\MT5\RESEARCH_STANDARD
Branch: main
Remote: https://github.com/zxiaohua980-sketch/research-standard.git
Scope:  research standards, Codex quant-research skill, bootstrap helpers
```

Use this repo on another computer to install the research rules and skill.

## Registry Repo

```text
Path:   D:\MT5\research_registry
Branch: master
Remote: none configured
Scope:  central strategy registry, data ledgers, stage states, frozen candidates
```

This should become a private remote if it needs to travel between machines.

## Known Strategy Or Project Repos

```text
D:\MT5\openclaw\trend
  Remote: https://github.com/zxiaohua980-sketch/trend.git

D:\MT5\openclaw\bb_strategy
  Remote: none configured

D:\MT5\openclaw\strategy_double_bottom
  Remote: none configured

D:\MT5\openclaw\strategy_structure
  Remote: none configured

D:\MT5\H1M5N
  Remote: inspect before pushing

D:\MT5\HiddenDrift
  Remote: inspect before pushing

D:\MT5\HP
  Remote: inspect before pushing

D:\MT5\MSKD
  Remote: inspect before pushing

D:\MT5\SBL
  Remote: inspect before pushing
```

## Rule Of Thumb

Push one repository at a time from its own directory. Do not initialize or push
the whole `D:\MT5` directory unless a separate manifest/submodule design has
been chosen deliberately.

