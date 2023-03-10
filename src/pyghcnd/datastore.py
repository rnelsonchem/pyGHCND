import pandas as pd

class ParquetStore(object):
    def load_data(self, ghcnd):
        if not ghcnd.folder.is_dir():
            ghcnd.folder.mkdir()

        raw_file = ghcnd.folder / 'raw.parquet'
        if raw_file.exists():
            ghcnd.raw = pd.read_parquet(ghcnd.folder / 'raw.parquet')
            ghcnd.stats = pd.read_parquet(ghcnd.folder / 'stats.parquet')
            ghcnd._has_data = True

    def raw_df_save(self, ghcnd):
        ghcnd.raw.to_parquet(ghcnd.folder / 'raw.parquet')

    def stats_df_save(self, ghcnd):
        ghcnd.stats.to_parquet(ghcnd.folder / 'stats.parquet')
        

