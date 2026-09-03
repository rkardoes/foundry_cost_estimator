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
        params = None
        url = data.get("NextPageLink")

    return items
