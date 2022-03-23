import pytest

import check_classes

# weekday (strings) <-> DayOfWeek (integers) conversions

def test_proper_conversion_weekday_to_DayOfWeek():

    assert check_classes.weekday_to_DayOfWeek('SUN') == 0
    assert check_classes.weekday_to_DayOfWeek('MON') == 1
    assert check_classes.weekday_to_DayOfWeek('TUE') == 2
    assert check_classes.weekday_to_DayOfWeek('WED') == 3
    assert check_classes.weekday_to_DayOfWeek('THU') == 4
    assert check_classes.weekday_to_DayOfWeek('FRI') == 5
    assert check_classes.weekday_to_DayOfWeek('SAT') == 6

def test_wrong_conversion_weekday_to_DayOfWeek():
    with pytest.raises(ValueError,match='unknown weekday'):
        check_classes.weekday_to_DayOfWeek('aaa')

def test_proper_conversion_DayOfWeek_to_weekday():
    assert check_classes.DayOfWeek_to_weekday(0) == 'SUN'
    assert check_classes.DayOfWeek_to_weekday(1) == 'MON'
    assert check_classes.DayOfWeek_to_weekday(2) == 'TUE'
    assert check_classes.DayOfWeek_to_weekday(3) == 'WED'
    assert check_classes.DayOfWeek_to_weekday(4) == 'THU'
    assert check_classes.DayOfWeek_to_weekday(5) == 'FRI'
    assert check_classes.DayOfWeek_to_weekday(6) == 'SAT'

def test_wrong_conversion_DayOfWeek_to_weekday():
    with pytest.raises(ValueError,match='unknown DayOfWeek'):
        check_classes.DayOfWeek_to_weekday(123)

def test_conversion_weekday_DayOfWeek_back_and_forth_involution():
    assert check_classes.DayOfWeek_to_weekday(check_classes.weekday_to_DayOfWeek('SUN')) == 'SUN'
    assert check_classes.DayOfWeek_to_weekday(check_classes.weekday_to_DayOfWeek('MON')) == 'MON'
    assert check_classes.DayOfWeek_to_weekday(check_classes.weekday_to_DayOfWeek('TUE')) == 'TUE'
    assert check_classes.DayOfWeek_to_weekday(check_classes.weekday_to_DayOfWeek('WED')) == 'WED'
    assert check_classes.DayOfWeek_to_weekday(check_classes.weekday_to_DayOfWeek('THU')) == 'THU'
    assert check_classes.DayOfWeek_to_weekday(check_classes.weekday_to_DayOfWeek('FRI')) == 'FRI'
    assert check_classes.DayOfWeek_to_weekday(check_classes.weekday_to_DayOfWeek('SAT')) == 'SAT'

    assert check_classes.weekday_to_DayOfWeek(check_classes.DayOfWeek_to_weekday(0)) == 0
    assert check_classes.weekday_to_DayOfWeek(check_classes.DayOfWeek_to_weekday(1)) == 1
    assert check_classes.weekday_to_DayOfWeek(check_classes.DayOfWeek_to_weekday(2)) == 2
    assert check_classes.weekday_to_DayOfWeek(check_classes.DayOfWeek_to_weekday(3)) == 3
    assert check_classes.weekday_to_DayOfWeek(check_classes.DayOfWeek_to_weekday(4)) == 4
    assert check_classes.weekday_to_DayOfWeek(check_classes.DayOfWeek_to_weekday(5)) == 5
    assert check_classes.weekday_to_DayOfWeek(check_classes.DayOfWeek_to_weekday(6)) == 6
    
    
# test class_time <-> StartTime conversions

def test_proper_conversion_class_time_to_StartTime():
    date = check_classes.datetime(year=2022,month=1,day=1,hour=18,minute=45,second=0,microsecond=0)
    assert check_classes.class_time_to_StartTime(base_date=date,class_time='10:00') == check_classes.datetime(year=2022,month=1,day=1,hour=10,minute=0,second=0,microsecond=0)
    
def test_wrong_conversion_class_time_to_StartTime_class_time_wrong_format():
    with pytest.raises(ValueError,match='wrong class_time format; should be HH:MM'):
        date = check_classes.datetime(year=2022,month=1,day=1,hour=18,minute=45,second=0,microsecond=0)
        out = check_classes.class_time_to_StartTime(base_date=date,class_time='10,00')

