from api_calls import get_raw_foundry_prices
from data_transforms import derive_models, apply_sku_transforms, load_raw_to_pd
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

    df = apply_sku_transforms(df)

    # print(df.info())
    # print(df.head())
    # print(df["token_type"].unique())
    # print(df["cached"].unique())
    # print(df["deployment_type"].unique())
    # print(df["processing_type"].unique())
    # print(df["unitOfMeasure_numeric"].unique())

    # checks_df = df#[df["plain_sku_name"] == "5.4 batch"]

    # check1 = checks_df.groupby("plain_sku_name")[
    #     ["token_type", "cached", "deployment_type", "processing_type"]
    # ].nunique()

    # check2 = checks_df.groupby("plain_sku_name")[
    #     ["token_type", "cached", "deployment_type", "processing_type"]
    # ].apply(lambda x: x.drop_duplicates())

    # check3 = checks_df.groupby("plain_sku_name").agg(
    #     token_types=("token_type", "unique"),
    #     cached=("cached", "unique"),
    #     deployment_types=("deployment_type", "unique"),
    #     processing_types=("processing_type", "unique"),
    # )

    # print(check1)
    # print(check2)
    # print(check3)

    models_df = derive_models(df)

    print(models_df.info())
    print(models_df.head())

    print(models_df[models_df["input_sku"].isna()])
    print(models_df[(models_df["input_sku"].isna())&(models_df["input_cached_sku"].isna())])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", type=bool)
    parser.add_argument("--raw_path", type=str)
    args = parser.parse_args()
    main(args.reload, args.raw_path)

