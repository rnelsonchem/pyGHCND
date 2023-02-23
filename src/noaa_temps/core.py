import time
import pickle

from datetime import datetime, timedelta
from pathlib import Path

import requests
import numpy as np
import pandas as pd
import scipy.stats as sps

class NOAAWeatherCore(object):
    def __init__(self, stationid, start_date, token_file, data_folder='.'):
        self.stationid = stationid
        self.start = start_date
        self.folder = Path(data_folder)

        self.token = open(token_file).read().strip()

        self.now = datetime.now()

        self._has_data = False
        # This method should be defined in a data_store class
        self._load_data()

    def _api_request(self, year, offset=None, debug=False):
        # An API call function, separated out for testing purposes
        req_str = 'http://www.ncei.noaa.gov/cdo-web/api/v2/data?'\
            f"datasetid=GHCND&stationid=GHCND:{self.stationid}&"\
            f"startdate={year}-01-01&enddate={year}-12-31&limit=1000&"

        if offset:
            req_str += f'offset={offset}&includemetadata=false'

        req = requests.get(req_str, headers={'token': self.token})

        # Skip error checking for debugging purposes
        if not debug:
            if req.status_code != 200:
                raise ValueError('Status code != 200')

        return req

    def _download_year(self, year):
        # Can only download data year by year
        req = self._api_request(year)    
        js = req.json()

        # If the dataset is empty, then drop out of the run
        if js == {}:
            return []

        try:
            meta = js['metadata']['resultset']
            count = meta['count']
            limit = meta['limit']
        except:
            raise ValueError('Metadata error')

        results = js['results']

        frames = count//limit
        if count%limit == 0:
            frames -= 1
        offset = limit + 1

        for frame in range(frames):
            # 5 request per second max
            time.sleep(0.2)

            req = self._api_request(year, offset)
            js = req.json()

            results.extend(js['results'])
            offset += limit

        return results

    def _raw_df_proc(self, results):
        data = pd.DataFrame(results)
        data['date'] = pd.to_datetime(data['date'])

        # Pivot the data from longform into columns
        data = data.pivot(columns='datatype', index='date', values='value')

        # Remove leap year days to make things easier
        mask = (data.index.month == 2) & (data.index.day == 29)
        data = data.loc[~mask].copy()

        # Data conversions
        # Convert temps from C to F
        data.TMAX = (data.TMAX*0.1)*9/5 + 32
        data.TMIN = (data.TMIN*0.1)*9/5 + 32
        # Drop some obviously bad values (assumptions)
        data.loc[data.TMAX > 130., 'TMAX'] = np.nan
        data.loc[data.TMIN > 130., 'TMIN'] = np.nan
        # Convert precipitation from mm to inches
        data.PRCP = (data.PRCP*0.1)/25.4 
        if hasattr(data, 'SNOW'): data.SNOW = data.SNOW/25.4
        if hasattr(data, 'SNWD'): data.SNWD = data.SNWD/25.4
        # If precipitation isn't given, ie NaN, then it was zero on that day
        # (assumption)
        data.fillna(value={'PRCP':0, 'SNOW':0, 'SNWD':0,}, inplace=True)
        # Esitmate of total water = rain + snow/10, i.e. 1" snow = 0.1" rain
        if hasattr(data, 'SNOW'): data['SNPR'] = data.PRCP + data.SNOW/10.

        if self._has_data:
            # Combine the old/new data, but be sure to mask out any partial
            # data for an unfinished year
            mask = self.raw.index >= data.index[0]
            self.raw = pd.concat([self.raw[~mask], data])
        else:
            self.raw = data

        # Delta years for linear regression analysis
        self.raw['yeardiff'] = self.raw.index.year - self.start

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

                vals.append([fit.slope, data_group, 'slope'])
                vals.append([ps[0], data_group, 'p_slope'])
                vals.append([fit.intercept, data_group, 'icept'])
                vals.append([ps[1], data_group, 'p_icept'])

        df = pd.DataFrame(vals, columns=['value', 'data_group', 'type'],)
        return df

    def _stats_df_proc(self, ):
        gb = self.raw.groupby([self.raw.index.month, self.raw.index.day])
        stats = gb.apply(self._data_reduce)
        stats = stats.droplevel(level=2)

        pivot = stats.pivot(values='value', columns=['data_group', 'type'])
        pivot.index.rename(['month', 'day'], inplace=True)
        pivot.columns.rename([None, None], inplace=True)

        self.stats = pivot 

    def update_data(self, status=False):
        if self._has_data:
            last_date = self.raw.index[-1] + timedelta(days=1)
            begin = int(last_date.strftime('%Y'))
        else:
            begin = self.start
        
        # Add 1 to end for the range below
        end = int(self.now.strftime('%Y')) + 1
        
        # Check for a temp file of downloaded data -- this is used for broken
        # connections
        temp_file = self.folder / f'temp_pickle_{self.stationid}'
        results = []
        if not temp_file.exists():
            # Save a temp file with the current data
            with open(temp_file, 'wb') as fp:
                pickle.dump([begin, end, results], fp)
        else:   
            # If restarting an broken data download, load the saved data
            with open(temp_file, 'rb') as fp:
                begin, end, results = pickle.load(fp)
        
        if status:
            from tqdm import trange
            rng = trange
        else:
            rng = range

        for year in rng(begin, end): 
            new_res = self._download_year(year)
            results.extend(new_res)
           
            # Incremement this variable so restart at the correct year
            begin += 1
            with open(temp_file, 'wb') as fp:
                pickle.dump([begin, end, results,], fp)

        # Process and save the raw data
        self._raw_df_proc(results)
        # This method must be defined as a data_store object class
        self._raw_df_save()
        # Remove the tempfile if the previous calls are successful
        temp_file.unlink()

        self._stats_df_proc()
        # This method must be defined as a data_store object class
        self._stats_df_save()

    def daily_trends_sorted(self, by=None, ascending=False, abs_val=True):
        cats = ('TMIN', 'TMAX')
        dfs = []

        for cat in cats:
            slopes = self.stats.loc[:, [(cat, 'slope'), (cat, 'p_slope')]]\
                    .droplevel(0, axis=1)
            slopes['-log_p'] = -np.log10(slopes['p_slope'])

            if abs_val: weight = slopes['slope'].abs()
            else: weight = slopes['slope']
            slopes['-log_p*slope'] = -np.log10(slopes['p_slope'])*weight
            
            if by:
                slopes = slopes.sort_values(by=by, ascending=ascending)\
                        .reset_index()

            dfs.append(slopes)

        totals = pd.concat(dfs, axis=1, keys=cats)
        if by:
            totals['rank'] = np.arange(1, totals.shape[0] + 1)
            totals.set_index('rank', inplace=True)

        return totals
