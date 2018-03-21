
from __future__ import print_function
import httplib2
import os
import pdb
import sys
from datetime import datetime
from twilio.rest import Client

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
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'callback'
RESULTS_FILE = 'results.txt'

NUM_SERVING = 20
NUM_WAITING = 0
NOSHOW_TIME_LIM = 300
INDEX_FILE_NAME = 'idx_file.dat'

# sheet indicies
NAME = 1
ID = 2
PHONE = 3
EMAIL = 4

# my own number to send test texts to
twilio_number_testing = os.environ.get('TWILIO_NUMBER_TESTING')

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
def get_values(spreadsheet_id):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    #spreadsheetId = '1i119SHQA2Om0ykgpIoP8V4GQOMZf-IrVAotu9yV4m3k'
    rangeName = 'A2:E'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=rangeName).execute()
    values = result.get('values', [])
    return values

# Prints out the current state and should always be max the capacity specified
def print_state(state, text_count):
    try:
        print ("Current State:")
        for idx, elem in enumerate(state):
            if idx < NUM_SERVING:
                print ("%d : [SERVING] text count %d | %s %s" %(idx,
                    text_count[idx], elem[NAME], elem[PHONE]))
            else:
                print ("%d : [WAITING] text count %d | %s %s" %(idx,
                    text_count[idx], elem[NAME], elem[PHONE]))
    except:
        print ("No Data")

# If there's space left in the capacity, gets next customer(s) to fill up cap
def get_next(spreadsheet_id, state, end_idx, text_count):
    values = get_values(spreadsheet_id)

    # fill in remaining slots

    if len(state) < (NUM_SERVING + NUM_WAITING):
        try:
            state.append(values[end_idx])
            text_count.append(0)
            end_idx+=1
        except:
            print ("No more clients")
    else:
        print ("Too many people in line!")

    return state, end_idx, text_count

def get_next_batch(spreadsheet_id, state, end_idx, text_count, batch_num):
    for elem in range(batch_num):
        try:
            state, end_idx, text_count = get_next(spreadsheet_id, state, end_idx,
                text_count)
        except:
            print ("No more clients")
            return state, end_idx, text_count
    return state, end_idx, text_count

# removes individual from queue
# id_num is the id of the person who serviced
def done(state, idx, text_count, servicer):
    try:
        idx = int(idx)
        if idx >= NUM_SERVING:
            raise Exception()
        removed = state.pop(idx)
        text_count.pop(idx)

        entry = removed[NAME] + " " + removed[ID] + " " + removed[PHONE] + " " + removed[EMAIL]

        done_result = str(datetime.now()) + " Serviced by: " + str(servicer) + " | Serviced: " + str(entry) + "\n"
        # write to file with time stamp + name + photographer
        results = open(RESULTS_FILE, 'a+')
        results.write(str(done_result))
        results.close()
    except:
        print ("Invalid Index")
    return state, text_count

# deletes individual from queue
def delete(state, idx, text_count):
    try:
        idx = int(idx)
        if idx >= NUM_SERVING:
            raise Exception()
        state.pop(idx)
        text_count.pop(idx)
    except:
        print ("Invalid Index")
    return state, text_count

def print_noshow(noshow_list, noshow_timer):
    print ("No Show List:")
    if not noshow_list:
        print ("None")
    for idx, elem in enumerate(noshow_list):
        elapsed= (datetime.now() - noshow_timer[idx])
        print ("%d : time elapsed: %d:%02d | %s " %(idx, (elapsed.seconds)//60,
            (elapsed.seconds)%60, elem[NAME]))

def move_to_noshow(state, noshow_list, noshow_timer, idx, text_count):
    try:
        idx = int(idx)
        to_add = state.pop(idx)
        text_count.pop(idx)
        noshow_list.append(to_add)
        noshow_timer.append(datetime.now())
    except:
        print ("Invalid Index")
    return state, noshow_list, noshow_timer, text_count

def noshow_readd(state, noshow_list, noshow_timer, idx, text_count):
    try:
        idx = int(idx)
        to_add = noshow_list.pop(idx)
        noshow_timer.pop(idx)
        state.append(to_add)
        text_count.append(0)
    except:
        print ("Invalid Index")
    return state, noshow_list, noshow_timer, text_count

def noshow_refresh (noshow_list, noshow_timer):
    to_delete = []
    for idx, elem in enumerate(noshow_list):
        elapsed = (datetime.now() - noshow_timer[idx])
        if elapsed.seconds >= NOSHOW_TIME_LIM:
            to_delete.append(idx)

    to_delete.reverse()
    for idx in to_delete:
        noshow_list.pop(idx)
        noshow_timer.pop(idx)
    return noshow_list, noshow_timer

def noshow_delete(noshow_list, noshow_timer, idx):
    try:
        idx = int(idx)
        noshow_list.pop(idx)
        noshow_timer.pop(idx)
    except:
        print ("Invalid Index")

    return noshow_list, noshow_timer

