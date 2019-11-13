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
    
The --verbose argument is optional. It can be added multiple times to increase the verbosity. It is recommended that you include it once in your initial testing, but that you eventually remove the argument to avoid excessive output.


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
  - *idleTimeout* - This is the time in minutes the script will 'IDLE" while waiting for new emails. Usually, this shouldn't be changed from 29 if your internet connection is always on. If you sometimes lose connectivity, the value can be reduced in order to recover from those losses quicker. If you're running on a laptop that likes to sleep its network connection for example, you might want to set this to 15 or even 5 so that notifications will be sent quicker when the device wakes. You shouldn't make the value greater than 29 unless you are familiar with IMAP IDLE and you have configured your server appropriately. 
  
  
  - *enableEmailActions* (optional) - Set this to true if you'd like to allow actions (as defined in the Notification Actions screen in the app) to be performed on the email. **Please note** that these actions will only work if the app has actually had time to sync the email. Otherwise, the action will fail silently.

  - *disableAlertMessage* (optional) - Set this to true if you don't want the text alert when you receive an email. Use this if you only want a sound notification or if you'd like the script to wake the app on your device when new mail arrives and let it issue the notifications. In that case, you should also set the "Remote Notifications Manager" in the Syncing preferences of the app to  "App". The advantage of this approach is that you can then make use of the 'Notification Rules' feature of the app and the email for the notification is guaranteed to be synced to the app before the notification is issued. The downside of this approach is that some notifications might be delayed.
  
   - *alertSound* (optional) - Use this to include a sound with the notification. The available sounds are listed in the URL References section of this document. 
   
   - *alertPrefix* (optional) - Use this to include some text before the beginning of the alert message. For example, it can be useful to use the account name here to indicate which account the email came in on. Or, you might include the name of the script to remind you of what is generating the notification.X Include a newline in this string to place this prefix on a separate line.
  
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
    
- *dontWakeApp* - This will deliver the notification without waking the app to perform a background refresh. The 'dontWakeApp' parameter will be ignored if 'ghContentReady' is true or if 'ghEnableEmailActions' is true.

- *ghContentReady* - This can be set to 1 to tell the app to wake up and sync emails in order that it has the email loaded when a notification is tapped. 

    The following parameters are only used if 'ghContentReady' is set to 1. They are useful in helping the app know what should be synced in order to download the email.
    - *ghAccountName* -  This specifies the account in which the email was received.
    - *ghFolderPath* - This is the folder (or INBOX) in which the email was received.
    - *messageId* - This is the messageId for the new email
    - *accountInfoHash* - This is an alternate means of specifying the account .The value can be obtained from the app, but this should generally not be used.

- *deviceId* - This can be used to send the notification to a specific device. The value can be obtained from the app, but this should generally not be used.

- *ghEnableEmailActions* - Setting this to true or 1 allows notification actions to be performed on the email in the notification. When invoked, the action will only work if the app has actually had time to sync the email. Otherwise, the action will fail silently.




