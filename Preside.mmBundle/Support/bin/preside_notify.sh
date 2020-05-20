#!/bin/sh


#############################
presideIoUser=""  
presideIoPassword=""
alertPrefix="[MailMate]"
enableEmailActions=1
#alertSound="GHSound_ChurchBell.mp3"
#disableAlertMessage=1


#############################


fromStr="${MM_FROM_NAME}"
if [ "${fromStr}" == "" ]; then
    fromStr="${MM_FROM_ADDRESS}"
fi


msgTxt="${alertPrefix} From: ${fromStr}, Subject: ${MM_SUBJECT}"


curl -v --user "${presideIoUser}:${presideIoPassword}" \
     --data-urlencode "ghContentReady=1" \
     --data-urlencode "messageId=${MM_MESSAGE_ID}" \
     --data-urlencode "ghAccountName=${MM_ACCOUNT}" \
     --data-urlencode "ghFolderPath=${MM_FOLDERPATH}" \
     --data-urlencode "alertMsg=${msgTxt}" \
     --data-urlencode "ghEnableEmailActions=1" \
     https://users.preside.io/preside/GHSendPushMsg



