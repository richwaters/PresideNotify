

#https://blog.timstoop.nl/posts/2009/03/11/python-imap-idle-with-imaplib2.html


import imaplib2, time, requests, email, urllib, datetime
from email.parser import HeaderParser
from threading import *
import thread
import json

MonitoredFolders = [
    {
        'user': "",                # Your IMAP user id
        'password' : "",           # Your IMAP password
        'server' : "",             # Your IMAP SERVER
        'folder' : "INBOX",
        'accountName' : "",        # Should match name of account in Preside app
        'presideIoUser' : "",      # Your Preside.io user name (email address)
        'presideIoPassword' : "",  # Your Preside.io password
        'idleTimeout' : 29 * 60
    },
    
    # Another account or folder to monitor - Remove this entry if you only have 1 account
    {
        'user': "",                # Your IMAP user id
        'password' : "",           # Your IMAP password
        'server' : "",             # Your IMAP SERVER
        'folder' : "",
        'accountName' : "",        # Should match name of account in Preside app
        'presideIoUser' : "",      # Your Preside.io user name (email address)
        'presideIoPassword' : "",  # Your Preside.io password
        'idleTimeout' : 29 * 60
    },

]

 
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


            logInfo( 'Sending IDLE' )
            
            self.imapConnection.idle(callback=callback, timeout=self.monitoredFolder['idleTimeout'] )

            self.event.wait()

            logInfo( 'IDLE Completed' )

            if self.needIdle:
                self.event.clear()
                continue
            
            if self.needsync:
                self.event.clear()
                self.doSync()

                
    def doSync(self):
        logInfo( 'Syncing new messages' )
        uidSearchStr = '(UNSEEN UID %s:*)' % (self.highestUid)
        (retcode, uids) = self.imapConnection.uid('search' , None, uidSearchStr )
        #print uids
        if retcode == 'OK':
            for uid in uids[0].split():
                if uid <= self.highestUid:
                    #print 'SKIPPING ' + uid
                    continue
                
                typ, headersData = self.imapConnection.uid('fetch', uid , '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID SUBJECT FROM)])')
                headers=headersData[0][1]
                parser = HeaderParser()
                h = parser.parsestr(headers)

                subject = h['Subject']
                sender = h['From']
                alertMsg = 'PresideNotify.py - From: %s\nSubject: %s' % (sender,subject)
                messageId = h['Message-ID']


                qDict = { 'alertMsg' : alertMsg, 'ghAccountName' : self.monitoredFolder['accountName'], 'ghFolderPath' : self.monitoredFolder['folder'],  'messageId' : messageId, 'ghContentReady' : 1 }

                qStr = urllib.urlencode( qDict )
                              

                req = 'https://users.preside.io/preside/GHSendPushMsg?' + qStr
                
                logInfo( 'Sent notification: ' + req )

                r = requests.get(req, auth=(self.monitoredFolder['presideIoUser'], self.monitoredFolder['presideIoPassword']));
                logInfo( 'Notification response: ' + str(r.headers) )


def doIdle( monitoredFolder ): 
    try:
        M = imaplib2.IMAP4_SSL( monitoredFolder['server'] ) ; 
        M.login(monitoredFolder['user'], monitoredFolder['password'] )
        
        selectResponse = M.select( monitoredFolder['folder'] )
        highestSeq = selectResponse[1][0]
        uidResponse = M.fetch( highestSeq, "UID" )
        highestUid = uidResponse[1][0].split()[-1][:-1]

        # Start the Idler thread
        idler = Idler(M, monitoredFolder, highestUid)
        idler.start()
        #time.sleep(29*60)
        time.sleep(8*60*60)

    except e:
        print str(e)
        raise

    finally:
       idler.stop()
       idler.join()
       M.close()
       M.logout()
       logInfo( 'Logged out' )

       
def logInfo( msg ):
    pass
    #uncomment for debugging
    #print str(datetime.datetime.now()) + ': ' + msg


def maintainIdle( monitoredFolder ):
    while True:
        logInfo( 'Running Idle for Account ' + monitoredFolder['accountName'] + ' and Folder: ' + monitoredFolder['folder'] )
        doIdle( monitoredFolder ) 


for monitoredFolder in MonitoredFolders:
     thread.start_new_thread( maintainIdle, (monitoredFolder, ) )


# This doesn't work for some reason so just loop and sleep for a day at a time
# sleep forever
#time.sleep( sys.maxsize )
#
while True:
    time.sleep( 86400 )

