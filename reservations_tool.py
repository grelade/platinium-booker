import argparse
import json
import webbrowser
import os

from platinium import Client
from html_tools import generate_html

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('--authfile', type=str, default='auth.json')
    parser.add_argument('--overwrite_html',const=True,action='store_const',default=False,help='forcefully recreates reservations tool html file')
    # parser.add_argument('--reservefile', type=str, default='reservations.json')
    # parser.add_argument('--week_ahead', type=int, default=1)
    # parser.add_argument('--verbose', const=True, action='store_const', default=False)

    args = parser.parse_args()

    toolpath = 'reservations_tool.html'
    if not os.path.exists(toolpath) or args.overwrite_html:
        
        with open(args.authfile,'r') as file:
            d = json.load(file)

        username = d['username']
        password = d['password']

        client = Client(username=username,password=password,auto_log=True)

        generate_html(client,html_file=toolpath)
    
    webbrowser.open_new_tab(f'file://{os.path.realpath(toolpath)}')
