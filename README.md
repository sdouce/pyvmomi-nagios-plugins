# pyvmomi-nagios-plugins

Plugins inspired from https://github.com/rogerlz/nagios-check-vcenter 

## check_datastore.py : 
For your VMFS :
This plugin can alert you for two thing :
  - VMFS Occupation 
  - VMFS Surallocation

Usage:
	    This is a bigger help with actions separated by mode
	
	
	    if mode = datastore
	        name = datastore name
	            actions =
	                FreeSpace
	                Health
	
	
	Options:
	  --version             show program's version number and exit
	  -h, --help            show this help message and exit
	  -H HOSTNAME           vCenter Hostname/IP
	  -P PORT               vCenter Port (default: 443)
	  -A AUTHFILE           Authfile
	  -n NAME               see usage text
	  -a ACTION             see usage text
	  -W WARNING_SURALLOC   The Warning threshold (default: 150)
	  -C CRITICAL_SURALLOC  The Critical threshold (default: 180)
	  -w WARNING            The Warning threshold (default: 80)
	  -c CRITICAL           The Critical threshold (default: 90)


Status information give number of SnapShot present on VMFS . 
Graph Output show you 

## snap.py : 
For one VM 
Generate Alert if : 
  - Snapshot is more than x Days Old 
  - Snapshot threechild is bigger than 3 level . 


