import asyncio
import argparse
from datetime import datetime, timedelta
import time
import json

from platinium import Client
from platinium import APIException
from reserve_tools import CompareClasses

class booker:

    def __init__(self,
                 authfile: str,
                 reservefile: str,
                 timestep: float = 0.001,
                 no_tries: int = 5,
                 t_reconnect: int = 3500,
                 dt: str = '0'):

        self.authfile = authfile
        self.reservefile = reservefile

        self.timestep = timestep
        self.no_tries = no_tries
        self.t_reconnect = timedelta(seconds=t_reconnect)
        self.dt = str_to_timedelta(dt)

    def prepare_booker(self):

        self.load_auth(self.authfile)
        self.load_classes(self.reservefile)

        self.client = Client(username=self.username,
                             password=self.password,
                             auto_log=True)
        
        self.cc = CompareClasses(self.client,self.classes_dict)

    def get_current_time(self):

        t = datetime.now()
        t = t + self.dt
        return t

    def load_auth(self,
                  authfile: str):

        with open(authfile,'r') as f:
            d = json.load(f)

        self.username = d['username']
        self.password = d['password']

    def load_classes(self,
                     reservefile: str):

        with open(reservefile,'r') as f:
            c = json.load(f)

        self.classes = [val for key,val in c.items()]
        self.classes_dict = c

    async def reserve_loop(self):
        t_now = self.get_current_time()
        current_weekday = t_now.weekday()
        if self.dt:
            print(f'time delta = {self.dt}')
        print(f'{t_now}: standby')
        check_classes = True

        while True:
            await asyncio.sleep(self.timestep)
            t_now = self.get_current_time()
            new_weekday = t_now.weekday()

            # do reservation list checks before making any reservations
            t_now_plus_delta = t_now + self.t_reconnect
            if (t_now_plus_delta.weekday() != current_weekday) and check_classes:
                print('reservation is near... comparing classes')
                self.cc._set_dates(start_date = t_now_plus_delta,
                                   week_ahead = 0,
                                   days_ahead = 1)
                self.cc._generate_dfs()
                self.cc._generate_matches()
                self.cc._print_nonverbose()
                check_classes = False

            if current_weekday != new_weekday:
                current_weekday = new_weekday
                check_classes = True #put the flag back

                for cls in self.classes[current_weekday]:
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

                    for i in range(self.no_tries):
                        try:
                            out = self.client.add_reservation(class_id=class_id,date=date.isoformat())
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
                        out_class = self.client.get_classes(location_id=cls['location_id'],start_date=date0.isoformat())

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

    async def login_loop(self):
        while True:

            t_now = self.get_current_time()
            self.client.login()
            sid = self.client.api_session_data['SessionId']
            print(f"{t_now}: connecting to FP (SessionId={sid})")
            await asyncio.sleep(self.t_reconnect.seconds)
            #print(client.access_token)


def str_to_timedelta(s: str) -> timedelta:
    
    prefix = s[0]
    
    ss = s.lstrip('r').split(':')
    print(ss)
    out = [0,0,0]
    if len(ss)==1:
        out[-1] = int(ss[0])
    elif len(ss)==2:
        out[-1] = int(ss[1])
        out[-2] = int(ss[0])
    elif len(ss)==3:
        out = list(map(lambda x: int(x),ss))
    
    print(out)
    delta = timedelta(hours=out[0],minutes=out[1],seconds=out[2])
    
    if prefix=='r':
        delta = -delta
        
    print(delta)    
    return delta
            
async def main(booker):
    t1 = asyncio.create_task(booker.reserve_loop())
    t2 = asyncio.create_task(booker.login_loop())
    await asyncio.gather(t1,t2)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--authfile', type=str, default='auth.json')
    parser.add_argument('--reservefile', type=str, default='reservations.json')
    parser.add_argument('--dt', type=str, default='0',help='set global advance time lag in formats {r}HH:MM:SS, {r}MM:SS, {r}SS (use prefix {r} for retarded)')
    parser.add_argument('--timestep', type=float, default=0.001 ,help='micro-timestep')
    parser.add_argument('--t_reconnect', type=int, default=3600 ,help='client reconnect time')
    parser.add_argument('--no_tries', type=int, default=5 ,help='number of unsuccesful tries before exit')
    parser.add_argument('--verbose', const=True, action='store_const', default=False)

    args = parser.parse_args()

    authfile = args.authfile
    reservefile = args.reservefile
    
    dt = args.dt
    timestep = args.timestep
    no_tries = args.no_tries
    t_reconnect = args.t_reconnect
    verbose = args.verbose


    b = booker(authfile=authfile,
               reservefile=reservefile,
               dt=dt,
               timestep=timestep,
               no_tries=no_tries,
               t_reconnect=t_reconnect)
    
    print("="*100)
    print(f"auth file: {authfile}")
    print(f"reservations file: {reservefile}")
    print(f"time lag dt = {dt} ")
    print(f"script local time: {datetime.now()+b.dt}")
    print(f"micro-timestep = {timestep} sec")
    print(f"client reconnect time = {t_reconnect} sec")
    print(f"number of tries before exit = {no_tries}")
    print("="*100)
    
    b.prepare_booker()

    asyncio.run(main(b))
