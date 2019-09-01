

using terms from application "Mail"
	
	on perform mail action with messages theMessages
		
		-- Set this to your Preside.io userName (which is your email address)
		set ghUser to ""
		
		-- Set this to your Preside.io password
		set ghPassword to ""
		
		repeat with aMessage in theMessages
			set msg_subject to subject of aMessage
			set msg_sender to sender of aMessage
			set msg_id to message id of aMessage
			set senderName to extract name from msg_sender
			set mailBoxVar to mailbox of aMessage
			set accountVar to account of mailBoxVar
			set folderName to name of mailBoxVar
			set accountName to name of accountVar
			
			set msgTxt to "Mail.app - " & "From: " & senderName & "
" & "Subject: " & msg_subject
			
			-- Use python for URL encoding. Other possibilities are discussed here: https://stackoverflow.com/questions/23852182/i-need-to-url-encode-a-string-in-applescript
			
			set encodedTxt to do shell script "/usr/bin/python -c 'import sys, urllib; print urllib.quote(sys.argv[1])' " & "\"" & msgTxt & "\""
			
			set encodedMessageId to do shell script "/usr/bin/python -c 'import sys, urllib; print urllib.quote(sys.argv[1])' " & "\"" & msg_id & "\""
			
			-- Setup the call to curl which will post the notification
			set cmdLine to "curl -v --user '" & ghUser & ":" & ghPassword & "' 'https://users.preside.io/preside/GHSendPushMsg?ghContentReady=1&messageId=" & encodedMessageId & "&ghAccountName=" & accountName & "&ghFolderPath=" & folderName & "&alertMsg=" & encodedTxt & "'"
			
			-- Uncomment the following line to debug url
			-- do shell script "echo " & quoted form of (cmdLine as string) & ¬
			" > /tmp/PresideNotify_debug.txt"
			
			do shell script cmdLine
		end repeat
	end perform mail action with messages
end using terms from
