import json
from datetime import datetime
from json2html import json2html
from tqdm import tqdm

from platinium import Client
from reserve_tools import generate_online_classes_df, StartTime_to_class_time,DayOfWeek_to_weekday, RENAME_DICT


def generate_tab(client: Client,
                 location_id: int,
                 start_date: datetime = None):
    '''
    generate html table with classes available at location_id
    '''
    if start_date == None:
        start_date = datetime.now()
        
    online_classes_df = generate_online_classes_df(client=client,
                                                   location_ids=[location_id],
                                                   date=start_date)

    online_classes_df['StartTime'] = online_classes_df['StartTime'].apply(StartTime_to_class_time)
    online_classes_df['DayOfWeek'] = online_classes_df['DayOfWeek'].apply(DayOfWeek_to_weekday)
    online_classes_df = online_classes_df.rename({v:k for k,v in RENAME_DICT.items()},axis=1).loc[::,RENAME_DICT.keys()]
    online_classes_df = online_classes_df.sort_values(by='class_time')
    
    
    def parse_div(location_id,weekday,class_name,class_id,class_time):
        return f'''<div class="activity-cell" data-location-id={location_id} data-day="{weekday}" data-class-name="{class_name}" data-class-id={class_id} data-class-time="{class_time}"><h6>{class_name}</h6><p>id = {class_id}</p></div>'''

    f = lambda x: parse_div(x['location_id'],x['weekday'],x['class_name'],x['class_id'],x['class_time'])

    online_classes_df['parsed_div'] = online_classes_df.apply(f,axis=1)
    online_classes_df['cumcount'] = online_classes_df.groupby(['class_time','weekday']).cumcount()
    rdict = {'MON':'Poniedziałek','TUE':'Wtorek','WED':'Środa','THU':'Czwartek','FRI':'Piątek','SAT':'Sobota','SUN':'Niedziela'}
    online_classes_df['weekday'] = online_classes_df['weekday'].replace(rdict)
    pvt = online_classes_df.pivot(index='weekday',columns=['class_time','cumcount'],values='parsed_div').fillna('')
    
    #ensure all weekdays are in the table
    for day in rdict.values():
        if day not in pvt.index:
            pvt.loc[day] = ''
            print(day)
    
    pvt = pvt.loc[rdict.values()]
    inpt = pvt.to_dict()
    
    # pre-formatting
    l = []
    currh = ''
    hours = {True:'__HOURODD__',False:'__HOUREVEN__'}
    switch = True

    for k,d in inpt.items():
        d0 = dict()
        if currh != k[0]:
            switch= not switch
            d0['__HOUR0__'] = f'{hours[switch]}{k[0]}'
            currh = k[0]

        else:
            d0['__HOUR0__'] = f'{hours[switch]}'

        for k0,v0 in d.items():
            d0[k0] = v0

        l+= [d0]

    inpt = l
    
    #json2html conversion
    tab = json2html.convert(json = inpt,table_attributes=f'''id="loc{location_id}"''',escape=False)
    
    tab = tab.replace('<tr><td>__HOUREVEN__','''<tr class="even"><td class="hour">''')
    tab = tab.replace('<tr><td>__HOURODD__','''<tr class="odd"><td class="hour">''')
    # html = html.replace('<td>__HOUREVEN__','''<td class="hour">''')
    tab = tab.replace('<th>__HOUR0__</th>','''<th class="hour">''')
    tab = tab.replace('''<td><div class="activity-cell"''','''<td class="cell"><div class="activity-cell"''')
    
    return tab


def generate_html(client: Client,
                  template_file: str = 'reservations_tool.template',
                  html_file: str = 'reservations_tool.html',
                  start_date: datetime = None):
    '''
    generate html file with creation/modification reservation tool (to run in web browser)
    '''
    
    print('generating reservations tool HTML file...')
    with open(template_file,'r') as f:
        template = f.read()
        
    locs = client.get_locations()

    location_ids = str([ f'''loc{loc['Id']}''' for loc in locs])
    location_names = str([ f'''{loc['Name']}''' for loc in locs])
    
    tabs = ''
    for loc in tqdm(locs):
        id = loc['Id']
        tabs += generate_tab(client, id, start_date)

    html = template.replace('__CONTAINER__',tabs).replace('__LOCATIONIDS__',location_ids).replace('__LOCATIONNAMES__',location_names)

    with open(html_file,'w') as f:
        f.write(html)