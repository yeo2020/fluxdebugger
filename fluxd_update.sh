#! /bin/bash

LOCAL_REPO=/home/pi/fluxd
# GIT_CLONE_COMMAND="git clone https://github.com/yeo2020/fluxdebugger.git"
# GIT_RESET_COMMAND="git reset --hard origin/master"
# GIT_PULL_COMMAND="git pull"


cd "$LOCAL_REPO"

#for wget 
if [ $# -ne 0 ];then
    echo "get master IP : $1"
    WGET_SRC="http://$1/fluxds/bin/debayer"
    wget -O debayer $WGET_SRC
    WGET_SRC2="http://$1/fluxds/bin/rpiraw"
    wget -O rpiraw $WGET_SRC2
    chmod +x debayer
    chmod +x rpiraw
fi


# For git 
#if [ -d ".git" ]; then
#   echo "Git found"
#else
#   echo "No repository found so clone source"
#   cd ..
#   $GIT_CLONE_COMMAND
#fi

#cd $LOCAL_REPO

#$GIT_RESET_COMMAND
#$GIT_PULL_COMMAND

exit 0
