import awswrangler as wr
import pandas as pd
import sqlite3
import numpy as np

def get_data(boat, trip_no):

    trip_data = {}
    
    trip_info = get_trip_info(boat = boat, trip_no=trip_no)
    trip_data['trip_info'] = trip_info

    print(trip_info)

    bv_sets = get_bv_sets(boat=boat, trip_id = trip_info['trip_id'])
    trip_data['bv_sets'] = bv_sets

    bv_fish = get_bv_fish(boat = boat, trip_id = trip_info['trip_id'])
    trip_data['bv_fish'] = bv_fish
                          

    ai_df= get_ai_counts(boat=boat, trip_info=trip_info)
    trip_data['ai_df'] = ai_df

    all_counts = get_bv_counts(ai_df, bv_fish)
    trip_data['all_counts'] = all_counts

    ai_sets = join_bv_sets(bv_sets, ai_df)
    trip_data['ai_sets'] = ai_sets

    df_elog = get_elog_data(boat, trip_info['trip_start_date'], trip_info['trip_end_date'])
    trip_data['elogs'] = df_elog

    bv_set_counts = get_bv_set_counts(bv_fish, bv_sets)
    trip_data['bv_set_counts'] = bv_set_counts

    
    return trip_data



def get_trip_info(boat, trip_no):
    trip_df = wr.athena.read_sql_query(f"SELECT * FROM {boat}_v1_bv_trips", database="tnc_edge")
    
    trip_df.sort_values(by = 'trip_end_date', ascending= True, inplace= True)
    
    trip_id = trip_df['trip_id'].values[trip_no]
    
    trip_start_date = trip_df['trip_start_date'].values[trip_no]
    trip_end_date = trip_df['trip_end_date'].values[trip_no]

    trip_info = {}
    trip_info['trip_id'] = trip_id
    trip_info['trip_start_date'] = trip_start_date
    trip_info['trip_end_date'] = trip_end_date

    return trip_info
    
def get_bv_sets(boat, trip_id):
    
    bv_sets = wr.athena.read_sql_query(f"SELECT * FROM {boat}_v1_bv_sets where trip_id = '{trip_id}'", database = "tnc_edge")

    return bv_sets

def get_bv_fish(boat, trip_id):

    bv_fish = wr.athena.read_sql_query(f"SELECT fish.* FROM {boat}_v1_bv_fish fish left join {boat}_v1_bv_sets sets on sets.set_id = fish.set_id where sets.trip_id = '{trip_id}'", database = "tnc_edge")

    return bv_fish

def get_bv_set_counts(bv_fish, bv_sets):
    datetime_cols = ['set_start_datetime','set_end_datetime','haul_start_datetime','haul_end_datetime']
    for col in datetime_cols:
        bv_sets[col] = pd.to_datetime(bv_sets[col], utc = True)
        bv_sets[col] = bv_sets[col].dt.tz_convert(None)
        
    retained_bv_counts = bv_fish[bv_fish['future'] == 'retained'].groupby('set_id').agg({'fish_id':'count'}).reset_index().rename(columns = {'fish_id':'retained_count'})
    joined_bv_sets = pd.merge(bv_sets, retained_bv_counts, how = 'left', on = 'set_id')
    
    return joined_bv_sets

# read in catch countst
def get_ai_counts(boat, trip_info):
    
    model = 'ondeck' if boat == 'stpatrick' else 'aifish' if boat == 'brancol' else None
    if model == 'ondeck':
        count_column = None
        number_columns = ['overallcatches', 'overallcount','overalldiscards', 'detection_confidence','count'] 
    elif model == 'aifish':
        count_column = 'count'
        number_columns = ['count', 'detection_confidence']
        
    trip_start_date = trip_info['trip_start_date']
    trip_end_date = trip_info['trip_end_date']
    
    aifish_sql = f"""
        SELECT 
        aifd.id,
        aifd.{count_column} as count,
        aifd.detection_confidence,
        v.start_datetime 
        FROM {boat}_v1_{model}data aifd 
        join {boat}_v1_video_files v on aifd.video_uri = v.decrypted_path 
        where start_datetime > '{trip_start_date}' and start_datetime < '{trip_end_date}'

    """

    ondeck_sql = f"""
        SELECT 
        aifd.id,
        aifd.overallcount,
        aifd.overallcatches,
        aifd.overalldiscards,
        (cast(aifd.overallcatches as DOUBLE) - cast(aifd.overalldiscards as DOUBLE)) as count,
        aifd.detection_confidence,
        v.start_datetime 
        FROM {boat}_v1_{model}data aifd 
        join {boat}_v1_video_files v on aifd.video_uri = v.decrypted_path 
        where start_datetime > '{trip_start_date}' and start_datetime < '{trip_end_date}'
    
    """
    sql = ondeck_sql if model == 'ondeck' else aifish_sql if model == 'aifish' else None

    ai_df = wr.athena.read_sql_query(sql, database="tnc_edge")
    ai_df.start_datetime = pd.to_datetime(ai_df.start_datetime, utc = True)
    ai_df['utc_start_datetime'] = ai_df['start_datetime'].dt.tz_convert(None)
    ai_df['utc_end_datetime'] = ai_df['utc_start_datetime'] + pd.Timedelta(minutes = 5)

    for col in number_columns:
        ai_df[col] = pd.to_numeric(ai_df[col], errors='coerce')
 
    ai_df['weighted_count'] = ai_df['detection_confidence'] * ai_df['count']
    return ai_df

