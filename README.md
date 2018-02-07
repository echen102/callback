# fn(callback)

This is a basic callback system. The finished product integrates with google spreadsheets and twillio to allow users to sign up and receive a text when the service is ready for them. 

## Requirements
* Twillio API (not yet integrated)
* Google sheets API
* Python 2.7 + 

## Functions implemented

## Functions to be implemented (please don't mind the notes)
-[] user can either print out current state : current
-[] user can send text to anyone in the queue : text INDEX
-[] user can set in progress to done : done INDEX

    increment sheet index

    if total number in progress + in line > max line

        don't do anything

    else

        query next value in sheet (sheet index + in progress + in line + 1) 

        add to queue
-[] user can see no show queue: noshow
-[] user can set anyone in progress to no show: noshow INDEX

    moves no show information into a global map (not persistent)

        map[data] = timer (timer value adjustable by global variable)

-[] user can move anyone in the noshow queue to the queue: readd INDEX

    appends noshow to end of queue (can exceed num in progress + num in line)

    removes noshow from noshow map
-[] user can refresh no show queue: noshow refresh 

    removes all entries in map with timers that have zeroed out

## Usage

Will be filled out as this is built. 