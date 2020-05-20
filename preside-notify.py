#!/usr/bin/python3

# This script uses the concepts from this blog entry.
# https://blog.timstoop.nl/posts/2009/03/11/python-imap-idle-with-imaplib2.html


import imaplib2
import imaplib
import time 
import requests 
import email
import urllib 
import datetime
from email.parser import HeaderParser
from threading import *
import json5
import sys
import getopt
import os
from email.header import Header, decode_header, make_header
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

Verbosity = 0
USAGE = 'preside-notify.py [--help] [--verbose] --config=<file name>'


# This is the threading object that does all the waiting on 
# the event
class Idler(object):
    def __init__(self, conn, monitoredFolder, highestUid):
        self.imapConnection = conn
        self.event = Event()
        self.highestUid = highestUid
        self.monitoredFolder = monitoredFolder
 
    def idle(self):
        monitoredFolder = self.monitoredFolder
        
        # Starting an unending loop here
        while True:
            if self.event.isSet():
                return

            self.needsync = False
            self.needIdle = False
            self.needAbort = False
            
            def callback(args):
                (response, userArg, aborted) = args
                logInfo( monitoredFolder,  'IDLE Callback ' + str( response) )
                if aborted:
                    logInfo(monitoredFolder, "IDLE aborted (probably lost connection)" )
                    self.needAbort = True
                    self.event.set()
                    return
                    

                if not self.event.isSet():
                    idleResponse = self.imapConnection.response( 'IDLE' )
                    logInfo(monitoredFolder,  'IDLE response ' + str(idleResponse) )
        
                    if idleResponse[1][0] == 'TIMEOUT':
                        self.needIdle = True
                    else:
                        self.needsync = True
                    self.event.set()
                else:
                    #idleResponse = self.imapConnection.response( 'IDLE' )
                    logInfo(monitoredFolder,  "Response received with event already set " ) 


            try:
                timeout = self.monitoredFolder['idleTimeout'] * 60
                logInfo( monitoredFolder, 'Sending IDLE with timeout ' + str( timeout ) )
            
                self.imapConnection.idle(callback=callback, timeout=timeout)
                self.event.wait()

                logInfo( monitoredFolder, 'IDLE Completed' )

                if self.needAbort:
                    self.event.clear()
                    return

                if self.needIdle:
                    self.event.clear()
                    continue
            
                if self.needsync:
                    self.event.clear()
                    self.doSync()
                    
            except Exception as e:
                logException( e )
                time.sleep(4)
                return
                #raise


                
    def doSync(self):
        self.highestUid = syncMonitoredFolder( self.monitoredFolder , self.imapConnection, self.highestUid )



#########################

def stringFromDictForKey(dict, key ):
    if key in dict:
        return dict[key]
    return ''

def boolFromDictForKey(dict, key ):
    if key in dict:
        return dict[key]
    return False

                
def parseHeadersResponse( headersResponse ):
    headersStr = headersResponse.decode('utf-8')
    parser = HeaderParser()
    headersDict = parser.parsestr(headersStr)
    decodedHeadersDict = {}
    for k, v in headersDict.items():
        decodedHeadersDict[k.lower()] = str( make_header(decode_header(v)) )

    return( decodedHeadersDict )


