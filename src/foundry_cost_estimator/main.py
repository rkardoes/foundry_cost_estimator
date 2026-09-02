from api_calls import get_raw_foundry_prices
from data_transforms import apply_transforms, load_raw_to_pd
import json
import argparse


def main(reload: bool = False, raw_path: str|None = None):
    if raw_path is None:
        raw_path = "data/raw_response.json"
    if reload:
        print("reloading data from api call")
        data = get_raw_foundry_prices()
        with open(raw_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)


    with open(raw_path, "r") as file:
        raw = json.load(file)

    df = load_raw_to_pd(raw)

    df = apply_transforms(df)

    print(df.info())
    print(df.head())
    print(df["token_type"].unique())
    print(df["cached"].unique())
    print(df["deployment_type"].unique())
    print(df["processing_type"].unique())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", type=bool)
    parser.add_argument("--raw_path", type=str)
    args = parser.parse_args()
    main(args.reload, args.raw_path)

