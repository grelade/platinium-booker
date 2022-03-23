import asyncio
from datetime import datetime, timedelta
import time
import json

from platinium import Client
from platinium import APIException
from check_classes import CompareClasses

dt = None
#dt = -timedelta(minutes=9)
# dt = - timedelta(days=5)+timedelta(hours=2,minutes=31,seconds=0)
#dt = -timedelta(minutes=10*60+30+10)

#set delta time to 2 seconds before midnight
# tnow = datetime.now()
# dt = tnow.replace(hour=0,minute=0,second=0,microsecond=0)-tnow-timedelta(seconds=2)

# dt -= timedelta(days=1)
# dt += timedelta(days=14)

def get_current_time():
    t = datetime.now()
    if dt:
        t = t + dt
    return t

def load_classes(file,mode='list'):
    with open(file,'r') as file:
        c = json.load(file)
        
    if mode == 'list':
        classes = [val for key,val in c.items()]        
        return classes
    elif mode == 'dict':
        return c
    else:
        print('unknown load_classes mode')


with open('auth.json','r') as file:
    d = json.load(file)
    
username = d['username']
password = d['password']

client = Client(username=username, password=password, auto_log=True)

# classes = list()
# #MONDAY
# classes+=[[{'location_id':3,'class_name':'BRZUCHOMANIA','class_id':304,'class_time':'18:00'}]]
# # classes+=[[{'location_id':3,'class_name':'PILATES','class_id':2623,'class_time':'10:00'}]]
# #TUESDAY
# classes+=[[{'location_id':3,'class_name':'BODY SHAPE','class_id':1603,'class_time':'18:00'},
#            {'location_id':3,'class_name':'TABATA','class_id':1599,'class_time':'19:00'}]]
# #WEDNESDAY
# classes+=[[{'location_id':3,'class_name':'TABATA','class_id':1260,'class_time':'18:00'},
#            {'location_id':3,'class_name':'STRETCHING','class_id':1262,'class_time':'19:00'}]]
# #THURSDAY
# classes+=[[#{'location_id':3,'class_name':'ABT','class_id':1268,'class_time':'17:00'},
#            {'location_id':3,'class_name':'STRETCHING','class_id':1266,'class_time':'18:00'}]]
# #FRIDAY
# classes+=[[{}]]
# #SATURDAY
# classes+=[[{'location_id':3,'class_name':'BRZUCHOMANIA','class_id':297,'class_time':'10:00'}]]
# #SUNDAY
# classes+=[[{'location_id':3,'class_name':'TABATA','class_id':2830,'class_time':'09:00'},
#            {'location_id':3,'class_name':'XCO','class_id':1033,'class_time':'09:00'}]]

classes = load_classes('classes.json',mode='list')
classes_dict = load_classes('classes.json',mode='dict')

timestep= .001
no_tries = 5
t_reconnect = 3500 #session_time = 3600

cc = CompareClasses(client,classes_dict)

async def reserve_loop():
    t_now = get_current_time()
    current_weekday = t_now.weekday()

    print(f'{t_now}: standby')
    check_classes = True
    
    while True:
        await asyncio.sleep(timestep)
        t_now = get_current_time()
        new_weekday = t_now.weekday()
        
        # do reservation list checks before making any reservations
        t_now_plus_delta = t_now+timedelta(seconds=t_reconnect)
        if (t_now_plus_delta.weekday() != current_weekday) and check_classes:
            print('reservation is near... comparing classes')
            cc._set_dates(start_date = t_now_plus_delta,
                          week_ahead = 0,
                          days_ahead = 1)
            cc._generate_dfs()
            cc._generate_matches()
            cc._print_nonverbose()
            check_classes = False
            
        if current_weekday != new_weekday:
            current_weekday = new_weekday
            check_classes = True #put the flag back

            for cls in classes[current_weekday]:
                h,m = cls['class_time'].split(':')
                date = t_now.replace(hour=int(h),minute=int(m),second=0,microsecond=0)+timedelta(days=7)
                class_id = cls['class_id']
                class_name = cls['class_name']
                location_id = cls['location_id']

                success = False

                err_flags = {'wrong_class_id': False,
                               'wrong_class_name':False,
                               'wrong_location_id':False,
                               'wrong_class_time':False,
                               'is_cancelled':False,
                               'not_reservable':False,
                               'is_disabled':False}

                for i in range(no_tries):
                    try:
                        out = client.add_reservation(class_id=class_id,date=date.isoformat())
                        if out['Status'] == 1:
                            print(f"{t_now}: ({i+1} try) made reservation {class_name} {cls['class_time']}")
                            success = True
                            break

                    except APIException:
                        err_flags['wrong_class_id'] = True
                        print('wrong class')

                    if not success:
                        print(f"{t_now}: ({i+1} try) couldnt make a reservation {class_name} {cls['class_time']}; status = {out['Status']}")
                        time.sleep(.1)




                if not success:
                    #figure out reason
                    date0 = t_now.replace(hour=int(0),minute=int(0),second=0,microsecond=0)+timedelta(days=7)
                    out_class = client.get_classes(location_id=cls['location_id'],start_date=date0.isoformat())

                    match_cls = []
                    for c in out_class:
                        if class_id == c['Id']:
                              match_cls+=[c]

                    if len(match_cls)!=1:
                        err_flags['wrong_class_id'] = True
                    else:
                        c = match_cls[0]
                        print(c)
                        if class_name != c['Name']:
                              err_flags['wrong_class_name'] = True
                        if location_id != c['LocationId']:
                              err_flags['wrong_location_id'] = True # dummy flag due to get_classes
                        if date.isoformat() != c['StartTime']:
                              err_flags['wrong_class_time'] = True

                        err_flags['is_cancelled'] = c['IsCanceled'] #not checked yet
                        err_flags['not_reservable'] = not c['IsReservable'] or (c['ReservationButton'] == 0)
                        err_flags['is_disabled'] = not c['IsEnabled'] #not checked yet

                    strout = f"{t_now}: failed reservation {class_name} {cls['class_time']} after {no_tries} attempts.  Reasons: "
                    for key,flag in err_flags.items():
                        if flag: strout+=f'{key}; '
                    print(strout)
    #     else:
    #         print(f'{t_now}: waiting...')

async def login_loop():
    while True:

        t_now = get_current_time()
        client.login()
        sid = client.api_session_data['SessionId']
        print(f"{t_now}: connecting to FP (SessionId={sid})")
        await asyncio.sleep(t_reconnect)
        #print(client.access_token)


async def main():
    t1 = asyncio.create_task(reserve_loop())
    t2 = asyncio.create_task(login_loop())
    await asyncio.gather(t1,t2)

asyncio.run(main())
