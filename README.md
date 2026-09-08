# Microsoft Foundry Cost Estimator

## Intro
This project aims provide a rough estimate for model costs on Microsoft Foundry by querying Microsoft's retail API. API results are parsed and an attempt is made to combine multiple SKU's to a singular model name. From there, a cost estimate is made. Data is stored in a SQLite DB locally once polled, and supports historical pricing data.

## Setup
Clone repo, run:
```
uv sync
```

To use for the first time, run **from the repo root**:
```
uv run foundry_cost_estimator/main.py --reload True --wipe_db True
```

## General Usage

To run, **from repo root**:
```
uv run src/foundry_cost_estimator/main.py
```

To reload from stored json:
```
uv run src/foundry_cost_estimator/main.py --reload True --raw-path data/response/<date>.json
```

To run and wipe the db:
```
uv run src/foundry_cost_estimator/main.py --wipe-db True
```


*AI Usage: Used for research debugging. Contains no AI written code (and you can tell).*