def test_proper_conversion_StartTime_to_class_time():
    date = check_classes.datetime(year=2022,month=5,day=3,hour=18,minute=35,second=10,microsecond=0)
    isoformat = date.isoformat()
    assert check_classes.StartTime_to_class_time(StartTime = isoformat) == '18:35'
    
def test_wrong_conversion_StartTime_to_class_time_StartTime_wrong_format():
    isoformat = '2022-05-03T18:35,10'
    with pytest.raises(ValueError,match='Invalid isoformat string'):
        out = check_classes.StartTime_to_class_time(StartTime = isoformat)
    
    
    
# test classes_df generation
def test_proper_generate_own_classes_df():
    classes = {'MON':[
                        {
                          "location_id": 3,
                          "class_name": "BRZUCHOMANIA",
                          "class_id": 6916,
                          "class_time": "18:00"
                        }
                     ],
               'TUE':[
                       {
                          "location_id": 4,
                          "class_name": "KORT 2 - Rezerwacja Squash",
                          "class_id": 510,
                          "class_time": "18:30"
                        }
               ],
               'WED':[],
               'THU':[],
               'FRI':[],
               'SAT':[],
               'SUN':[]
              }
    classes_df = check_classes.generate_own_classes_df(classes)
    assert isinstance(classes_df,check_classes.DataFrame)
    assert all (k in classes_df.columns for k in check_classes.OWN_CLASSES_COLUMNS) # all columns are correctly named
    assert classes_df.index.name == check_classes.OWN_CLASSES_INDEX # index has the correct name
    assert classes_df['location_id'].dtype == check_classes.np.int64
    assert classes_df['class_id'].dtype == check_classes.np.int64
    assert classes_df.shape == (2,5)
    
def test_proper_generate_own_classes_df_incomplete_classes_dict():
    classes = {'MON':[
                        {
                          "location_id": 3,
                          "class_name": "BRZUCHOMANIA",
                          "class_id": 6916,
                          "class_time": "18:00"
                        }
                     ],
               'TUE':[
                       {
                          "location_id": 4,
                          "class_name": "KORT 2 - Rezerwacja Squash",
                          "class_id": 510,
                          "class_time": "18:30"
                        }
               ],
               'WED':[]
              }
    classes_df = check_classes.generate_own_classes_df(classes)
    assert isinstance(classes_df,check_classes.DataFrame)
    assert all (k in classes_df.columns for k in check_classes.OWN_CLASSES_COLUMNS) # all columns are correctly named
    assert classes_df.index.name == check_classes.OWN_CLASSES_INDEX # index has the correct name
    assert classes_df['location_id'].dtype == check_classes.np.int64
    assert classes_df['class_id'].dtype == check_classes.np.int64
    assert classes_df.shape == (2,5)
    
def test_wrong_generate_own_classes_df_incorrect_classes_dict_format():
    classes = {'MON':[
                        {
                          "locationId": 3,
                          "className": "BRZUCHOMANIA",
                          "ClassId": 6916,
                          "ClassName": "18:00"
                        }
                     ],
               'TUE':[
                       {
                          "location_id": 4,
                          "class_name": "KORT 2 - Rezerwacja Squash",
                          "class_id": 510,
                          "class_time": "18:30"
                        }
               ],
               'WED':[],
               'THU':[],
               'FRI':[],
               'SAT':[],
               'SUN':[]
              }
    with pytest.raises(ValueError,match='wrong classes format'):
        classes_df = check_classes.generate_own_classes_df(classes)

def test_wrong_generate_own_classes_df_incomplete_classes_dict_format():
    classes = {'MON':[
                        {
                          "location_id": 3,
                          "class_name": "BRZUCHOMANIA",
                          "class_id": 6916,
                        }
                     ],
               'TUE':[
                       {
                          "location_id": 4,
                          "class_time": "18:30"
                        }
               ],
               'WED':[]
              }
    with pytest.raises(ValueError,match='wrong classes format'):
        classes_df = check_classes.generate_own_classes_df(classes)
        

        
# test extracting all location_ids from classes_df

def test_extract_location_ids():
    from test_mock import classes_df_dict_mock
    
    classes_df = check_classes.pd.DataFrame(classes_df_dict_mock)
    classes_df.index.name = check_classes.OWN_CLASSES_INDEX
    classes_df['location_id'] = classes_df['location_id'].astype(check_classes.np.int64)
    classes_df['class_id'] = classes_df['class_id'].astype(check_classes.np.int64)
    
    location_ids = check_classes.extract_location_ids(classes_df)
    
    assert isinstance(location_ids,list)
    assert location_ids == [3,4]
    
