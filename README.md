# pyvmomi-nagios-plugins

Plugins inspired from https://github.com/rogerlz/nagios-check-vcenter 

## check_datastore.py : 
  This plugin can alert you for two thing :
    - VMFS Occupation 
    - VMFS Surallocation
Status information give number of SnapShot present on VMFS . 
Graph Output show you 

## snap.py : 
For one VM 
Generate Alert if : 
  - Snapshot is more than x Days Old 
  - Snapshot threechild is bigger than 3 level . 


