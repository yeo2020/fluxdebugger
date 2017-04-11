#! /bin/bash

LOCAL_REPO=/home/pi/fluxd
HTML_REPO=/var/www/html/fluxd
# GIT_CLONE_COMMAND="git clone https://github.com/yeo2020/fluxdebugger.git"
# GIT_RESET_COMMAND="git reset --hard origin/master"
# GIT_PULL_COMMAND="git pull"

# add autorun for Fluxdebugger
check_value=`cat /etc/rc.local | grep -c FluxDebugger.py`
if [ "$check_value" -eq 1 ]; then
    echo "auto-exec command is already written  in rc.local"
else
    echo "Add auto-exec command to rc.local"
    sudo sed -i -e '$i \# start fluxdebugger' /etc/rc.local
    sudo sed -i -e '$i \timestamp=$(date +%s)' /etc/rc.local
    sudo sed -i -e '$i \sleep 10 && sudo python -u /home/pi/fluxd/FluxDebugger.py > /home/pi/fluxd/"$timestamp".txt\n' /etc/rc.local
fi

# make directory 
if [ $# -ne 0 ];then
	echo "parameter given $1"
	if [ $1 = "-f" ];then
		echo "-f given"
		rm -rf $LOCAL_REPO
	fi
else
	echo "no parameter"
fi

if [ -d "$HTML_REPO" ] ; then
	echo "Folder exist(HTML)"
else
	echo "Folder does not exist so create(HTML)"
	sudo mkdir -p "$HTML_REPO"
	sudo chown pi "$HTML_REPO"
	sudo chgrp pi "$HTML_REPO"
fi
if [ -d "$LOCAL_REPO" ] ; then
	echo "Folder exist(FluxDebugger)"
else
	echo "Folder does not exist so create(FluxDebugger)"
	mkdir -p "$LOCAL_REPO"
fi

cd "$LOCAL_REPO"

#for wget 
if [ $# -ne 0 ];then
	echo "get master IP : $1"
    WGET_SRC="http://$1/fluxds/bin/FluxDebugger.py"
    wget -O FluxDebugger.py $WGET_SRC
    WGET_SRC2="http://$1/fluxds/bin/fluxd_update.sh"
    wget -O fluxd_update.sh $WGET_SRC2

	chmod +x fluxd_update.sh
	./fluxd_update.sh $1
fi


# For git 
#if [ -d ".git" ]; then
#	echo "Git found"
#else
#	echo "No repository found so clone source"
#	cd ..
#	$GIT_CLONE_COMMAND
#fi

#cd $LOCAL_REPO

#$GIT_RESET_COMMAND
#$GIT_PULL_COMMAND

exit 0
