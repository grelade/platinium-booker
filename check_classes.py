import argparse
from datetime import datetime,timedelta
import json
import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from typing import List, Tuple, Dict, Union

from platinium import Client


WEEKDAY_NAMES = ['SUN','MON','TUE','WED','THU','FRI','SAT']
DAYOFWEEK_INTS = [0,1,2,3,4,5,6]

OWN_CLASSES_COLUMNS = ['location_id', 'class_name', 'class_id', 'class_time']
OWN_CLASSES_INDEX = 'own_id'

RENAME_DICT = {'location_id': 'LocationId',
               'class_name': 'Name',
               'class_id': 'Id',
               'class_time': 'StartTime',
               'weekday': 'DayOfWeek'}

ONLINE_CLASSES_COLUMNS = ['StartTime',
                              'Name',
                              'Id',
                              'LocationId',
                              'DayOfWeek',
                              'IsReserved',
                              'IsReservable',
                              'IsEnabled',
                              'IsCanceled',
                              'ReservationButton']
ONLINE_CLASSES_INDEX = 'online_id'

class CompareClasses:
    
    def __init__(self,
                 client: Client,
                 classes: Dict):
        
        self.client = client
        self.classes_dict = classes
        self.classes_df = None
        self.online_classes_df = None
        self.candidate_pairs_df = None
        self.basic_matches_df = None
        self.exact_matches_df = None
        
        self.abs_times = None # absolute StartTimes
        self.location_ids = None # a list of LocationIds
        
        self.week_ahead = None
        self.days_ahead = None
        self.start_date = None
    
    def _set_dates(self,
                    start_date: datetime = datetime.today(),
                    week_ahead: int = 1,
                    days_ahead: int = 7) -> None:
        
        self.week_ahead = week_ahead
        self.days_ahead = days_ahead
        self.start_date = start_date + timedelta(days=self.week_ahead*7)    
    
    def _generate_dfs(self) -> None:
        
        self.classes_df = generate_own_classes_df(self.classes_dict)
        self.location_ids = extract_location_ids(self.classes_df)

        self.online_classes_df = generate_online_classes_df(self.client,
                                                            self.location_ids,
                                                            self.start_date,
                                                            self.days_ahead)
        
        self.abs_times = self.online_classes_df['StartTime'].copy()
        
        self.classes_df, self.online_classes_df = transform_dfs(self.classes_df,
                                                                self.online_classes_df)
        
        self.classes_df, self.online_classes_df = sort_dfs(self.classes_df,
                                                           self.online_classes_df,
                                                           self.abs_times)
        
    def _generate_matches(self) -> None:
        
        self.classes_df, self.online_classes_df, self.candidate_pairs_df = form_candidate_pairs(self.classes_df,
                                                                                                self.online_classes_df)   
        self.basic_matches_df, self.exact_matches_df = extract_matches(self.classes_df,
                                                                       self.online_classes_df,
                                                                       self.candidate_pairs_df)
    
    def _print_verbose(self) -> None:
        
        print_verbose(self.classes_df,
                      self.online_classes_df,
                      self.basic_matches_df,
                      self.exact_matches_df,
                      self.abs_times)
    
    def _print_nonverbose(self) -> None:
        
        print_nonverbose(self.classes_df,
                         self.exact_matches_df,
                         self.abs_times)

def weekday_to_DayOfWeek(weekday: str) -> Union[int,None]:
    if weekday in WEEKDAY_NAMES:
        weekday_ix = np.argwhere(np.array(WEEKDAY_NAMES)==weekday).item()
        return DAYOFWEEK_INTS[weekday_ix]
    else:
        raise ValueError('unknown weekday')

def DayOfWeek_to_weekday(DayOfWeek: int) -> Union[str,None]:
    if DayOfWeek in DAYOFWEEK_INTS:
        dow_ix = np.argwhere(np.array(DAYOFWEEK_INTS)==DayOfWeek).item()
        return WEEKDAY_NAMES[dow_ix]
    else:
        raise ValueError('unknown DayOfWeek')

def class_time_to_StartTime(base_date: datetime,
                            class_time: str) -> datetime:
    split = class_time.split(':')
    if len(split)==2:
        h,m = split
        date = base_date.replace(hour=int(h),minute=int(m),second=0,microsecond=0)
        return date
    else:
        raise ValueError('wrong class_time format; should be HH:MM')

def StartTime_to_class_time(StartTime: str) -> str:
    date = datetime.fromisoformat(StartTime)
    return date.strftime('%H:%M')

