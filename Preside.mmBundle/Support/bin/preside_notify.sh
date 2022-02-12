#!/bin/sh -e -x


#############################
presideIoUser=""  
presideIoPassword=""
alertPrefix="[MailMate]"
enableEmailActions=1
#alertSound="GHSound_ChurchBell.mp3"
#disableAlertMessage=1


#############################

if [ "$1" == "--setup" ]; then
    echo "Settting up Preside Notify. Please enter your credentials in response to the prompts."

    while true; do
        echo
        printf "Preside.io User Name (email address): "
        read presideIoUser
        if [ "${presideIoUser}" == "" ]; then
            continue
        fi

        while true ;  do
            printf  "Preside.io password: "
            read presideIoPassword
            if [ "${presideIoPassword}" != "" ]; then
                break ; 
            fi
        done

        status=`curl --silent --output /dev/null --write-out '%{http_code}' --user "${presideIoUser}:${presideIoPassword}" https://users.preside.io/preside/GHSendPushMsg?alertMsg=Test+notification`

        if [ $? -ne 0 ]; then
            echo "Test notification failed. Please try again"
            continue;
        fi

        if [ "${status}" = "200" ]; then 
            break
        fi
        echo
        echo "Authentication failed with result: ${result}"
        echo
        echo "Please try again"
    done

    set +e
    security delete-generic-password -a "preside.io" > /dev/null 2>&1
    set -e
    security add-generic-password -a "preside.io"  -s login -w "${presideIoUser}:${presideIoPassword}"

    echo "Preside.io credentials stored in keychain. Setup complete."
    
    
    exit 0
fi

presideIoUserPwd=`security find-generic-password -a "preside.io" -s login -w`

fromStr="${MM_FROM_NAME}"
if [ "${fromStr}" == "" ]; then
    fromStr="${MM_FROM_ADDRESS}"
fi


msgTxt="${alertPrefix} From: ${fromStr}, Subject: ${MM_SUBJECT}"


curl --silent --user "${presideIoUserPwd}" \
     --request "POST" \
     --header 'Content-Type: "application/x-www-form-urlencoded' \
     --data-urlencode "ghContentReady=1" \
     --data-urlencode "messageId=${MM_MESSAGE_ID}" \
     --data-urlencode "ghAccountName=${MM_ACCOUNT}" \
     --data-urlencode "ghFolderPath=${MM_FOLDERPATH}" \
     --data-urlencode "alertMsg=${msgTxt}" \
     --data-urlencode "ghEnableEmailActions=1" \
     https://be.preside.io/preside/GHSendPushMsg >/dev/null



