This file is needed at 
/lib/systemd/system/
to run on start up on the raspberry pi
to enable use theses cmds 
sudo systemctl enable bleclient.service
sudo systemctl daemon-reload
The pi does need to be rebooted to have the service be active