def generate_own_classes_df(classes: Dict) -> DataFrame:
    
    def check_class_integrity(wd_cl):
        if not isinstance(wd_cl,list):
            raise ValueError('wrong classes format')
        for cl in wd_cl:
            if not all (k in cl for k in OWN_CLASSES_COLUMNS):
                raise ValueError('wrong classes format')
    
    classes_df = []
    for weekday,wd_cl in classes.items():
        check_class_integrity(wd_cl)
        df0 = pd.DataFrame(wd_cl)
        df0['weekday'] = weekday
        classes_df = df0 if len(classes_df)==0 else pd.concat((classes_df,df0))
        
    classes_df = classes_df.reset_index()
    classes_df = classes_df.drop(labels=['index'],axis=1)
    classes_df.index.name = 'own_id'
    
    dtypes=(np.int64,str,np.int64,str,str)
    for dtype, col in zip(dtypes,classes_df.iteritems()):
        colname, colval = col
        classes_df[colname] = classes_df[colname].astype(dtype)

    return classes_df


def extract_location_ids(classes_df: DataFrame) -> List:
    if 'location_id' in classes_df.keys():
        l = list(classes_df['location_id'].unique())
        return [int(lid) for lid in l]
    else:
        raise ValueError('wrong classes_df format; no location_id column')

def generate_online_classes_df(client : Client, 
                               location_ids : List, 
                               date : datetime, 
                               days_forward : int = 7,
                               cols : List = ONLINE_CLASSES_COLUMNS) -> DataFrame:
    '''
    generate dataframe of online classes starting from start_date for days_forward days
    '''
    out = []

    for lid in location_ids:
        out += client.get_classes(location_id=lid,
                                 start_date=date.isoformat(),
                                 days=days_forward)

    online_classes_df = pd.DataFrame(out)
    online_classes_df = online_classes_df.reset_index()
    online_classes_df = online_classes_df.drop(labels=['index'],axis=1)
    online_classes_df.index.name = ONLINE_CLASSES_INDEX
    
    if all (k in online_classes_df.columns for k in cols):
        
        online_classes_df = online_classes_df.loc[:,cols]
    else:
        raise KeyError('unknown name in cols')
    
    return online_classes_df

def transform_dfs(classes_df: DataFrame, 
                  online_classes_df: DataFrame) -> Tuple[DataFrame,DataFrame]:
    '''
    transforms both classes_df and online_classes_df to compatible forms; StartTime is cast into relative form
    '''
    #cast column names of classes_df to columns of online_classes_df
    classes_df['weekday'] = classes_df['weekday'].apply(weekday_to_DayOfWeek)
    classes_df = classes_df.rename(RENAME_DICT,axis=1)
    
    #cast StartTime to hh:mm format
    online_classes_df['StartTime'] = online_classes_df['StartTime'].apply(StartTime_to_class_time)
    
    return classes_df, online_classes_df

def sort_dfs(classes_df: DataFrame,
             online_classes_df: DataFrame,
             abs_times: Series) -> Tuple[DataFrame,DataFrame]:
    '''
    sort both classes_df and online_classes_df in chronological order following the absolute time abs_times
    '''
    
    if online_classes_df.shape[0] != len(abs_times):
        raise ValueError('abs_times incompatible with online_classes_df')
    
    online_classes_df = online_classes_df.iloc[abs_times.sort_values().index]
    
    dow = online_classes_df['DayOfWeek'].unique()
    classes_df = classes_df[classes_df['DayOfWeek'].isin(dow)]
    
    def g(a):
        def h(x):
            out = np.argwhere(online_classes_df['DayOfWeek'].unique()==x)
            return out.item()
        if a.name == 'DayOfWeek':
            a = a.apply(h)
        return a

    classes_df = classes_df.sort_values(by=['DayOfWeek','StartTime'],key = g)

    return classes_df, online_classes_df

def form_candidate_pairs(classes_df : DataFrame, 
                         online_classes_df: DataFrame) -> Tuple[DataFrame,DataFrame,DataFrame]:
    
    
    candidate_pairs_df = pd.DataFrame(columns=[OWN_CLASSES_INDEX,
                                               ONLINE_CLASSES_INDEX,
                                               'correct_StartTime',
                                               'correct_DayOfWeek',
                                               'correct_Id',
                                               'correct_Name',
                                               'correct_LocationId',
                                               'correct_IsCanceled',
                                               'correct_IsReservable',
                                               'correct_IsEnabled'])
    
    for i, cls_own in classes_df.iterrows():
        for j, cls_online in online_classes_df.iterrows():

            rec = {OWN_CLASSES_INDEX: i,
                   ONLINE_CLASSES_INDEX: j,
                   'correct_StartTime': cls_online['StartTime'] == cls_own['StartTime'],
                   'correct_DayOfWeek': cls_online['DayOfWeek'] == cls_own['DayOfWeek'],
                   'correct_Id': cls_online['Id'] == cls_own['Id'],
                   'correct_Name': cls_online['Name'] == cls_own['Name'],
                   'correct_LocationId': cls_online['LocationId'] == cls_own['LocationId'],
                   'correct_IsCanceled': cls_online['IsCanceled'] == False,
                   'correct_IsReservable': (cls_online['IsReservable'] == True and cls_online['ReservationButton'] != 0),
                   'correct_IsEnabled': cls_online['IsEnabled'] == True}
            
            candidate_pairs_df = candidate_pairs_df.append(rec,ignore_index=True)
    
    candidate_pairs_df = candidate_pairs_df.set_index([OWN_CLASSES_INDEX,ONLINE_CLASSES_INDEX])
    
    dtypes=(bool,bool,np.int64,bool,bool,bool,bool,bool)
    for dtype, col in zip(dtypes,candidate_pairs_df.iteritems()):
        colname, colval = col
        candidate_pairs_df[colname] = candidate_pairs_df[colname].astype(dtype)
        
    return classes_df, online_classes_df, candidate_pairs_df