def syncMonitoredFolder( monitoredFolder, imapConnection, highestUid ):
    logInfo( monitoredFolder, 'Syncing new messages' )
    #uidStr = self.highestUid.decode( 'utf-8' )
    uidStr = highestUid + 1
    uidSearchStr = '(UNSEEN UID %s:*)' % (uidStr)
            
    logImap( monitoredFolder,  'Sending -- ' + uidSearchStr )
    (retcode, uids) = imapConnection.uid('search' , None, uidSearchStr )
    logImap( monitoredFolder, 'Received --  Type: ' + str( retcode ) + ' UIDS: ' + str (uids) )

    #print uids
    if retcode != 'OK':
        logInfo( monitoredFolder, 'Search for unseen messages failed' )
        return highestUid
    
    for uid in uids[0].split():
        uidStr = uid.decode( 'utf-8' )
        uidInt = int( uidStr )
        if uidInt <= highestUid:
            logInfo( monitoredFolder, 'SKIPPING UID: ' + uidStr )
            continue

        if highestUid == None or uidInt > highestUid:
            highestUid = uidInt

        peekStr = '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID SUBJECT FROM)])'
        logImap( monitoredFolder, 'Sending -- ' + peekStr )

        typ, fetchResp = imapConnection.uid('fetch', uid ,peekStr )
        logImap( monitoredFolder, 'Received -- Type: ' + str( typ ) + ' Headers: ' + str (fetchResp) )

        if typ != 'OK':
            logInfo( monitoredFolder, "Bad response to fetch UID" )
            continue

        if len( fetchResp ) == 0:
            logInfo( monitoredFolder, "Empty response to fetch UID" )
            continue

        headersIndex = 0
        #isSeen = False
        resp = fetchResp[headersIndex]
        while type( resp ) != tuple and headersIndex < len( fetchResp ):
            headersIndex += 1

            #This isn't right. These FLAGS that are being received are  coming through from the SELECT commands and aren't related to the BODY.PEEK or the uid being requested. I'm still not certain why they're arriving here, but they should just be ignored.
            #flags = imaplib.ParseFlags( resp )
            #if b'\\Seen' in flags:
            #    isSeen = True
            resp = fetchResp[headersIndex]

        if headersIndex == len( fetchResp ) :
            logInfo( monitoredFolder, 'Cannot get email headers' )
            continue

        parsedHeaders = parseHeadersResponse( fetchResp[headersIndex][1] )
        subject = stringFromDictForKey( parsedHeaders, 'subject' )
        sender = stringFromDictForKey( parsedHeaders, 'from' )
        messageId = stringFromDictForKey( parsedHeaders, 'message-id' )
        
        enableEmailActions = boolFromDictForKey( monitoredFolder, 'enableEmailActions' )
        disableAlerts =  boolFromDictForKey( monitoredFolder, 'disableAlertMessage' )
        soundName =  stringFromDictForKey( monitoredFolder, 'alertSound' )

        #if isSeen:
        #    logInfo( monitoredFolder, 'Skipping seen email: ' + subject )
        #    continue


        qDict = {
            'ghAccountName' : monitoredFolder['accountName'],
            'ghFolderPath' : monitoredFolder['folder'],
            'messageId' : messageId,
            'ghContentReady' : 1,
            'ghEnableEmailActions' : enableEmailActions
            }

        if not disableAlerts:
            alertPfx = stringFromDictForKey( monitoredFolder, 'alertPrefix' )
            alertMsg = '%sFrom: %s\nSubject: %s' % (alertPfx,sender,subject)
            qDict['alertMsg'] = alertMsg

        if len(soundName):
            qDict['alertSound'] = soundName

        qStr = urllib.parse.urlencode( qDict )

        req = 'https://users.preside.io/preside/GHSendPushMsg?' + qStr

        logInfo( monitoredFolder, 'Sent notification: ' + req )

        r = requests.get(req, auth=( monitoredFolder['presideIoUser'], monitoredFolder['presideIoPassword']));
        logInfo( monitoredFolder, 'Notification response: ' + str(r.headers) )

    return highestUid


def connectAndIdle( monitoredFolder,highestUid):
    idler = None
    M = None
    
    #logInfo( monitoredFolder, 'Connecting' )
    imaplib2DebugLevel = max( Verbosity - 2, 0 )
    try:
        M = imaplib2.IMAP4_SSL( host=monitoredFolder['server'], debug=imaplib2DebugLevel ) ;
    except Exception as e:
        logInfo( monitoredFolder, "ERROR connecting" )
        logException( e )
        return highestUid

    try:
        M.login(monitoredFolder['user'], monitoredFolder['password'] )
    except Exception as e:
        logInfo( monitoredFolder, "ERROR logging in" )
        logException( e )
        try:
            M.close()
        except:
            pass
        return highestUid
    
    try:

        logImap( monitoredFolder, 'Sending --  SELECT ' + monitoredFolder['folder'] )
        selectResponse = M.select( monitoredFolder['folder'] )
        logImap( monitoredFolder, 'Received --  ' + str( selectResponse ) )

        (typ, resp) = selectResponse
        if typ != "OK":
            logInfo(monitoredFolder,  "Bad select" )
            return highestUid
             

        if highestUid == 0:
            highestSeq = resp[0]
            if highestSeq != b'0':
                uidResponse = M.fetch( highestSeq, "UID" )
                highestUid = int( uidResponse[1][0].split()[-1][:-1].decode( 'utf-8' ) )

        with ThreadPoolExecutor(max_workers=1) as executor:
            highestUid = syncMonitoredFolder( monitoredFolder, M, highestUid )
            idler = Idler(M, monitoredFolder, highestUid)
            executor.submit( idler.idle() )
            highestUid = idler.highestUid

        logInfo( monitoredFolder, "IDLE Done" )
        return highestUid
        
    except Exception as e:
        logInfo( monitoredFolder, 'ERROR setting up IDLE' )
        logException( e )
        return highestUid

    finally:
        try:
            if idler != None:
                idler.stop()
                idler.join()

            if M != None:    
                M.close()
                M.logout()
                
            logInfo( monitoredFolder, 'Logged out' )
        except:
             pass


