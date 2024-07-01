import scipy.stats as stats
import itertools 
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def aggregate_by_interval(df, freq, agg_list, agg_cols):
    agg_dict = {}
    for col in agg_cols:
        agg_dict[col] = agg_list
        
    data = df.groupby(pd.Grouper(key = 'utc_start_datetime', freq = f'{freq}min')).agg(agg_dict).reset_index()
    data.columns = ['_'.join(col).strip() for col in data.columns.values]

    return data

def aggregate_concat(dfs, freq, agg_list, agg_cols):
    datas = []
    for df in dfs:
        data = aggregate_by_interval(df = df, freq = freq, agg_list = agg_list, agg_cols= agg_cols)
        data.fillna(0, inplace = True)
        datas.append(data)

    concat_data = pd.concat(datas)

    return concat_data

def compare_aggregation_correlations(dfs, intervals, agg_list, x_col, y_col):
    results = {}
    for x_agg in agg_list:
        # print(f'x_agg: {x_agg}')
        x_results = []
        for i in intervals:
            data = aggregate_concat(dfs, freq = i, agg_list= agg_list, agg_cols=[x_col, y_col])

            for y_agg in agg_list:
                y_results = {}
                slope, intercept, rvalue, pvalue, stderr = stats.linregress(x=data[f'{x_col}_{x_agg}'], y=data[f'{y_col}_{y_agg}'])
                r2 = rvalue ** 2
                y_results['interval'] = i
                y_results['y_agg'] = y_agg
                y_results['r2'] = r2
        
                x_results.append(y_results)
            
                
        df_Xresults = pd.DataFrame(x_results)
        # print(df_Xresults.head())
        results[x_agg] = df_Xresults

    return results

def compare_aggregation_correlation_columns(dfs, intervals, agg_list, x_col, y_cols):
    results = []
 
    for i in intervals:
        
        data = aggregate_concat(dfs, freq = i, agg_list= agg_list, agg_cols=[x_col]+ y_cols)
        # result['interval'] = i
        for y_col, x_agg, y_agg in itertools.product(y_cols, agg_list, agg_list):
            result = {}
            result['interval'] = i
            result['x_agg'] = x_agg
            result['y_agg'] = y_agg
            result['y_col'] = y_col

            # get r2 value
            x = np.array(data[f'{x_col}_{x_agg}']).reshape((-1, 1))
            y = np.array(data[f'{y_col}_{y_agg}']).reshape((-1, 1))
            model = LinearRegression()
            model.fit(x,y)
            r2 = model.score(x,y)

            result['r2'] = r2

            results.append(result)
            
                
        
        df_results = pd.DataFrame(results)
        

    return df_results

def add_rolling_aggregates(df, win, agg_dict, keep_cols):
    rolling_df = df.rolling(win, center = True).agg(agg_dict)
    new_cols = {}
    for col in agg_dict.keys():
        new_cols[col]= f'rolling_{col}'
        
    rolling_df.rename(columns = new_cols, inplace = True)

    _df = pd.merge(df[keep_cols], rolling_df, left_index=True, right_index=True)
    return _df.reset_index()