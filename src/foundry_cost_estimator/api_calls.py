import requests
import pandas as pd


def get_raw_foundry_prices() -> dict:
    ms_retail_api = "https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview"

    response = requests.get(
        ms_retail_api,
        params={
            "$filter": "serviceName eq 'Foundry Models'"
        }
    )
    response.raise_for_status()

    data = response.json()

    return data["Items"]
