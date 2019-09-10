# PresideNotify
PresideNotify is of tools for monitoring email Inboxes and/or folders and sending notifications to the Preside iPhone app when new emails arrive.  


<br/>
      
## Prerequisites
Before using these monitoring tools, you should go to the More > Syncing screen in Preside and set the 'Background Sync' type to "Remote (private computer)". That should lead you through a process whereby you register for a Preside.io account if you don't already have one. You should also enable the 'New email notification' option on that same 'Syncing & Notifications' screen. That should obtain permission from iOS to issue notifications. Finally, on that screen, scroll down a little to the 'Remote notifications' section and set the 'Manager' option to 'Remote'.

To check to make sure you have everything setup properly, open the terminal app or other shell and issue a 'curl' command like:

   curl --user '<Preside.io user name>:<Preside.io password>' 'https://users.preside.io/preside/GHSendPushMsg?alertMsg=Test'

That should cause a notification to appear on your device.             


<br/>

## Applescript monitoring
The Applescript option uses the Mac Mail app to monitor for new emails. You'll need to leave that app always running for the notifications to be delivered. The way this works is that a 'rule' is setup in Mac Mail app that runs the applescript whenever a new mail is received. 

To make use of this tool, start by downloading the PresideNotify.applescript file. Then double click on the file to open it in the Applescript Editor. Next, edit the 'set ghUser to ""' line and insert your own Preside.io user name between the "".  Then, edit the 'set ghPassword to ""' line and insert your Preside.io password in between the "". Exit the Applescript Editor and move the script into the ~/Library/Application\ Scripts/com.apple.mail folder.

At this point the applescript is configured and is ready to be setup as a rule inside the Mac Mail app. To do that, open the Mail app and click 'Mail' then 'Preferences'. Then click on 'Rules' towards the top right. Next, click 'Add rule' to create the new rule. Enter 'PresideNotify' for the 'Description'. Then, change the criteria to 'If **any** conditions are met' and '**Every message**'. Next, change the actions to '**Run applescript**' and select the PresideNotify applescript.

[This screenshot](PresideMailRuleScreenshot.png) shows what the rule parameters should generally look like. (Advanced users might choose to use a different filter than 'Every message' or even set up multiple rules that uses different notifications depending on the filter.) 

After saving the rule, make sure that it is 'checked' in the list of rules.

That's it. You should now be notified whenever a new message is received and the Mac Mail app is running.

<br/>


## Python Monitoring

The python monitoring option is slightly more advanced, in that it can be run as a daemon and/or on a server. The script is a python3 script. As such you should either specify python3 on the command line or with the #! at the top of the script or make sure that python3 is the default python version for your environment. To set it up, download the preside-notify.py script and the preside-notify.cfg file. Then, edit the preside-notify.cfg file and fill in the appropriate values for the 'MonitoredFolders' variable. Also, the script uses some packages you'll need to install:

sudo pip3 install requests
sudo pip3 install imaplib2
sudo pip3 install json5

At this point, the script is ready to run. You can do that with a command like:

    python3 preside-notify.py --verbose --config=preside-notify.cfg
    
The --verbose argument is optional. It is recommended that you include it in your initial testing, but that you eventually remove the argument to avoid excessive output.


### Limitations
- The python option only works with IMAP accounts
- Also, it won't work with accounts that require OAuth authentication. You might be able to work around that issue by creating an app-specific password.

<br/>

## Config File Reference
This section documents the configuration file used by the python script configuration file. 

- *ConfigFileVersion* - This is the version of the configuration file. Don't change this.
- *MonitoredFolders* - This is the list of folders/Inboxes you want to monitor for new emails. It is an array of entries defined as follows:
  - *user* - This is the user name for your IMAP account. It will usually be your email address.
  - *password* - This is the password for your IMAP account.
  - *server* - This is your IMAP server
  - *folder* - This is the folder or Inbox you'd like to monitor for new emails. Inboxes should be specified as INBOX. Other should be specified with the full path to the folder that uses the proper IMAP prefix and hierarchy characters. This might look something like: INBOX.Reference.Travel, or it might look something like Reference/Travel, or it might look like something else, depending on your server.
  - *accountName* - This is the name of the account as it appears in Preside. 
  - *presideIoUser* - This is the email address you chose as your login id when you registered for your Preside.io account
  - *presideIoPassword* - This is your Preside.io password
  - *idleTimeout* - This is the time in minutes the script will 'IDLE" while waiting for new emails. It should almost never be changed from 29. Learn about IMAP IDLE if you do want to change this.
  
<br/>


## URL Reference
This section documents the URL paramateters that can be passed to Preside.io to invoke push notifications. The first part of the URL, itself is specfified as: **https://users.preside.io/preside/GHSendPushMsg** followed by various URL variables. These variables are each optional. Their values must be url encoded with the proper percent encoding as defined in RFC 3896. 

- *alertMsg* - This is the message that will be displayed in the notification.
- *badgeNum* - This can be used to badge the applicationIcon with the provided number.
- *alertSound* - This specifies a sound to play for the notification. The available sounds are:  
    GHSound_Applause.mp3  
    GHSound_Piano1.mp3  
    GHSound_ChurchBell.mp3  
    GHSound_Silence.wav  
    GHSound_ChurchBell.mp3  
    GHSound_Symbol.mp3  
    GHSound_Comedy.mp3  
    GHSound_Tock.mp3  
    GHSound_DogBark.mp3  
    GHSound_TulaBass.mp3  
    GHSound_Forest.mp3          
    GHSound_LaserShot.mp3        
    GHSound_LuneCalls.mp3  
- *dontWakeApp* - This will deliver the notification without waking the app to perform a background refresh.
- *ghContentReady* - This can be set to 1 to tell the app to wake up and sync emails in order that it has the email loaded when a notification is tapped. The 'dontWakeApp' parameter will be ignored if 'ghContentReady' is set to 1.

    The following parameters are only used if 'ghContentReady' is set to 1. They are useful in helping the app know what should be synced in order to download the email.
    - *ghAccountName* -  This specifies the account in which the email was received.
    - *ghFolderPath* - This is the folder (or INBOX) in which the email was received.
    - *messageId* - This is the messageId for the new email
    - *accountInfoHash* - This is an alternate means of specifying the account .The value can be obtained from the app, but this should generally not be used.

- *deviceId* - This can be used to send the notification to a specific device. The value can be obtained from the app, but this should generally not be used.




