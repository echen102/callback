
from __future__ import print_function
import httplib2
import os

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

NUM_IN_PROGRESS = 2
NUM_IN_LINE = 3
INDEX_FILE_NAME = 'idx_file.dat'

# assume sheet index starts at 2 due to column labels
SHEET_IDX_START = 2

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

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1i119SHQA2Om0ykgpIoP8V4GQOMZf-IrVAotu9yV4m3k'
    rangeName = 'A2:E'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    # assume that the sheet starts at A2 due to column labels
    sheet_idx = SHEET_IDX_START

    # check to see if file is present
    try: 
        idx_file = open(INDEX_FILE_NAME, 'r')
        sheet_idx = int(idx_file.readline())
        idx_file.close()
    except: 
        idx_file = open(INDEX_FILE_NAME, 'w')
        idx_file.close()

    if not values:
        print('No data found.')
    else:
        for row in values:
            if row: 
                print(row)
            else: 
                pass

    idx_file = open(INDEX_FILE_NAME, 'w')
    idx_file.write(str(sheet_idx))
    idx_file.close()


if __name__ == '__main__':
    main()

