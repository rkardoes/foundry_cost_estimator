import sqlite3
import pandas as pd
from datetime import datetime, timezone

class DB():
    def __init__(self, path: str):
        self.connection = sqlite3.connect(path)

    def _make_tables(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS skus (
                sku_id TEXT PRIMARY KEY,
                sku_name_full TEXT NOT NULL,
                sku_name TEXT NOT NULL,
                arm_sku_name TEXT NOT NULL,
                product_name TEXT NOT NULL,
                location TEXT NOT NULL,
                token_type TEXT,
                cached_token INTEGER,
                deployment_type TEXT,
                processing_type TEXT
            );
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                price_version_pk INTEGER PRIMARY KEY AUTOINCREMENT,
                sku_id TEXT NOT NULL,
                retail_price REAL NOT NULL,
                unit_price REAL NOT NULL,
                unit_of_measure TEXT NOT NULL,
                unit_of_measure_num INTEGER,
                effective_start_date TEXT NOT NULL,
                observed_from TEXT NOT NULL,
                observed_to TEXT,
                is_current INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY (sku_id) REFERENCES skus(sku_id),
                UNIQUE (sku_id, retail_price, unit_price, unit_of_measure, effective_start_date)
            );
        """)

        self.connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_one_current_sku
            ON prices (sku_id)
            WHERE is_current = 1;
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS models (
                model_pk INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                deployment_type TEXT NOT NULL,
                processing_type TEXT NOT NULL,
                location TEXT NOT NULL,
                input_sku TEXT,
                output_sku TEXT,
                input_cached_sku TEXT,
                output_cached_sku TEXT,

                FOREIGN KEY(input_sku) REFERENCES skus(sku_id),
                FOREIGN KEY(output_sku) REFERENCES skus(sku_id),
                FOREIGN KEY(input_cached_sku) REFERENCES skus(sku_id),
                FOREIGN KEY(output_cached_sku) REFERENCES skus(sku_id),

                UNIQUE(model_name, deployment_type, processing_type, location)
            );
        """)

    def _drop_all_tables(self) -> None:

        self.connection.execute("PRAGMA foreign_keys = OFF")

        tables = self.connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%';
        """).fetchall()

        for (table,) in tables:
            self.connection.execute(f"DROP TABLE {table}")
            self.connection.commit()

        self.connection.execute("PRAGMA foreign_keys = ON")
        
    def _upsert(self, table: str, data: pd.DataFrame, column_map: dict[str, str], db_key_columns: list[str]) -> None:
        insert_columns = []

        for key in column_map.keys():
            insert_columns.append(column_map[key])

        q_marks = ["?" for _ in insert_columns]

        excluded = [f"{col} = excluded.{col}" for col in insert_columns 
                    if col not in db_key_columns]

        query = f"""
            INSERT INTO {table} ({",\n".join(insert_columns)}) VALUES ({", ".join(q_marks)})
            ON CONFLICT ({", ".join(db_key_columns)})
            DO UPDATE SET
            {",\n".join(excluded)}
            ;
        """

        cursor = self.connection.cursor()

        try:
            cursor.executemany(
                query,
                data[column_map.keys()].itertuples(index=False, name=None)
            )

            self.connection.commit()

        except sqlite3.DatabaseError:
            self.connection.rollback()
            raise

    def upsert_skus(self, data: pd.DataFrame) -> None:
        column_map = {
            "skuId": "sku_id",
            "skuName": "sku_name_full",
            "plain_sku_name": "sku_name",
            "armSkuName": "arm_sku_name",
            "productName": "product_name",
            "location": "location",
            "token_type": "token_type",
            "cached": "cached_token",
            "deployment_type": "deployment_type",
            "processing_type": "processing_type"
        }

        key_columns = ["sku_id"]

        table = "skus"

        self._upsert(table, data, column_map, key_columns)

    def upsert_models(self, data: pd.DataFrame) -> None:

        table = "models"

        column_map = {
            "name": "model_name",
            "deployment_type": "deployment_type",
            "processing_type": "processing_type",
            "location": "location",
            "input_sku": "input_sku",
            "output_sku": "output_sku",
            "input_cached_sku": "input_cached_sku",
            "output_cached_sku": "output_cached_sku",
        }

        key_columns = ["model_name", "deployment_type", "processing_type", "location"]

        self._upsert(table, data, column_map, key_columns)

    def upsert_prices(self, data: pd.DataFrame) -> None:

        table = "prices"

        column_map = {
            "skuId": "sku_id",
            "retailPrice": "retail_price",
            "unitPrice": "unit_price",
            "unitOfMeasure": "unit_of_measure",
            "unitOfMeasure_numeric": "unit_of_measure_num",
            "effectiveStartDate": "effective_start_date",
            "observed_from": "observed_from",
            "observed_to": "observed_to",
            "is_current": "is_current"
        }

        key_columns = ["sku_id", "retail_price", "unit_price", "unit_of_measure", "effective_start_date"]

        observed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        current_prices = set(self.connection.execute("""
            SELECT sku_id, retail_price, unit_price, unit_of_measure
            FROM prices
            WHERE is_current = 1 
        """))

        incoming_prices = set(
            data[["skuId", "retailPrice", "unitPrice", "unitOfMeasure"]].itertuples(index=False, name=None)
        )

        # get set of new price ids, id is at index = 0 for the resulting set of tuples
        new_price_ids = {x[0] for x in (incoming_prices - current_prices)}
        updated_records = 0
        for id in new_price_ids:
            cursor = self.connection.execute("SELECT * FROM prices WHERE is_current = 1 AND sku_id = ?", (id,))
            old = cursor.fetchone()
            if old is not None:
                self.connection.execute("""
                UPDATE prices SET 
                observed_to = ?,
                is_current = 0 
                WHERE is_current = 1 
                AND sku_id = ?
                """, 
                (observed_at, id,)
                )

                updated_records += 1

        self.connection.commit()

        print(f"SCD 2: Updated {updated_records} records")

        new_sku_df = data[data["skuId"].isin(new_price_ids)].copy()
        new_sku_df["is_current"] = 1
        new_sku_df["observed_from"] = observed_at
        new_sku_df["observed_to"] = None

        self._upsert(table, new_sku_df, column_map, key_columns)


    def _query_sku_price(self, sku:str) -> float:
        query = """
            SELECT
                (unit_price/unit_of_measure_num) as ppt
            FROM
                prices
            WHERE
                sku_id = ?
        """
        ppt = self.connection.execute(
            query,
            (sku,)
        ).fetchone()[0]
        return ppt

    def query_model_sku_prices(self, model_name:str, location:str, deployment_type:str, processing_type:str) -> dict:
        query = """
            SELECT
                input_sku,
                output_sku,
                input_cached_sku,
                output_cached_sku
            FROM 
                models
            WHERE 
                model_name = ? AND
                location = ? AND
                deployment_type = ? AND
                processing_type = ?
            ;
        """
        skus = self.connection.execute(
            query,
            (model_name, location, deployment_type, processing_type)
        ).fetchone()
        sku_ids = {
            "input": skus[0],
            "output": skus[1],
            "input_cached": skus[2],
            "output_cached": skus[3]
        }
        prices = {}
        for (sku, id) in sku_ids.items():
            prices[sku] = self._query_sku_price(id) if id is not None else None
        model = {
            "name": model_name,
            "location": location,
            "deployment_type": deployment_type,
            "processing_type": processing_type
        }
        prices["model"] = model
        return prices

    def query_locations(self) -> list:
        lst: list[tuple] = self.connection.execute("SELECT DISTINCT location FROM models;").fetchall()
        rtrn_list = [x[0] for x in lst]
        return rtrn_list

    def query_deployment_type(self, location: str) -> list:
        lst: list[tuple] = self.connection.execute("SELECT DISTINCT deployment_type FROM models WHERE location = ?;", (location,)).fetchall()
        rtrn_list = [x[0] for x in lst]
        return sorted(rtrn_list)

    def query_processing_type(self, location: str, deployment_type: str) -> list:
        lst: list[tuple] = self.connection.execute("SELECT DISTINCT processing_type FROM models WHERE location = ? AND deployment_type = ?;", (location, deployment_type,)).fetchall()
        rtrn_list = [x[0] for x in lst]
        return sorted(rtrn_list)

    def query_models_filtered(self, location: str, deployment_type: str, processing_type: str) -> list:
        lst: list[tuple] = self.connection.execute("SELECT DISTINCT model_name FROM models WHERE location = ? AND deployment_type = ? AND processing_type = ?", (location, deployment_type, processing_type,)).fetchall()
        rtrn_list = [x[0] for x in lst]
        return sorted(rtrn_list)