def test_extract_location_ids_wrong_classes_df_no_location_id():
    from test_mock import classes_df_dict_mock
    
    classes_df = check_classes.pd.DataFrame(classes_df_dict_mock)
    classes_df.index.name = check_classes.OWN_CLASSES_INDEX
    del classes_df['location_id']
    classes_df['class_id'] = classes_df['class_id'].astype(check_classes.np.int64)
    
    with pytest.raises(ValueError,match='wrong classes_df format; no location_id column'):
        location_ids = check_classes.extract_location_ids(classes_df)
    

# test generating online_classes_df 

def test_generate_online_classes_df(mocker):
    from test_mock import get_classes_output_mock
    
    def mock_get_classes(self,location_id,start_date,days):
        return get_classes_output_mock
    
    def mock_init(self,username,password,auto_log):
        pass

    mocker.patch(
        'check_classes.Client.get_classes',
        mock_get_classes
    )
    mocker.patch(
        'check_classes.Client.__init__',
        mock_init
    )

    client = check_classes.Client(username='aa',password='bb',auto_log=True)
    date = check_classes.datetime(year=2022,month=5,day=3,hour=18,minute=35,second=10,microsecond=0)
    online_classes_df = check_classes.generate_online_classes_df(client=client,
                                                                 location_ids=[3],
                                                                 date=date,
                                                                 days_forward=1)
    assert all (k in online_classes_df.columns for k in check_classes.ONLINE_CLASSES_COLUMNS)
    assert online_classes_df.index.name == check_classes.ONLINE_CLASSES_INDEX
    assert online_classes_df['Id'].dtype == check_classes.np.int64
    assert online_classes_df['LocationId'].dtype == check_classes.np.int64
    assert online_classes_df['DayOfWeek'].dtype == check_classes.np.int64
    assert online_classes_df['ReservationButton'].dtype == check_classes.np.int64
    assert online_classes_df['IsReserved'].dtype == bool
    assert online_classes_df['IsReservable'].dtype == bool
    assert online_classes_df['IsEnabled'].dtype == bool
    assert online_classes_df['IsCanceled'].dtype == bool
    assert online_classes_df.shape == (10,10)
    
def test_generate_online_classes_df_wrong_name_in_cols(mocker):
    from test_mock import get_classes_output_mock
    
    cols = check_classes.ONLINE_CLASSES_COLUMNS
    cols+=['wrong_column']
    
    def mock_get_classes(self,location_id,start_date,days):
        return get_classes_output_mock
    
    def mock_init(self,username,password,auto_log):
        pass

    mocker.patch(
        'check_classes.Client.get_classes',
        mock_get_classes
    )
    mocker.patch(
        'check_classes.Client.__init__',
        mock_init
    )

    client = check_classes.Client(username='aa',password='bb',auto_log=True)
    date = check_classes.datetime(year=2022,month=5,day=3,hour=18,minute=35,second=10,microsecond=0)
    with pytest.raises(KeyError,match='unknown name in cols'):
        online_classes_df = check_classes.generate_online_classes_df(client=client,
                                                                     location_ids=[3],
                                                                     date=date,
                                                                     days_forward=1,
                                                                     cols=cols)
        
def test_transform_dfs():
    from test_mock import classes_df_dict_mock, online_classes_df_dict_mock
    from test_mock import classes_transformed_df_dict_mock, online_classes_transformed_df_dict_mock
    
    # prepare mock classes_df
    classes_df = check_classes.pd.DataFrame(classes_df_dict_mock)
    classes_df.index.name = check_classes.OWN_CLASSES_INDEX
    classes_df['location_id'] = classes_df['location_id'].astype(check_classes.np.int64)
    classes_df['class_id'] = classes_df['class_id'].astype(check_classes.np.int64)
    
    # prepare mock online_classes_df
    online_classes_df = check_classes.pd.DataFrame(online_classes_df_dict_mock)
    online_classes_df.index.name = check_classes.ONLINE_CLASSES_INDEX
    
    classes_df, online_classes_df = check_classes.transform_dfs(classes_df, online_classes_df)
    
    assert all (k in classes_df.columns for k in check_classes.RENAME_DICT.values()) # ensure all new column names are there
    assert all (k not in classes_df.columns for k in check_classes.RENAME_DICT.keys()) # ensure no old column names are there
    assert all (k in check_classes.DAYOFWEEK_INTS for k in classes_df['DayOfWeek'].to_list()) # ensure weekday->DayOfWeek in classes_df
    assert all ( len(st.split(':'))==2 for st in online_classes_df['StartTime'].to_list()) # ensure StartTime -> class_time in online_classes_df
    
    online_classes_transformed_df = check_classes.pd.DataFrame(online_classes_transformed_df_dict_mock)
    classes_transformed_df = check_classes.pd.DataFrame(classes_transformed_df_dict_mock)
        
    assert online_classes_df.equals(online_classes_transformed_df)
    assert classes_df.equals(classes_transformed_df)
    
