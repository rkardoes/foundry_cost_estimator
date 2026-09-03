import sqlite3

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
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                price_version_pk INTEGER PRIMARY KEY,
                sku_id TEXT NOT NULL,
                retail_price REAL NOT NULL,
                unit_price REAL NOT NULL,
                unit_of_measure TEXT NOT NULL,
                unit_of_measure_num INTEGER,
                effectiveStartDate TEXT NOT NULL,
                effectiveEndDate TEXT NOT NULL,
                observed_from TEXT NOT NULL,
                observed_to TEXT,
                is_current INTEGER,

                FOREIGN KEY (sku_id) REFERENCE skus(sku_id)
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS models (
                model_version_pk INTEGER PRIMARY KEY,
                model_name TEXT NOT NULL,
                deployment_type TEXT NOT NULL,
                processing_type TEXT NOT NULL,
                location TEXT NOT NULL,
                input_sku TEXT,
                output_sku TEXT,
                input_cached_sku TEXT,
                output_cached_sku TEXT,

                FOREIGN KEY(input_sku) REFERENCE skus(sku_id),
                FOREIGN KEY(output_sku) REFERENCE skus(sku_id),
                FOREIGN KEY(input_cached_sku) REFERENCE skus(sku_id),
                FOREIGN KEY(output_cached_sku) REFERENCE skus(sku_id)
            )
        """)