def logException( e ):
    print ( str(datetime.datetime.now()) + ': ' + str(e) )
    print(sys.exc_info()[0])

def logMessage( monitoredFolder, msg ):
    accountName = monitoredFolder.get( 'accountName', '[Unknown]' )
    folderName = monitoredFolder.get( 'folder' , '[Unknown]' )
    accountAndFolder =  'Account ' + accountName + ', Folder: ' + folderName
    print ( '[%s] %s: %s' % ( accountAndFolder,  str(datetime.datetime.now()) , msg) )
    
def logInfo( monitoredFolder, msg ):
    if Verbosity > 0:
        logMessage( monitoredFolder, msg )
       
def logImap( monitoredFolder, msg ):
    if Verbosity > 1:
        logInfo( monitoredFolder, '[IMAP] %s' % (msg) )

def maintainIdle( monitoredFolder ):
    accountAndFolder =  'Account ' + monitoredFolder['accountName'] + ', Folder: ' + monitoredFolder['folder']
    sleepTime = 8
    highestUid = 0
    idleTimeoutSeconds = (monitoredFolder['idleTimeout'] * 60)
    while True:
        logInfo( monitoredFolder, 'Running Idle' )
        try:
            idleStartTime = time.time()
            highestUid = connectAndIdle( monitoredFolder, highestUid )
            idleEndTime = time.time()

            idledSeconds = (idleEndTime-idleStartTime)
            if idledSeconds < 60:
                sleepTime = min( sleepTime * 2, 300, idleTimeoutSeconds )
            elif idledSeconds > idleTimeoutSeconds:
                sleepTime = 8

        except Exception as e:
            #shouldn't ever get here, in theory
            logException( e )
            sleepTime = min( sleepTime * 2, 300, idleTimeoutSeconds )

        #connectAndIdle should never exit. If we're here, there's been and error. Sleep for a bit
        logInfo (monitoredFolder, 'Waiting %s secs before trying again' % (str(sleepTime)) )
        time.sleep(sleepTime)

            

def runThreads(monitoredFolders):
    with ThreadPoolExecutor( max_workers = len(monitoredFolders) ) as executor:
        for monitoredFolder in monitoredFolders:
            executor.submit( maintainIdle, monitoredFolder )                               

def readJson(filename):
    try:
        with open(filename) as f_in:
            return(json5.load(f_in))

    except Exception as e:
        print( "\n***** ERROR loading config file. Check for missing commas and other syntax errors.\n" )
        #shouldn't ever get here, in theory
        logException( e )
        sys.exit(1)


def validateMonitoredFolders( monitoredFolders ):
    hasError = False
    requiredKeys = ['user', 'password', 'server', 'folder', 'accountName', 'presideIoUser', 'presideIoPassword', 'idleTimeout'  ]
    for monitoredFolder in monitoredFolders:
        #logInfo( monitoredFolder, 'Validating configuration' )
        for k in requiredKeys:
            if  k not in monitoredFolder:
                logMessage( monitoredFolder, 'Missing configuration key: ' + k )
                hasError = True
                        
    if hasError:
        sys.exit(1)

    
def main(argv):
    global Verbosity
    configFile = ''
    
    try: 
        opts, args = getopt.getopt(argv, "h", ["help","verbose","config="])
    except getopt.GetoptError:
        print( USAGE )
        sys.exit(2)

    Verbosity = 0
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print( USAGE )
            sys.exit(0)
          
        elif opt in ("--verbose"):
            Verbosity += 1
          
        elif opt in ("--config"):
            configFile = arg
          
    if configFile == '':
        print( USAGE )
        sys.exit(1)
            
    if os.path.exists( configFile ) == False:
       print( 'Config file not found: ' + configFile  )
       sys.exit(1)

    cfgJson = readJson( configFile )
    monitoredFolders = cfgJson[ 'MonitoredFolders' ]
    if len( monitoredFolders ) == 0:
      print( 'No folders to monitor speficied on config file')
      sys.exit(1)

    validateMonitoredFolders( monitoredFolders )
    runThreads( monitoredFolders )
        


if __name__ == '__main__':
    main(sys.argv[1:])
