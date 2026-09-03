import pandas as pd

def load_raw_to_pd(raw: dict):
    df = pd.DataFrame(raw)
    return df

def _check_for_markers(tokens: list[str], markers: set) -> tuple[bool, list[str]]:
    flag = False
    for toke in tokens:
        if toke in markers:
            tokens.remove(toke)
            flag = True
            return flag, tokens
    return flag, tokens


def _parse_sku(sku: str) -> dict:
    """
    This one is a doozey. The markers dictionary defines what strings
    result in a mark for that type. It then uses the _check_for_markers() func
    to see if a token matches that marker. That token is then removed, so that
    the list of tokens eventually can be made into a plain_sku_name, which is
    then used later down the line for a generic "model" table.

    The big thing here is the matching of the markers. Update that dict if you
    need to add more morkers or columns down the line.
    """
    markers = {
        "input_token_type": {"input", "inp", "in"},
        "output_token_type": {"output", "out", "outp", "opt"},
        "cached_flag": {"cached", "cd"},
        "global_deployment_type": {"global", "gl", "glbl", "glb"},
        "regional_deployment_type": {"regional", "regnl", "rgnl", "rgl"},
        "datazone_deployment_type": {"data_zone", "dz", "dzone", "datazone"},
        "priority_processing_type": {"pp"},
        "standard_processing_type": {"std", "standard"},
        "noise_markers": {"tokens, token"}
    }

    sku_normalized = sku.replace("-", " ").lower().replace("data zone", "data_zone")

    # This is where you define what columns are going to be returned
    sku_types: dict[str, str|bool|None] = {
        "token_type": None,
        "cached": None,
        "deployment_type": None,
        "processing_type": None,
        "plain_sku_name": None
    }

    sku_tokens = sku_normalized.split(" ")

    # Get markers. ORDER MATTERS!!! Each check removes tokens
    is_input, sku_tokens = _check_for_markers(sku_tokens, markers["input_token_type"])
    is_output, sku_tokens = _check_for_markers(sku_tokens, markers["output_token_type"])
    is_cached, sku_tokens = _check_for_markers(sku_tokens, markers["cached_flag"])
    is_global, sku_tokens = _check_for_markers(sku_tokens, markers["global_deployment_type"])
    is_regional, sku_tokens = _check_for_markers(sku_tokens, markers["regional_deployment_type"])
    is_dz, sku_tokens = _check_for_markers(sku_tokens, markers["datazone_deployment_type"])
    is_priority, sku_tokens = _check_for_markers(sku_tokens, markers["priority_processing_type"])
    is_standard, sku_tokens = _check_for_markers(sku_tokens, markers["standard_processing_type"])
    noise, sku_tokens = _check_for_markers(sku_tokens, markers["noise_markers"])

    # Whatever is left is the plain name
    plain_name = " ".join(sku_tokens)

    # This next block is the logic to get the value for the column based on marker
    token_type = "unknown"
    if is_input ^ is_output:
        token_type = "input" if is_input else "output"

    deployment_type = "unknown"
    if is_global ^ is_regional ^ is_dz:
        if is_global:
            deployment_type = "global"
        elif is_regional:
            deployment_type = "regional"
        elif is_dz:
            deployment_type = "data_zone"

    processing_type = "default"
    if is_priority ^ is_standard:
        processing_type = "priority" if is_priority else "standard"

    cached = False
    if is_cached:
        token_type = "input"
        cached = True

    # Set column values
    sku_types["token_type"] = token_type
    sku_types["deployment_type"] = deployment_type
    sku_types["processing_type"] = processing_type
    sku_types["cached"] = cached
    sku_types["plain_sku_name"] = plain_name

    return sku_types

def _parse_unitOfMeasure(uom: str) -> int|None:
    if "1M" in uom:
        return 1_000_000
    if "1K" in uom:
        return 1_000
    else: 
        try:
            to_int = int(uom)
            return to_int
        except:
            return None

def get_unitOfmeasure_column(df: pd.DataFrame) -> pd.DataFrame:
    df["unitOfMeasure_numeric"] = df["unitOfMeasure"].apply(_parse_unitOfMeasure)
    return df

def get_sku_type_columns(df: pd.DataFrame) -> pd.DataFrame:
    parsed = df["skuName"].apply(_parse_sku).apply(pd.Series)
    df = pd.concat([df, parsed], axis=1)
    return df
    
def filter_skus(df: pd.DataFrame) -> pd.DataFrame:
    df_filtered = df.loc[~(
        #(df["unitOfMeasure"].str.contains("k", case=False, na=False)) | 
        (df["unitOfMeasure"].str.contains("h", case=False, na=False)) | 
        (df["unitOfMeasure"] == "1") |
        (df["type"] != "Consumption")
    )]
    return df_filtered

def filter_unkowns(df: pd.DataFrame) -> pd.DataFrame:
    df_filtered = df.loc[~((df == "unknown").any(axis = 1))]
    return df_filtered

def apply_sku_transforms(df: pd.DataFrame) -> pd.DataFrame:
    """applies all transformations necessary to parse out the sku table"""
    df_return = filter_skus(df)
    df_return = get_unitOfmeasure_column(df_return)
    df_return = get_sku_type_columns(df_return)
    df_return = filter_unkowns(df_return)

    return df_return

def _test_sku_validity(sku: pd.Series) -> tuple[str|None, bool]:
    if len(sku) == 0:
        return None, True
    elif len(sku) > 1:
        return "INVALID", False
    else:
        return_sku = sku.iloc[0]
        return return_sku, True

def _test_model_validity(model: str, deployment: str, location: str, processing: str, skus: pd.DataFrame) -> dict|None:
    """
    Ensures that a model name, deployment, location, and processing type combo have only 1 input and output
    sku's attached, or 0. This will probably require a little bit of data cleaning down the road.
    """
    rel_skus = skus[
        (skus["plain_sku_name"] == model)&
        (skus["deployment_type"] == deployment)&
        (skus["location"] == location)&
        (skus["processing_type"] == processing)
        ]
    input_sku_cndts = rel_skus.loc[(rel_skus["token_type"]=="input")&(rel_skus["cached"]==False)]["skuId"]
    output_sku_cndts = rel_skus.loc[(rel_skus["token_type"]=="output")&(rel_skus["cached"]==False)]["skuId"]
    input_cached_sku_cndts = rel_skus.loc[(rel_skus["token_type"]=="input")&(rel_skus["cached"]==True)]["skuId"]
    output_cached_sku_cndts = rel_skus.loc[(rel_skus["token_type"]=="output")&(rel_skus["cached"]==True)]["skuId"]

    sku_column_cndts: dict[str, pd.Series] = {
        "input_sku": input_sku_cndts,
        "output_sku": output_sku_cndts,
        "input_cached_sku": input_cached_sku_cndts,
        "output_cached_sku": output_cached_sku_cndts,
    }

    sku_columns = {}

    for key in sku_column_cndts.keys():
        sku_id, valid = _test_sku_validity(sku_column_cndts[key])
        if not valid:
            return None
        sku_columns[key] = sku_id

    return sku_columns


def derive_models(df: pd.DataFrame) -> pd.DataFrame:
    model_cdnts = list(
        df[["plain_sku_name", "deployment_type", "location", "processing_type"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
        )
    models = []
    for mc in model_cdnts:
        model = _test_model_validity(mc[0], mc[1], mc[2], mc[3], df)
        if model is not None:
            model["name"] = mc[0]
            model["deployment_type"] = mc[1]
            model["location"] = mc[2]
            model["processing_type"] = mc[3]
            models.append(model)

    model_df = pd.DataFrame(models)    
    return model_df