from api_calls import get_raw_foundry_prices
from data_transforms import derive_models, apply_sku_transforms, load_raw_to_pd
from database import DB
from datetime import date
import json
import argparse


# I know this is messy please I just need this to work lol
def get_raw_data(raw_path) -> dict:
    try:
        with open(raw_path, "r") as file:
            raw = json.load(file)
            print("got raw data")
        return raw
    except:
        print("couldn't find json file to load from, calling api")
        data = get_raw_foundry_prices()
        with open(raw_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        try:
            with open(raw_path, "r") as file:
                raw = json.load(file)
            print("got raw data")
            return raw
        except:
            print("FATAL: ISSUE WITH FILE PATH (cannot load json)")
            raise

def main(reload: bool = False,  wipe_db: bool = False, raw_path: str|None = None):

    db = DB("data/foundry_prices.db")

    if raw_path is None:
        raw_path = f"data/response/{date.today()}.json"
    if reload:
        print("reloading data from api call")
        data = get_raw_foundry_prices()
        with open(raw_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    raw = get_raw_data(raw_path)

    df = load_raw_to_pd(raw)

    df = apply_sku_transforms(df)

    print("deriving models dataframe")
    models_df = derive_models(df)

    print("====================================== DATAFRAME INFO ======================================")
    print(df.info())
    print(df.head())
    print(models_df.info())
    print(models_df.head())
    print("============================================================================================")

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
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", type=bool)
    parser.add_argument("--raw_path", type=str)
    parser.add_argument("--wipe_db", type = bool)
    args = parser.parse_args()
    main(args.reload, args.wipe_db, args.raw_path) 

