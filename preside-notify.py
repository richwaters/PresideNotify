#!/usr/bin/python3

# This script uses the concepts from this blog entry.
# https://blog.timstoop.nl/posts/2009/03/11/python-imap-idle-with-imaplib2.html


import imaplib2
import imaplib
import time, requests, email, urllib, datetime
from email.parser import HeaderParser
from threading import *
import json5
import sys
import getopt
import os
from email.header import Header, decode_header, make_header


Verbosity = 0
USAGE = 'preside-notify.py [--help] [--verbose] --config=<file name>'


# This is the threading object that does all the waiting on 
# the event
class Idler(object):
    def __init__(self, conn, monitoredFolder, highestUid):
        self.thread = Thread(target=self.idle)
        self.imapConnection = conn
        self.event = Event()
        self.highestUid = highestUid
        self.monitoredFolder = monitoredFolder
 
    def start(self):
        self.thread.start()
 
    def stop(self):
        self.event.set()
 
    def join(self):
        self.thread.join()

 
    def idle(self):
        # Starting an unending loop here
        while True:
            if self.event.isSet():
                return

            self.needsync = False
            self.needIdle = False
            
            def callback(args):
                logInfo( 'IDLE Callback' )

                if not self.event.isSet():
                    idleResponse = self.imapConnection.response( 'IDLE' )
                    logInfo( str(idleResponse) )
        
                    if idleResponse[1][0] == 'TIMEOUT':
                        self.needIdle = True
                    else:
                        self.needsync = True
                    self.event.set()


            try:
                logInfo( 'Sending IDLE for ' + self.monitoredFolder["accountName"] )
            
                self.imapConnection.idle(callback=callback, timeout=self.monitoredFolder['idleTimeout'] * 60 )

                self.event.wait()

                logInfo( 'IDLE Completed' )

                if self.needIdle:
                    self.event.clear()
                    continue
            
                if self.needsync:
                    self.event.clear()
                    self.doSync()
                    
            except Exception as e:
                logException( e )
                time.sleep(4)

                
    def parseHeadersResponse( self, headersResponse ):
        headersStr = headersResponse.decode('utf-8')
        parser = HeaderParser()
        headersDict = parser.parsestr(headersStr)
        decodedHeadersDict = {}
        for k, v in headersDict.items():
            decodedHeadersDict[k.lower()] = str( make_header(decode_header(v)) )

        return( decodedHeadersDict )

    def stringFromDictForKey(self, dict, key ):
        if key in dict:
            return dict[key]
        return ''

                
    def doSync(self):
        logInfo( 'Syncing new messages' )
        #uidStr = self.highestUid.decode( 'utf-8' )
        uidStr = self.highestUid + 1
        uidSearchStr = '(UNSEEN UID %s:*)' % (uidStr)
            
        logImap( self.monitoredFolder,  'Sending -- ' + uidSearchStr )
        (retcode, uids) = self.imapConnection.uid('search' , None, uidSearchStr )
        logImap( self.monitoredFolder, 'Received --  Type: ' + str( retcode ) + ' UIDS: ' + str (uids) )

        #print uids
        if retcode != 'OK':
            logInfo( 'Search for unseen messages failed' )
            return
        
        for uid in uids[0].split():
            uidStr = uid.decode( 'utf-8' )
            uidInt = int( uidStr )
            if uidInt <= self.highestUid:
                logInfo( 'SKIPPING UID: ' + uidStr )
                continue
            if self.highestUid == None or uidInt > self.highestUid:
                self.highestUid = uidInt

            peekStr = '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID SUBJECT FROM)])'
            logImap( self.monitoredFolder, 'Sending -- ' + peekStr )

            typ, fetchResp = self.imapConnection.uid('fetch', uid ,peekStr )
            logImap( self.monitoredFolder, 'Received -- Type: ' + str( typ ) + ' Headers: ' + str (fetchResp) )

            if typ != 'OK':
                logInfo( "Bad response to fetch UID" )
                continue

            if len( fetchResp ) == 0:
                logInfo( "Empty response to fetch UID" )
                continue

            headersIndex = 0
            isSeen = False
            resp = fetchResp[headersIndex]
            while type( resp ) != tuple and headersIndex < len( fetchResp ):
                headersIndex += 1
                flags = imaplib.ParseFlags( resp )
                if b'\\Seen' in flags:
                    isSeen = True
                resp = fetchResp[headersIndex]

            if headersIndex == len( fetchResp ) :
                logInfo( 'Cannot get email headers' )
                continue

            parsedHeaders = self.parseHeadersResponse( fetchResp[headersIndex][1] )
            subject = self.stringFromDictForKey( parsedHeaders, 'subject' )
            sender = self.stringFromDictForKey( parsedHeaders, 'from' )
            messageId = self.stringFromDictForKey( parsedHeaders, 'message-id' )

            if isSeen:
                logInfo( 'Skipping seen email: ' + subject )
                continue
            

            alertMsg = 'PresideNotify.py - From: %s\nSubject: %s' % (sender,subject)

            qDict = {
                'alertMsg' : alertMsg,
                'ghAccountName' : self.monitoredFolder['accountName'],
                'ghFolderPath' : self.monitoredFolder['folder'],
                'messageId' : messageId,
                'ghContentReady' : 1
                }

            qStr = urllib.parse.urlencode( qDict )
                              
            req = 'https://users.preside.io/preside/GHSendPushMsg?' + qStr
            
            logInfo( 'Sent notification: ' + req )
            
            r = requests.get(req, auth=(self.monitoredFolder['presideIoUser'], self.monitoredFolder['presideIoPassword']));
            logInfo( 'Notification response: ' + str(r.headers) )



