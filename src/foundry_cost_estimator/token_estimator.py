import tiktoken
from helpers import _list_selector


class Estimator():
    def __init__(self, prices: dict):
        self.estimation_type = None
        self.include_cached_types: bool = False

        self.input_sample = None
        self.output_sample = None

        self.input_token_estimate_per_day = 0
        self.output_token_estimate_per_day = 0
        self.input_cached_token_estimate_per_day = 0
        self.output_cached_token_estimate_per_day = 0

        self.model = prices["model"]

        self.in_ppt = prices["input"]
        self.out_ppt = prices["output"]
        self.in_cd_ppt = prices.get("input_cached")
        self.out_cd_ppt = prices.get("output_cached")
        self.input_cached = True if prices.get("input_cached") is not None else False
        self.output_cached= True if prices.get("output_cached") is not None else False

        # deterimine tokenizer need
        ops = ["enter token number", "use tokenizer"]
        op = _list_selector("type num to select option", ops)

        if op == ops[0]:
            self.estimation_type = "manual"
        elif op == ops[1]:
            self.estimation_type = "tokenizer"
            self.tokenizer = Tokenizer()
            self.input_sample = input("paste input sample\n")
            self.output_sample = input("\npaste output sample (do not include newlines!!!!)\n")

        else: raise ValueError("something went wrong in the estimator setup")

        self.cost_per_day = self.estimate_cost_per_day()
        self.report = Report(self)
        

    def estimate_cost_per_day(self) -> float:
        if self.estimation_type == "manual":
            if not self.include_cached_types:
                tryer = True
                while tryer:
                    try:
                        in_toke = int(input("enter number of tokens for avg input\n"))
                        out_toke = int(input("enter number of tokens for avg output\n"))
                        tryer = False
                    except KeyboardInterrupt:
                        exit()
                    except:
                        "invalid input"
        elif self.estimation_type == "tokenizer":
            in_toke = self.tokenizer.get_token_count(self.input_sample)
            out_toke = self.tokenizer.get_token_count(self.output_sample)

        print("\n")
        time_spans = {
            "day": 1,
            "week": 7,
            "month": 30
        }

        time_span = _list_selector("select time span for number of prompts", list(time_spans.keys()))

        tryer = True
        while tryer:
            try:
                prompts = int(input(f"\nHow many of these prompts per {time_span}?\n"))
                tryer = False
            except KeyboardInterrupt:
                exit()
            except:
                "invalid input"

        self.input_token_estimate_per_day = in_toke/time_spans[time_span] * prompts
        self.output_token_estimate_per_day = out_toke/time_spans[time_span] * prompts

        cost_per_day = (self.input_token_estimate_per_day * self.in_ppt) + (self.output_token_estimate_per_day * self.out_ppt)
        return cost_per_day


class Tokenizer():
    def __init__(self):
        encoding_name = self.set_encoding_name()
        self.encoding = tiktoken.get_encoding(encoding_name)

    def set_encoding_name(self) -> str:
        encodings = tiktoken.list_encoding_names()
        encoding = _list_selector("select encoder (google it for your model)", encodings)
        return encoding

    def get_token_count(self, prompt) -> int:
        return len(self.encoding.encode(prompt))

class Report():
    def __init__(self, est: Estimator) -> None:
        self.cost_per_day = est.cost_per_day
        self.cost_per_wk = self.cost_per_day * 7
        self.cost_per_mo = self.cost_per_day * 30
        self.model_name = est.model["name"]
        self.location = est.model["location"]
        self.deployment = est.model["deployment_type"]
        self.processing = est.model["processing_type"]
        self.day_low = f"${self.cost_per_day*.8:,.2f}"
        self.wk_low = f"${self.cost_per_wk*.8:,.2f}"
        self.mo_low = f"${self.cost_per_mo*.8:,.2f}"
        self.day_mid = f"${self.cost_per_day:,.2f}"
        self.wk_mid = f"${self.cost_per_wk:,.2f}"
        self.mo_mid = f"${self.cost_per_mo:,.2f}"
        self.day_high = f"${self.cost_per_day*1.2:,.2f}"
        self.wk_high = f"${self.cost_per_wk*1.2:,.2f}"
        self.mo_high = f"${self.cost_per_mo*1.2:,.2f}"

    def __str__(self) -> str:

        details =  f"""
COST ESTIMATE
===================================================
model: {self.model_name}
location: {self.location}
deployment type: {self.deployment}
processing type: {self.processing}
===================================================\n
"""
        table = [
            f"     {"LOW":^10} | {"MID":^10} | {"HIGH":^10}",
            f"Day: {self.day_low:>10} | {self.day_mid:>10} | {self.day_high:>10}",
            f" Wk: {self.wk_low:>10} | {self.wk_mid:>10} | {self.wk_high:>10}",
            f" Mo: {self.mo_low:>10} | {self.mo_mid:>10} | {self.mo_high:>10}",
        ]

        table_complete = "\n".join(table)

        final = details + table_complete
        return final