#! /bin/bash

sudo sed -i "/fluxdebugger/d" /etc/rc.local
sudo sed -i "/timestamp/d" /etc/rc.local

sudo rm -rf /home/pi/FluxPlanet/fluxdebugger/
sudo rm -rf /home/pi/fluxd/
sudo rm /home/pi/bin/git_fluxdebugger_update.sh

exit 0
