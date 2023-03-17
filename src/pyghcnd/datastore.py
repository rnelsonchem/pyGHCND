import pandas as pd

class ParquetStore(object):
    def load_data(self, ghcnd):
        if not ghcnd.folder.is_dir():
            ghcnd.folder.mkdir()

        raw_file = ghcnd.folder / 'raw_full.parquet'
        if raw_file.exists():
            ghcnd._raw_full = pd.read_parquet(raw_file)
            ghcnd.stats = pd.read_parquet(ghcnd.folder / 'stats.parquet')
            ghcnd._has_data = True

    def raw_df_save(self, ghcnd):
        ghcnd._raw_full.to_parquet(ghcnd.folder / 'raw_full.parquet')

    def stats_df_save(self, ghcnd):
        ghcnd.stats.to_parquet(ghcnd.folder / 'stats.parquet')
        

