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
    markers = {
        "input_token_type": {"input", "inp", "in"},
        "output_token_type": {"output", "out", "outp", "opt"},
        "cached_flag": {"cached", "cd"},
        "global_deployment_type": {"global", "gl", "glbl", "glb"},
        "regional_deployment_type": {"regional", "regnl", "rgnl", "rgl"},
        "datazone_deployment_type": {"data_zone", "dz", "dzone", "datazone"},
        "priority_processing_type": {"pp"},
        "standard_processing_type": {"std", "standard"}
    }

    sku_normalized = sku.replace("-", " ").lower().replace("data zone", "data_zone")
    
    sku_types = {
        "token_type": None,
        "cached": None,
        "deployment_type": None,
        "processing_type": None,
        "plain_sku_name": None
    }

    sku_tokens = sku_normalized.split(" ")

    is_input, sku_tokens = _check_for_markers(sku_tokens, markers["input_token_type"])
    is_output, sku_tokens = _check_for_markers(sku_tokens, markers["output_token_type"])
    is_cached, sku_tokens = _check_for_markers(sku_tokens, markers["cached_flag"])
    is_global, sku_tokens = _check_for_markers(sku_tokens, markers["global_deployment_type"])
    is_regional, sku_tokens = _check_for_markers(sku_tokens, markers["regional_deployment_type"])
    is_dz, sku_tokens = _check_for_markers(sku_tokens, markers["datazone_deployment_type"])
    is_priority, sku_tokens = _check_for_markers(sku_tokens, markers["priority_processing_type"])
    is_standard, sku_tokens = _check_for_markers(sku_tokens, markers["standard_processing_type"])
    
    plain_name = " ".join(sku_tokens)

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


    sku_types["token_type"] = token_type
    sku_types["deployment_type"] = deployment_type
    sku_types["processing_type"] = processing_type
    sku_types["cached"] = is_cached
    sku_types["plain_sku_name"] = plain_name

    return sku_types


def get_sku_type_columns(df: pd.DataFrame) -> pd.DataFrame:
    parsed = df["skuName"].apply(_parse_sku).apply(pd.Series)
    df = pd.concat([df, parsed], axis=1)
    return df
    

def filter_skus(df: pd.DataFrame) -> pd.DataFrame:
    df_filtered = df.loc[~(
        (df["unitOfMeasure"].str.contains("k", case=False, na=False)) | 
        (df["unitOfMeasure"].str.contains("h", case=False, na=False)) | 
        (df["unitOfMeasure"] == "1")
    )]
    return df_filtered

def apply_transforms(df: pd.DataFrame) -> pd.DataFrame:
    return get_sku_type_columns(filter_skus(df))
