import requests
import pandas as pd


def get_raw_foundry_prices() -> list[dict]:
    url = "https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview"
    params = {"$filter": "serviceName eq 'Foundry Models'"}

    items = []

    while url:
        response = requests.get(
            url,
            params=params
        )
        response.raise_for_status()
        data = response.json()
        items.extend(data["Items"])
        print(f"\rretrieved {len(items)} items", end="", flush=True)
        params = None
        url = data.get("NextPageLink")
    #newline from item count
    print("\n")
    return items
