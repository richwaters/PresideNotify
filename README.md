# PresideNotify
PresideNotify is of tools for monitoring email Inboxes and/or folders and sending notifications to the Preside iPhone app when new emails arrive.  



      
## Prerequisites
Before using these monitoring tools, you should go to the More > Syncing screen in Preside and set the 'Background Sync' type to "Remote (private computer)". That should lead you through a process whereby you register for a Preside.io account if you don't already have one. You should also enable the 'New email notification' option on that same 'Syncing & Notifications' screen. That should obtain permission from iOS to issue notifications. 

To check to make sure you have everything setup properly, open the terminal app or other shell and issue a 'curl' command like:

curl --user https://users.preside.io/preside/GHSendPushMsg?alertMsg=Test. 

That should cause a notification to appear on your device.             



## Applescript monitoring
The Applescript option uses the Mac Mail app to monitor for new emails. It is setup as a rule in that Mac Mail app. To make use of this tool, start by downloading the PresideNotify.applescript file. Then double click on the file to open it in the Applescript Editor. Next, edit the 'set ghUser to ""' line and insert your own Preside.io user name between the "".  Then, edit the 'set ghPassword to ""' line and insert your Preside.io password in between the "".

At this point the applescript is configured and is ready to be setup as a rule inside the Mac Mail app.

