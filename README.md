# fn(callback)

## Table of Contents

## What are we, and why do we exist?

Callback was based off of the commonly used sign-up and we'll text you when we're ready for you that is commonly utilized within the restaurant industry today, as a way to shift from physical lines to virtual lines. This allows the customer to hold a place in line, while having the freedom of not actually having to physically stay in line and deal with the potential problems that might result. 

While this system has already been established, and many programs have been written to service this, to be quite honest, we didn't really want to pay the premiums we needed to in order to use some of the more well developed software that's already on the market. When we decided we needed some sort of call back system, we knew we wouldn't need the system often enough to warrant purchasing a full blown infrastructure. We also didn't want to spend money hosting a server to store all of our data. So we decided to build this system ourselves, implement the functions that we needed and some that we just wanted to have. 

Since Google Forms can easily allow different computers to collect data at one time from a single form, and the results of a form can be funneled into a spreadsheet AND all your data is hosted on Google's servers, we thought this was the perfect platform to use. The only money you'll need to spend is on Twilio. For all you who don't want to pay much for this kind of system, instead of needing to create your own, we've done the work for you.

## Requirements
* Twilio API
* Google sheets API
* Python 3

## Functionality
- [x] user can get next customer
- [x] user can either print out current state : current
- [x] user can send text to anyone in the queue : text INDEX
- [x] user can set in progress to done : done INDEX
- [x] user can see no show queue: noshow
- [x] user can set anyone to no show: noshow INDEX
- [x] user can move anyone in the noshow queue to the queue: noshow readd INDEX
- [x] user can refresh no show queue: noshow refresh 
- [x] Add a number of times texted counter next to each name
- [ ] develop local user interface

## Usage Overview

Source the environment variables first (you'll need to fill this out with your corresponding information)

```shell
    source env.sh

```

Then run the callback file to start the program 
```shell
    python callback.py
```

You'll have two main "lines":
    * current line
        * The current state keeps track of who is being served and who is physically waiting in line.
    * no show line
        * This list keeps track of those who don't show up in time, and we're ready to service them. We can move individuals to the no show line to give them a buffer of a user specified time (the user is you), and can re-add them to the end of the current state if they do show up. 
        * We allow the user to also clear out all the no shows who have exceeded the specified buffer time. So if you want to boot them all out, you can. 

The program will first populate the current line with N number of people, where N is the number of people you want to serve at once and the number of people you want physically waiting in line (but still governed by their order in the virtual line). If there aren't N people, the program populates however many there are. 

The program will then prompt for user input until you give the command "quit", in which case it will exit out of the program. 

One feature we have added is a persistent index of how far down the spreadsheet we've already gone. This is useful for if the program is exited, but upon restart needs to service those who have not been serviced at all. We store the furthest index in the spreadsheet that you have reached, and use that as the starting point the next time the program relaunches. Delete the idx_file.dat file that is produced if you want to start from the very beginning of the spreadsheet. 

```shell
    rm idx_file.dat
```

Please refer to the Commands section (below) for all commands that this program takes in. 

## Commands 

Note: INDEX must be replaced by a numerical number - the index of the individual in question(as will be displayed next to the names). 

| Command  | Description |
| ------------- | ------------- |
| current  | Displays the current line state, including who is currently being served, who is waiting, and how many times you've texted each individual in line. Note that this text count resets when an individual is removed from the list.  |
| get next | Gets the next entry, and adds this person to the current line.  |
| text INDEX | Sends pre-formatted text message to the individual's phone.|
| done INDEX | Removes the person at INDEX, and moves the next person in line as being serviced|
| noshow | Displays the current no show line, and includes a time elapsed from when that individual was first moved to the noshow line|
|noshow refresh | Refreshes the list, and removes all individuals whose elapsed times have exceeded the user set limit. |
| noshow readd INDEX | Re adds the individual at INDEX in the noshow line to the current line. Removes this individual from the no show line. |
| noshow INDEX | Moves the individual at INDEX in the current line to the noshow line. Stores the time at which this individual was moved to the noshow line.|
| quit | Exit the program, and save the furthest index to file|
## Assumptions
We've made a couple of assumptions about the formatting of the Google Form, and some of its data. 

We assume that the order of information, from left to right is: 
    0. Time stamp
    1. Name
    2. ID
    3. Phone
    4. Email

The ordering of these columns can be changed easily. Refer to the parameters section for details. 

We assume that the phone number is given in a ###-###-#### format without the dashes, as we append +1 to the front in order to comply with the E.164 phone number format as needed by the Twilio API. Google forms allows pattern matching, so we would suggest you constrain your customers to inputting phone numbers in the format we assume the numbers to be in. Or you can add a parsing piece into the code that will transform whatever format phone number you accept into the E.164 format. 

## Parameters and Where to Find Them
Note: We index from 0

| Parameters  | Description |
| ------------- | ------------- |
| NAME  | Index of the name column in the spreadsheet  |
| ID | Index of the ID column in the spreadsheet |
| PHONE | Index of the phone column in the spreadsheet |
| EMAIL | Index of the email column in the spreadsheet |
| NUM_SERVING | Maximum number of people we will be concurrently serving|
| NUM_WAITING | Maximum number of people who will be waiting in line. However, we always allow the user to add no shows back into the current line, regardless of the NUM_WAITING capacity|
| NOSHOW_TIME_LIM | Total number of seconds we set the buffer time for no shows to show up. Any no shows who have not shown up by this time limit are removed from the no show line ONLY when noshow refresh is called. This is NOT automatic. |