def spawnIdler( monitoredFolder ):
    idler = None
    M = None
    
    #logInfo( 'Connecting to Account:%s, Folder: %s ' % (monitoredFolder['accountName'], monitoredFolder['folder'] ) )

    try:
        M = imaplib2.IMAP4_SSL( monitoredFolder['server'] ) ;
    except Exception as e:
        logInfo( "Error connecting to Account: %s" % (monitoredFolder['accountName']) )
        logException( e )
        raise

    try:
        M.login(monitoredFolder['user'], monitoredFolder['password'] )
    except Exception as e:
        logInfo( "Error logging into Account: %s" % (monitoredFolder['accountName']) )
        logException( e )
        try:
            M.close()
        except:
            pass
        raise e
    
    try:
        highestUid = 0

        logImap( monitoredFolder, 'Sending --  SELECT ' + monitoredFolder['folder'] )
        selectResponse = M.select( monitoredFolder['folder'] )
        logImap( monitoredFolder, 'Received --  ' + str( selectResponse ) )

        (typ, resp) = selectResponse
        if typ != "OK":
            logInfo( "Bad select" )
            raise
             

        highestSeq = resp[0]
        if highestSeq != b'0':
            uidResponse = M.fetch( highestSeq, "UID" )
            highestUid = int( uidResponse[1][0].split()[-1][:-1].decode( 'utf-8' ) )

        # Start the Idler thread
        idler = Idler(M, monitoredFolder, highestUid)
        idler.start()
        #time.sleep(29*60)
        time.sleep(8*60*60)

    except Exception as e:
        logInfo( 'Error setting up IDLE for Account:%s, Folder: %s ' % (monitoredFolder['accountName'], monitoredFolder['folder'] ) )
        logException( e )
        raise

    finally:
        try:
            if idler != None:
                idler.stop()
                idler.join()

            if M != None:    
                M.close()
                M.logout()
                
            logInfo( 'Logged out' )
        except:
             pass


def logException( e ):
    print ( str(datetime.datetime.now()) + ': ' + str(e) )
    print(sys.exc_info()[0])
  
def logInfo( msg ):
    if Verbosity > 0:
        print ( str(datetime.datetime.now()) + ': ' + msg)
       
def logImap( monitoredFolder, msg ):
    if Verbosity > 1:
        logInfo( '[IMAP-%s] %s' %(monitoredFolder['accountName'], msg ) )

def maintainIdle( monitoredFolder ):
    while True:
        logInfo( 'Running Idle for Account ' + monitoredFolder['accountName'] + ' and Folder: ' + monitoredFolder['folder'] )
        spawnIdler( monitoredFolder ) 


def runThreads(monitoredFolders):
    for monitoredFolder in monitoredFolders:
        t = Thread( target=maintainIdle, args=(monitoredFolder, ) )
        t.start()


# This doesn't work for some reason so just loop and sleep for a day at a time
# sleep forever
#time.sleep( sys.maxsize )
#
    while True:
        time.sleep( 86400 )



def readJson(filename):
    with open(filename) as f_in:
        return(json5.load(f_in))
                

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

    runThreads( monitoredFolders )
        


if __name__ == '__main__':
    main(sys.argv[1:])
