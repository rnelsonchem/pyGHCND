import pickle

from datetime import datetime, timedelta
from pathlib import Path

import requests
import numpy as np
import pandas as pd
import scipy.stats as sps

from tqdm import trange

from . import datastore

STORAGE_TYPES = {
        'parquet': datastore.ParquetStore,
        }

class GHCND(object):
    def __init__(self, stationid, token, store_type='parquet', 
                data_folder='.'):
        self.stationid = stationid
        self.folder = Path(data_folder)
        self.token = token

        self._store = STORAGE_TYPES[store_type]()

        station_info = self._api_request()
        if station_info == {}:
            raise ValueError(f'Bad station info call: {stationid}')
        self._station_info = station_info

        self.start_date = int(station_info['mindate'][:4])
        self.end_date = int(station_info['maxdate'][:4])
        self.now = datetime.now()

        self._has_data = False
        self._store.load_data(self)
        if self._has_data:
            self._raw_df_filter()

    def update_data(self, status=False):
        if self._has_data:
            last_date = self._raw_full.index[-1] + timedelta(days=1)
            begin = int(last_date.strftime('%Y'))
        else:
            begin = self.start_date
        
        # Add 1 to end for the range below
        end = self.end_date + 1
        
        # Check for a temp file of downloaded data -- this is used for broken
        # connections
        temp_file = self.folder / f'temp_pickle_{self.stationid}'
        results = []
        if not temp_file.exists():
            # Save a temp file with the current data
            with open(temp_file, 'wb') as fp:
                pickle.dump([begin, results], fp)
        else:   
            # If restarting an broken data download, load the saved data
            with open(temp_file, 'rb') as fp:
                begin, results = pickle.load(fp)
        
        rng = trange if status else range
        for year in rng(begin, end): 
            new_res = self._download_year(year)
            results.extend(new_res)
           
            # Incremement this variable so restart at the correct year
            begin += 1
            with open(temp_file, 'wb') as fp:
                pickle.dump([begin, results,], fp)

        if results != []:
            # Convert raw data into a DataFrame and pivot to make columns from
            # the data types (i.e. TMAX)
            raw_df = pd.DataFrame(results)
            raw_df['date'] = pd.to_datetime(raw_df['date'])
            # Remove leap year for convenience
            mask = (raw_df.date.dt.month == 2) & (raw_df.date.dt.day == 29)
            raw_df = raw_df.loc[~mask].copy()

            flags = ['mflag', 'qflag', 'sflag', 'tobs']
            gb = raw_df.groupby('datatype', group_keys=False)
            raw_new = gb.apply(self._raw_df_proc, flags=flags)\
                        .pivot(columns='datatype', index='date', 
                                values=['value',] + flags)\
                        .swaplevel(axis=1)
            
            # Convert string flags that are NaN to an empty strings
            flag_values = raw_new.loc[:, (slice(None), flags[:-1])].fillna('')
            raw_new.loc[:, (slice(None), flags[:-1])] = flag_values

            # Sort the columns 
            raw_new = raw_new[raw_new.columns.sort_values()]

            # Combine the old/new data if necessary
            if self._has_data:
                mask = self._raw_full.index >= raw_new.index[0]
                self._raw_full = pd.concat([self._raw_full[~mask], raw_new])
            else:
                self._raw_full = raw_new
                self._store.raw_df_save(self)

            # Re-filter the raw data and re-create the stats data if new data
            # was processed
            self._raw_df_filter()
            self._stats_df_proc()
            self._store.stats_df_save(self)

        # Remove the tempfile
        temp_file.unlink()

    def _api_request(self, req_type='station', year=None, offset=None, 
                debug=False):
        # An API call function for station info and weather data
        req_str = 'http://www.ncei.noaa.gov/cdo-web/api/v2/'
        
        if req_type == 'station':
            req_str += f'stations/GHCND:{self.stationid}'
        
        elif req_type == 'data':
            req_str += "data?datasetid=GHCND&"\
                f"stationid=GHCND:{self.stationid}&"\
                f"startdate={year}-01-01&"\
                f"enddate={year}-12-31&limit=1000&"
            if offset:
                req_str += f'offset={offset}&includemetadata=false'

        # Skip error checking for debugging purposes
        if debug:
            return req

        status_code_good = False
        try_count = 0
        MAX_TRIES = 5
        while not status_code_good:
            if try_count == MAX_TRIES:
                raise ValueError(f"Too many requests (n={MAX_TRIES})")

            req = requests.get(req_str, headers={'token': self.token})

            if req.status_code == 200:
                try:
                    json = req.json()
                    if req_type == 'data' and not offset and json != {}:
                        meta_check = json['metadata']['resultset']
                except:
                    try_count += 1
                return json

            try_count += 1

    def _download_year(self, year):
        # Can only download data year by year
        json = self._api_request('data', year)    

        # If the dataset is empty, then drop out of the run
        if json == {}:
            return []

        meta = json['metadata']['resultset']
        count = meta['count']
        limit = meta['limit']
        results = json['results']

        frames = count//limit
        if count%limit == 0:
            frames -= 1
        offset = limit + 1

        for frame in range(frames):
            json = self._api_request('data', year, offset)
            results.extend(json['results'])
            offset += limit

        return results

    def _raw_df_proc(self, group, flags):
        datatype = group['datatype'].iloc[0]

        if datatype in ['TMIN', 'TMAX']:
            group['value'] = (group['value']*0.1)*9/5 + 32
        elif datatype == 'PRCP':
            group['value'] = (group['value']*0.1)/25.4
        elif datatype in ['SNOW', 'SNWD']:
            group['value'] = group['value']/25.4

        attributes = group['attributes'].str.split(',', expand=True)
        column_dict = {i:f'{flags[i]}' for i in range(4)}
        attributes.rename(columns=column_dict, inplace=True)

        return_dfs = [group[['date', 'datatype', 'value']], attributes]
        return pd.concat(return_dfs, axis=1)

    def _raw_df_filter(self, ):

        # This method is only used in the given groupby, so there is no reason
        # to make this a new method
        def quality_filter(group):
            name = group.columns[0][0]
            # If the qflag is not an empty string, that suggest that the data
            # point was bad
            mask = group[name, 'qflag'] != ''
            vals = group[name, 'value']
            vals[mask] = np.nan
            return vals
            
        gb = self._raw_full.groupby(level=0, axis=1)
        self.raw = gb.apply(quality_filter)

        # Delta years for linear regression analysis
        self.raw['yeardiff'] = self.raw.index.year - self.start_date

        # Combined snow and precip data, assuming that 1" snow == 0.1" precip
        self.raw['SNPR'] = self.raw.PRCP + self.raw.SNOW*0.1

    def _stats_df_proc(self, ):
        gb = self.raw.groupby([self.raw.index.month, self.raw.index.day])
        stats = gb.apply(self._data_reduce)
        stats = stats.droplevel(level=2)

        pivot = stats.pivot(values='value', columns=['data_group', 'type'])
        pivot.index.rename(['month', 'day'], inplace=True)
        pivot.columns.rename([None, None], inplace=True)

        self.stats = pivot 

        # Add some ranking data
        cats = ('TMIN', 'TMAX')
        for cat in cats:
            slopes = self.stats[(cat, 'slope')]
            p_slope = self.stats[(cat, 'p_slope')]
            log_p = -np.log10(p_slope)

            self.stats[(cat, '-log_p')] = log_p 
            self.stats[(cat, '-log_p*slope')] = log_p*slopes
            self.stats[(cat, '-log_p*abs_slope')] = log_p*slopes.abs()

        sorted_cols = ['TMIN', 'TMAX', 'PRCP', 'SNOW', 'SNPR']
        self.stats = self.stats.loc[:, sorted_cols]

    def _data_reduce(self, group):
        vals = []

        for data_group in ['TMAX', 'TMIN', 'SNOW', 'PRCP', 'SNPR']:
            vals.append([group[data_group].min(), data_group, 'min'])
            vals.append([group[data_group].max(), data_group, 'max'])
            vals.append([group[data_group].mean(), data_group, 'mean'])
            vals.append([group[data_group].std(), data_group, 'std'])
            
            if data_group in ['TMAX', 'TMIN']:
                mask = ~group[data_group].isna()
                count = mask.sum() 
                vals.append([count, data_group, 'count'])

                fit = sps.linregress(group.loc[mask, 'yeardiff'], 
                                    group.loc[mask, data_group])
                ts = [abs(fit.slope/fit.stderr), 
                      abs(fit.intercept/fit.intercept_stderr)]
                ps = sps.t.sf(ts, count-2)*2

                vals.append([fit.intercept, data_group, 'icept'])
                vals.append([fit.slope, data_group, 'slope'])
                vals.append([ps[0], data_group, 'p_slope'])

        df = pd.DataFrame(vals, columns=['value', 'data_group', 'type'],)
        return df

