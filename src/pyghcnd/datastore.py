import pandas as pd

class ParquetStore(object):
    def _load_data(self, ):
        if not self.folder.is_dir():
            self.folder.mkdir()

        raw_file = self.folder / 'raw.parquet'
        if raw_file.exists():
            self.raw = pd.read_parquet(self.folder / 'raw.parquet')
            self.stats = pd.read_parquet(self.folder / 'stats.parquet')
            self._has_data = True

    def _raw_df_save(self, ):
        self.raw.to_parquet(self.folder / 'raw.parquet')

    def _stats_df_save(self, ):
        self.stats.to_parquet(self.folder / 'stats.parquet')
        

