from api_calls import get_raw_foundry_prices
from data_transforms import derive_models, apply_sku_transforms, load_raw_to_pd
from token_estimator import Estimator
from database import DB
from helpers import _list_selector
from datetime import date
from pathlib import Path
import json
import argparse

# I know this is messy please I just need this to work lol
def get_raw_data(raw_path) -> list[dict]:
    try:
        with open(raw_path, "r") as file:
            raw = json.load(file)
            print("got raw data")
        return raw
    except FileNotFoundError:
        print("couldn't find json file to load from, calling api")
        data = get_raw_foundry_prices()
        print("ensuring data/response exists")
        path = Path(raw_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(raw_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        return data
    except:
        raise


def lookup_loop(db: DB):
    locations = db.query_locations()
    location = _list_selector("type number to select location", locations)

    deployments = db.query_deployment_type(location)
    deployment = _list_selector("type number to select deployment type", deployments)

    processes = db.query_processing_type(location, deployment)
    process = _list_selector("type number to select processing type", processes)

    models = db.query_models_filtered(location, deployment, process)
    model = _list_selector("type number to select model", models)

    prices = db.query_model_sku_prices(model, location, deployment, process)

    est = Estimator(prices)
    print(est.report)

def main(reload: bool = False, call_api: bool = False, wipe_db: bool = False, raw_path: str|None = None):
    if raw_path is None:
        raw_path = f"data/response/{date.today()}.json"
    if call_api:
        print("reloading data from api call")
        data = get_raw_foundry_prices()
        with open(raw_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        reload = True

    if reload:

        raw = get_raw_data(raw_path)

        df = load_raw_to_pd(raw)

        df = apply_sku_transforms(df)

        print("deriving models dataframe\n")
        models_df = derive_models(df)

        # print("====================================== DATAFRAME INFO ======================================")
        # print(df.info())
        # print(df.head())
        # print(models_df.info())
        # print(models_df.head())
        # print("============================================================================================")

    db = DB("data/foundry_prices.db")

    if wipe_db:
        print("dropping all tables (wipe_db = True)")
        db._drop_all_tables()

        print("creating tables")
        db._make_tables()
        print("tables created")

        print("upserting skus")
        db.upsert_skus(df)
        print("upserting prices")
        db.upsert_prices(df)
        print("upserting models")
        db.upsert_models(models_df)

        print("done upserting, check all tables")  

    print("\n\n\n\n\n===================================")
    print("Foundry Model Cost Estimator")
    print("===================================")
    print("force close program with ctr+C\n\n\n")

    while True:
        lookup_loop(db)
        choice = input("\nget another estimate? (y,n)\n")
        if choice == "n":
            exit()
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", type=bool)
    parser.add_argument("--call_api", type=bool)
    parser.add_argument("--raw_path", type=str)
    parser.add_argument("--wipe_db", type = bool)
    args = parser.parse_args()
    main(args.reload, args.wipe_db, args.raw_path) 

