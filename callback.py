
from __future__ import print_function
import httplib2
import os
import pdb 
from datetime import datetime

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/callback.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'callback'

NUM_SERVING = 2
NUM_WAITING = 3
NOSHOW_TIME_LIM = 300
INDEX_FILE_NAME = 'idx_file.dat'
# sheet indicies
NAME = 1
ID = 2
PHONE = 3
EMAIL = 4

SPREADSHEET_ID = '1i119SHQA2Om0ykgpIoP8V4GQOMZf-IrVAotu9yV4m3k'

# assume sheet index starts at 1 due to column labels
SHEET_IDX_START = 1

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'callback.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

# gets all values from spread sheet
def get_values():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    #spreadsheetId = '1i119SHQA2Om0ykgpIoP8V4GQOMZf-IrVAotu9yV4m3k'
    rangeName = 'A2:E'
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=rangeName).execute()
    values = result.get('values', [])
    return values

# Prints out the current state and should always be max the capacity specified
def print_state(state): 
    print ("Current State:")
    for idx, elem in enumerate(state): 
        if idx < NUM_SERVING: 
            print ("%d : [SERVING] %s %s" %(idx, elem[NAME], elem[PHONE])) 
        else: 
            print ("%d : [WAITING] %s %s" %(idx, elem[NAME], elem[PHONE]))

# If there's space left in the capacity, gets next customer(s) to fill up cap
def get_next(state, end_idx): 
    values = get_values()

    # fill in remaining slots

    if len(state) < (NUM_SERVING + NUM_WAITING): 
        try: 
            state.append(values[end_idx])
            end_idx+=1
        except: 
            print ("No more clients")
    else: 
        print ("Too many people in line!")

    return state, end_idx

# removes individual from queue
# need to implement writing done to google spreadsheet here
def done(state, idx):
    try: 
        idx = int(idx)
        if idx >= NUM_SERVING: 
            raise Exception()
        state.pop(idx)
    except: 
        print ("Invalid Index")
    return state

def print_noshow(noshow_list, noshow_timer): 
    print ("No Show List:")
    if not noshow_list:
        print ("None")
    for idx, elem in enumerate(noshow_list):
        elapsed= (datetime.now() - noshow_timer[idx])
        print ("%d : %s time elapsed: %d:%02d" %(idx, elem[NAME], (elapsed.seconds)//60, (elapsed.seconds)%60))        

def move_to_noshow(state, noshow_list, noshow_timer, idx):
    try: 
        idx = int(idx)
        to_add = state.pop(idx)
        print (to_add)
        noshow_list.append(to_add)
        noshow_timer.append(datetime.now())
    except: 
        print ("Invalid Index")
    return state, noshow_list, noshow_timer

def noshow_readd(state, noshow_list, noshow_timer, idx):
    try: 
        idx = int(idx)
        to_add = noshow_list.pop(idx)
        noshow_timer.pop(idx)
        state.append(to_add)
    except: 
        print ("Invalid Index")
    return state, noshow_list, noshow_timer

def noshow_refresh (noshow_list, noshow_timer):
    for idx, elem in enumerate(noshow_list):
        elapsed = (datetime.now() - noshow_timer[idx])
        if elapsed.seconds >= NOSHOW_TIME_LIM:
            noshow_list.pop(idx)
            noshow_timer.pop(idx)
    return noshow_list, noshow_timer

def main():

    values = get_values()

    # initializations 
    state = []
    noshow_list = []
    noshow_timer = []

    # assume that the sheet starts at A2 due to column labels
    sheet_idx = SHEET_IDX_START
    end_idx = SHEET_IDX_START
    # check to see if file is present
    try: 
        idx_file = open(INDEX_FILE_NAME, 'r')
        sheet_idx = int(idx_file.readline())
        idx_file.close()
    except: 
        idx_file = open(INDEX_FILE_NAME, 'w')
        idx_file.close()

    # first population of state, populate to capacity 
    for idx, row in enumerate(values):
        if idx >= (NUM_SERVING+NUM_WAITING):
            break
        if row: 
            state.append(row)
            end_idx +=1
        else: 
            pass

    command = raw_input("--> ")
    split_command = command.split()
    while command != "quit":
        if command == "current": 
            pass
        elif command == "get next":
            state, end_idx = get_next(state, end_idx)
        elif split_command[0] == "done": 
            try: 
                state = done(state, split_command[1])
            except: 
                print ("Please include an index.")
        elif split_command[0] == "noshow":
            if len(split_command) == 1:
                # implement show noshow line here
                print_noshow(noshow_list, noshow_timer)
            else: 
                # implement noshow refresh
                if split_command[1] == "refresh":
                    noshow_list, noshow_timer = noshow_refresh(noshow_list, noshow_timer)
                elif split_command[1] == "readd":
                    state, noshow_list, noshow_timer = noshow_readd(state, noshow_list, noshow_timer, split_command[2])
                else: 
                    # implements noshow INDEX
                    state, noshow_list, noshow_timer = move_to_noshow(state, noshow_list, noshow_timer, split_command[1])
                pass
        else: 
            print ("Command not supported.")

        print_state(state)
        command = raw_input("--> ")
        split_command = command.split()

    idx_file = open(INDEX_FILE_NAME, 'w')
    idx_file.write(str(sheet_idx))
    idx_file.close()

if __name__ == '__main__':
    main()