def extract_matches(classes_df: DataFrame,
                    online_classes_df: DataFrame,
                    candidate_pairs_df: DataFrame) -> Tuple[DataFrame,DataFrame]:
    
    mask = candidate_pairs_df['correct_StartTime'] | candidate_pairs_df['correct_Id'] | candidate_pairs_df['correct_Name']
    mask &= candidate_pairs_df['correct_DayOfWeek']

    basic_matches_df = candidate_pairs_df.loc[mask]

    exact_flags = ['correct_StartTime',
                   'correct_DayOfWeek',
                   'correct_Id',
                   'correct_Name',
                   'correct_LocationId',
                   'correct_IsCanceled',
                   'correct_IsEnabled']
    exact_matches_df = candidate_pairs_df.loc[candidate_pairs_df.loc[:,exact_flags].all(axis=1)]
    
    return basic_matches_df, exact_matches_df

def print_verbose(classes_df: DataFrame,
                  online_classes_df: DataFrame,
                  basic_matches_df: DataFrame, 
                  exact_matches_df: DataFrame,
                  abs_times : DataFrame) -> None:
    
    ownid = basic_matches_df.index.get_level_values(0)

    for own_id, rec in basic_matches_df.groupby(by=ownid,sort=False):
        vals = exact_matches_df.index.get_level_values(0)
        if own_id in vals:
            online_ids = [exact_matches_df.loc[own_id].index.item()]
        else:
            online_ids = rec.index.get_level_values(1)

        df1 = online_classes_df.loc[online_ids]
        df0 = pd.DataFrame(columns=df1.columns)
        df0 = df0.append(classes_df.loc[[own_id]],ignore_index=True)
        df0 = df0.append({col: '---' for col in df0.columns},ignore_index=True)
        df_full = pd.concat((df0,df1))
        print('-'*80)
        date = datetime.fromisoformat(abs_times[online_ids].unique()[0])
        print(f'{date.strftime("%A %d. %B %Y")}')
        print('-'*80)
        print(df_full)
            
def print_nonverbose(classes_df: DataFrame,
                     exact_matches_df: DataFrame,
                     abs_times: Series) -> None:
    
    headers = [s.replace('correct_','') for s in exact_matches_df.columns.to_list()]

    cdf = classes_df.copy()
    cdf['platinium match'] = 'NO'
    for i, rec in exact_matches_df.iterrows():
        own_id,online_id = i
        online_id = int(online_id)
#             cdf.loc[own_id,'matched online_id'] = online_id
        cdf.loc[own_id,'StartTime'] = abs_times[online_id]
        cdf.loc[own_id,'platinium match'] = 'YES'

    cdf['DayOfWeek'] = cdf['DayOfWeek'].apply(DayOfWeek_to_weekday)
    print(cdf)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--authfile', type=str, default='auth.json')
    parser.add_argument('--classfile', type=str, default='classes.json')
    parser.add_argument('--week_ahead', type=int, default=1)
    parser.add_argument('--verbose', const=True, action='store_const', default=False)

    args = parser.parse_args()

    with open(args.authfile,'r') as file:
        d = json.load(file)

    username = d['username']
    password = d['password']

    client = Client(username=username,password=password,auto_log=True)

    with open(args.classfile,'r') as file:
        classes = json.load(file)
        
    week_ahead = args.week_ahead  
    verbose = args.verbose
    
    cc = CompareClasses(client,classes)
    cc._set_dates()
    cc._generate_dfs()
    cc._generate_matches()
    
    if verbose:
        cc._print_verbose()
    else:
        cc._print_nonverbose()
        
#     classes_df = generate_own_classes_df(classes)
#     location_ids = extract_location_ids(classes_df)
#     start_date = datetime.today()+timedelta(days=week_ahead*7)
    
#     online_classes_df = generate_online_classes_df(cl,location_ids,start_date,7)
#     abs_times = online_classes_df['StartTime'].copy()
    
#     classes_df, online_classes_df = transform_dfs(classes_df,online_classes_df)
#     classes_df, online_classes_df = sort_dfs(classes_df,online_classes_df,abs_times)

#     classes_df, online_classes_df, candidate_pairs_df = form_candidate_pairs(classes_df,online_classes_df)   
#     basic_matches_df, exact_matches_df = extract_matches(classes_df, online_classes_df, candidate_pairs_df)
    
#     if verbose:
        
#         print_verbose(classes_df,online_classes_df,basic_matches_df,exact_matches_df)
#     else:
        
#         print_nonverbose(exact_matches_df,abs_times)