def test_sort_dfs():
    
    # prepare mock classes_df, online_classes_df
    from test_mock import classes_transformed_df_dict_mock, online_classes_transformed_df_dict_mock
    classes_df = check_classes.pd.DataFrame(classes_transformed_df_dict_mock)
    classes_df.index.name = check_classes.OWN_CLASSES_INDEX
    online_classes_df = check_classes.pd.DataFrame(online_classes_transformed_df_dict_mock)
    online_classes_df.index.name = check_classes.ONLINE_CLASSES_INDEX
    
    # abs_times are needed before the transform_dfs
    from test_mock import online_classes_df_dict_mock
    abs_times = check_classes.pd.DataFrame(online_classes_df_dict_mock)['StartTime'].copy()
    
    classes_df, online_classes_df = check_classes.sort_dfs(classes_df, online_classes_df, abs_times)
    
    from test_mock import classes_transformed_sorted_df_dict_mock, online_classes_transformed_sorted_df_dict_mock
    classes_df_sorted = check_classes.pd.DataFrame(classes_transformed_sorted_df_dict_mock)
    online_classes_df_sorted = check_classes.pd.DataFrame(online_classes_transformed_sorted_df_dict_mock)
    assert classes_df.equals(classes_df_sorted)
    assert online_classes_df.equals(online_classes_df_sorted)

def test_sort_dfs_incompatible_abs_times():
    
    # prepare mock classes_df, online_classes_df
    from test_mock import classes_transformed_df_dict_mock, online_classes_transformed_df_dict_mock
    classes_df = check_classes.pd.DataFrame(classes_transformed_df_dict_mock)
    classes_df.index.name = check_classes.OWN_CLASSES_INDEX
    online_classes_df = check_classes.pd.DataFrame(online_classes_transformed_df_dict_mock)
    online_classes_df.index.name = check_classes.ONLINE_CLASSES_INDEX
    
    # abs_times are needed before the transform_dfs
    from test_mock import online_classes_df_dict_mock
    abs_times = check_classes.pd.DataFrame(online_classes_df_dict_mock)['StartTime'].copy()
    abs_times = abs_times[1:]
    with pytest.raises(ValueError,match='abs_times incompatible with online_classes_df'):
        classes_df, online_classes_df = check_classes.sort_dfs(classes_df, online_classes_df, abs_times)
        
def test_form_candidate_pairs():
    
    from test_mock import classes_transformed_sorted_df_dict_mock, online_classes_transformed_sorted_df_dict_mock
    classes_df = check_classes.pd.DataFrame(classes_transformed_sorted_df_dict_mock)
    online_classes_df = check_classes.pd.DataFrame(online_classes_transformed_sorted_df_dict_mock)    
    
    classes_df, online_classes_df, candidate_pairs_df = check_classes.form_candidate_pairs(classes_df, online_classes_df)
    
    assert candidate_pairs_df['correct_Id'].dtype == check_classes.np.int64
    
    # print(candidate_pairs_df.to_dict())
    # assert False
    
    from test_mock import candidate_pairs_df_dict_mock
    candidate_pairs_df_mock = check_classes.pd.DataFrame(candidate_pairs_df_dict_mock)
    assert candidate_pairs_df_mock.equals(candidate_pairs_df)
    
def test_extract_matches():
    
    from test_mock import classes_transformed_sorted_df_dict_mock, online_classes_transformed_sorted_df_dict_mock
    from test_mock import candidate_pairs_df_dict_mock
    classes_df = check_classes.pd.DataFrame(classes_transformed_sorted_df_dict_mock)
    online_classes_df = check_classes.pd.DataFrame(online_classes_transformed_sorted_df_dict_mock)
    candidate_pairs_df = check_classes.pd.DataFrame(candidate_pairs_df_dict_mock)
    
    basic_matches_df, exact_matches_df = check_classes.extract_matches(classes_df,online_classes_df,candidate_pairs_df)
