"""
An unofficial Python module for the Fitness Platinium Gym API
.. moduleauthor:: Jacek Grela
"""

from typing import Dict, List

import json
import random
import requests
from requests_toolbelt import MultipartEncoder
import string

from .exceptions import APIException, APIRequestException

class Client:
    BASE_URL = 'https://stats.fitnessplatinium.pl:13002/club-api'

    def __init__(self, username: str, password: str, auto_log: bool = False):
        self.headers = self._init_headers()
        self.username = username
        self.password = password

        self.session = self._init_session()

        self.logged = False
        self.access_token = None
        self.api_session_data = None

        if auto_log:
            self.login()

    def _init_headers(self) -> Dict:
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "content-type": "application/json",
        #     "pragma": "no-cache",
        #     "sec-ch-ua": "\"Chromium\";v=\"93\", \" Not;A Brand\";v=\"99\"",
        #     "sec-ch-ua-mobile": "?0",
        #     "sec-ch-ua-platform": "\"Linux\"",
        #     "sec-fetch-dest": "empty",
        #     "sec-fetch-mode": "cors",
        #     "sec-fetch-site": "same-site"
          }
        return headers

    def _init_session(self) -> requests.Session:

        session = requests.session()
        session.headers.update(self.headers)
        return session

    def _create_classes_uri(self) -> str:
        return self.BASE_URL+'/pl/classes'

    def _create_locations_uri(self) -> str:
        #return self.BASE_URL+'/pl/locations' alternative?
        return self.BASE_URL+'/pl/locations/with-classes'

    def _create_list_reservations_uri(self, user_id: int) -> str:
        return self.BASE_URL+'/pl/classes/user-active-reservations/'+str(user_id)

    def _create_reservations_history_uri(self, user_id: int) -> str:
        return self.BASE_URL+'/pl/classes/user-reservations-history/'+str(user_id)

    def _create_add_reservation_uri(self) -> str:
        return self.BASE_URL+'/pl/classes/add-reservation'

    def _create_remove_reservation_uri(self) -> str:
        return self.BASE_URL+'/pl/classes/remove-reservation'

    def _create_login_uri(self) -> str:
        return self.BASE_URL+'/user-token'

    def _request(self, method: str, uri: str, **kwargs) -> Dict:
        response = getattr(self.session,method)(uri,**kwargs)
        return self._handle_response(response)

    def _handle_response(self,response: requests.Response) -> Dict:
        # self.response = response
        if not (200 <= response.status_code < 300):
            raise APIException(response, response.status_code, response.text)
        try:
            return response.json()
        except ValueError:
            # return dict()
            raise APIRequestException('Invalid Response: %s' % response.text)

    def _get(self, uri: str, **kwargs):
        return self._request(method='get',uri=uri,**kwargs)

    def _post(self, uri: str, **kwargs):
        return self._request(method='post',uri=uri,**kwargs)

    def _put(self, uri: str, **kwargs):
        return self._request(method='put',uri=uri,**kwargs)

    def _delete(self, uri: str, **kwargs):
        return self._request(method='delete',uri=uri,**kwargs)

    def get_locations(self):
        uri = self._create_locations_uri()
        return self._get(uri)

    def get_classes(self,
                    location_id: int = 3,
                    start_date: str = '2021-10-20T10:00:00',
                    days: int = 1) -> List:
        
        uri = self._create_classes_uri()
        fields = {'LocationId':int(location_id),
                  'StartDate':start_date,
                  'Days':days,
                  'UserId':self.api_session_data['UserId']}

        return self._post(uri,data=json.dumps(fields))

    def get_active_reservations(self) -> List:
        uri = self._create_list_reservations_uri(user_id = self.api_session_data['UserId'])
        return self._get(uri)

    def get_reservations_history(self) -> List:
        uri = self._create_reservations_history_uri(user_id = self.api_session_data['UserId'])
        return self._get(uri)

    def add_reservation(self, class_id: int, date: str) -> Dict:
        uri = self._create_add_reservation_uri()
        fields = {"UserId": self.api_session_data['UserId'],
                  "Date": date, #StartTime from get_classes
                  "ClassScheduleId": class_id} #Id from get_classes

        return self._post(uri,data=json.dumps(fields))

    def remove_reservation(self, class_id: int, date: str) -> Dict:
        uri = self._create_remove_reservation_uri()
        fields = {"UserId": self.api_session_data['UserId'],
                  "Date": date,
                  "ClassScheduleId": class_id}

        return {"Status": self._post(uri,data=json.dumps(fields))}

    def login(self):
        print(f'logging in as: {self.username} ; len(password)={len(self.password)}')
        if self.username == "" and self.password == "":
            print('empty username and password; authfile is likely incorrect!')

        uri = self._create_login_uri()

        h = self.headers.copy()
        wfb_id =''.join(random.sample(string.ascii_letters+string.digits,16))

        fields = {'login': self.username,
                  'password': self.password,
                  'facebookid': 'undefined'}
        
        data = MultipartEncoder(fields=fields, boundary='----WebKitFormBoundary'+wfb_id)
        h["content-type"] = data.content_type
        
        try:
            response = self._post(uri=uri,data=data,headers=h)
            self.access_token = response['access_token']
            self.api_session_data = response['session']
            self.headers["authorization"] = 'Bearer '+ self.access_token
            self.session.headers.update(self.headers)
            self.logged = True
            print('login SUCCESS.')
            print("="*100)
            
        except APIRequestException:
            self.logged = False
            raise RuntimeError('login FAILED... check auth file?')
        
        
        