def join_bv_sets(bv_sets, ai_df):

    # join aif_df to sets
    df_hauls = bv_sets.loc[:,['set_id','set_number','haul_start_datetime','haul_end_datetime']]
    df_hauls['haul_start_datetime'] = pd.to_datetime(df_hauls['haul_start_datetime'])
    df_hauls['haul_end_datetime'] = pd.to_datetime(df_hauls['haul_end_datetime'])
    df_hauls['haul_start_datetime'] = df_hauls['haul_start_datetime'].dt.tz_convert(None)
    df_hauls['haul_end_datetime'] = df_hauls['haul_end_datetime'].dt.tz_convert(None)

    #Make the db in memory
    conn = sqlite3.connect(':memory:')
    
    #write the tables
    ai_df.to_sql('ai_counts', conn, index=False)
    df_hauls.to_sql('hauls', conn, index=False)
    
    query = """
    select
    *
    
    from ai_counts
    left join hauls on ai_counts.utc_start_datetime between hauls.haul_start_datetime and hauls.haul_end_datetime
    
    """
    df = pd.read_sql_query(query, conn)

    # convert datatypes
    df['count'] = pd.to_numeric(df['count'])
    df['haul_start_datetime'] = pd.to_datetime(df['haul_start_datetime'])
    df['haul_end_datetime'] = pd.to_datetime(df['haul_end_datetime'])
    df.start_datetime = pd.to_datetime(df.start_datetime)
    df['utc_start_datetime'] = pd.to_datetime(df['utc_start_datetime'])

    # get flags for haul not haul
    df['is_haul_bool'] =  df['set_number'].notnull()
    df['is_haul'] = df['is_haul_bool'].apply(lambda x: 1 if x else 0)

    df.sort_values(by = 'utc_start_datetime', inplace= True)
    
    return df

def get_bv_counts(ai_df, bv_fish):
    #join bv counts to ai counts
    #Make the db in memory
    conn = sqlite3.connect(':memory:')
    
    #write the tables
    ai_df.to_sql('ai_counts', conn, index=False)
    bv_fish.to_sql('bv_fish', conn, index=False)
    
    query = """
    select
        ai_counts.id,
        ai_counts.utc_start_datetime,
        bv_fish.*
    from ai_counts
    join bv_fish on bv_fish.catch_datetime >= ai_counts.utc_start_datetime 
        and bv_fish.catch_datetime < ai_counts.utc_end_datetime
    """
    bv_ai_df = pd.read_sql_query(query, conn)
    bv_counts = bv_ai_df.groupby('id').fish_id.agg('count').reset_index().rename(columns = {'fish_id':'bv_count'})
   
    df_all_counts = pd.merge(ai_df, bv_counts, how = 'left', on = 'id')
    df_all_counts.sort_values(by = 'utc_start_datetime', inplace = True)
    df_all_counts['bv_count'].fillna(0, inplace= True)

    return df_all_counts


def get_elog_data(vessel, trip_start_date, trip_end_date):
    #elog data
    
    sql = f"""
    select
    elogs.id,
    elogs.datetime,
    elogs.bycatchcount,
    elogs.catchcount,
    elogs.systemstartsetdatetime,
    elogs.systemendsetdatetime,
    elogs.systemstarthauldatetime,
    elogs.systemendhauldatetime
    
    from {vessel}_v1_deckhandevents_mostrecentlonglineevent_jsonextracted elogs
       where datetime > '{trip_start_date}' and datetime < '{trip_end_date}'
    """
    df_elog = wr.athena.read_sql_query(
        sql,
        database="tnc_edge")

    datetime_cols = ['datetime','systemstartsetdatetime','systemendsetdatetime','systemstarthauldatetime','systemendhauldatetime']
    for col in datetime_cols:
        df_elog[col] = pd.to_datetime(df_elog[col], utc = True)
        df_elog[col] = df_elog[col].dt.tz_convert(None)

    return df_elog

def get_vector_data(vessel, vector, trip_info):
    trip_start_date = trip_info['trip_start_date']
    trip_end_date = trip_info['trip_end_date']
    
    sql = f"""
    select
        id, score, datetime, detail, name
    from {vessel}_v1_tests
    where vector_id = '{vector}' and datetime > '{trip_start_date}' and datetime < '{trip_end_date}'       
    """
    df_vector = wr.athena.read_sql_query(sql, database="tnc_edge")
    df_vector['datetime'] = pd.to_datetime(df_vector['datetime'], utc=True)
    df_vector['datetime'] = df_vector['datetime'].dt.tz_convert(None)
    df_vector['score'] = pd.to_numeric(df_vector['score'])
    
    return df_vector