def text_number(account_sid, auth_token, twilio_number, state, idx, text_count):
    try:
        idx = int(idx)
        print ("Texting %s" %(state[idx][NAME]))
        print (state[idx][PHONE])
        phone_num = str("+1" + (state[idx][PHONE]))
        text_count[idx]+=1
        message = "Hello " + state[idx][NAME] + "! Please get in line."
        client = Client(account_sid, auth_token)
        client.api.account.messages.create(
            to= phone_num,
            from_=twilio_number,
            body=message)
    except:
        print ("Invalid Index or text didn't go through?")
    return state, text_count

# Text everyone on the List
def text_all(account_sid, auth_token, twilio_number, state, text_count):
    for i in range(len(state)):
        state, text_count = text_number(account_sid, auth_token,
                            twilio_number, state, i, text_count)
    return state, text_count

# allowing for manual entry of a person into the current queue
def manual_entry(state, text_count):
    entry_time = str(datetime.now())
    full_name = raw_input("Enter Full Name: ")
    id_num = raw_input("Enter ID: ")
    phone_num = raw_input("Enter Phone Number: ")
    email = raw_input("Enter Email: ")
    new_entry = [entry_time, full_name, id_num, phone_num, email]
    state.append(new_entry)
    text_count.append(0)
    return state, text_count

def load_config():
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_NUMBER')

    if not all([spreadsheet_id, twilio_account_sid, twilio_auth_token,
        twilio_number]):
        print ("Whoops! Please set environment variables")
        sys.exit()

    return (spreadsheet_id, twilio_number, twilio_account_sid,
        twilio_auth_token)

def main():
    spreadsheet_id, twilio_number, account_sid, auth_token = load_config()
    values = get_values(spreadsheet_id)

    # initializations
    state = []
    noshow_list = []
    noshow_timer = []
    text_count = []

    start_idx = 0
    end_idx = 0
    # check to see if file is present
    try:
        idx_file = open(INDEX_FILE_NAME, 'r')
        start_idx = int(idx_file.readline())
        end_idx = start_idx
        idx_file.close()
    except:
        idx_file = open(INDEX_FILE_NAME, 'w')
        idx_file.close()

    # first population of state, populate to capacity
    count = 0
    for idx, row in enumerate(values):
        if count >= (NUM_SERVING+NUM_WAITING):
            break
        if idx < start_idx:
            pass
        else:
            if row:
                state.append(row)
                text_count.append(0)
                count+=1
            else:
                pass
            end_idx+=1

    print(start_idx)
    print(end_idx)

    command = raw_input("--> ")
    split_command = command.split()
    while command != "quit":
        if not split_command or not command:
            pass
        elif command == "current":
            pass
        elif split_command[0] == "get" and split_command[1] == "next":
            if len(split_command) == 2:
                state, end_idx, text_count = get_next(spreadsheet_id, state, end_idx, text_count)
            elif len(split_command) ==3:
                try:
                    state, end_idx, text_count = get_next_batch(spreadsheet_id, state, end_idx,
                     text_count, int(split_command[2]))
                except:
                    print ("Please include an index.")
            else:
                print ("Incorrect format.")
        elif split_command[0] == "done":
            try:
                state, text_count = done(state, split_command[1], text_count, split_command[2])
            except:
                print ("Please include an index.")
        elif split_command[0] == "noshow":
            if len(split_command) == 1:
                # implement show noshow line here
                print_noshow(noshow_list, noshow_timer)
            else:
                # implement noshow refresh
                if split_command[1] == "refresh":
                    noshow_list, noshow_timer = noshow_refresh(noshow_list,
                        noshow_timer)
                elif split_command[1] == "readd":
                    state, noshow_list, noshow_timer, text_count = \
                        noshow_readd(state, noshow_list, noshow_timer,
                            split_command[2], text_count)
                elif split_command[1] == "delete":
                    noshow_list, noshow_timer = noshow_delete(noshow_list,
                        noshow_timer, split_command[2])
                else:
                    # implements noshow INDEX
                    state, noshow_list, noshow_timer, text_count = \
                        move_to_noshow(state, noshow_list, noshow_timer,
                            split_command[1], text_count)
        elif split_command[0] == "text":
            if len(split_command) < 2:
                print ("Please use text[index number|all]")
            elif split_command[1] == "all":
                state, text_count = text_all(account_sid, auth_token,
                    twilio_number, state, text_count)
            else:
                state, text_count = text_number(account_sid, auth_token,
                    twilio_number, state, split_command[1], text_count)
        elif command == "manual entry":
            state, text_count = manual_entry(state, text_count)
        elif split_command[0] == "delete":
            try:
                state, text_count = delete(state, split_command[1], text_count)
            except:
                print ("Please include an index.")
        else:
            print ("Command not supported.")

        print_state(state, text_count)
        command = raw_input("--> ")
        split_command = command.split()

    idx_file = open(INDEX_FILE_NAME, 'w')
    idx_file.write(str(end_idx))
    idx_file.close()

if __name__ == '__main__':
    main()
