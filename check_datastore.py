#!/usr/bin/python2.7
# coding: utf-8

"""

    An Nagios plugin made in Python using pyVmomi that
    get informations for virtual machines, esx hosts and datastores

"""

__author__ = "Sébastien Douce <sebastien.douce@cheops.fr>"
__version__ = "1.0"
import csv
import ssl
try:
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from pyVim import connect
        from pyVmomi import vmodl
        from pyVmomi import vim
except ImportError as e:
    raise(e)

import atexit
from optparse import OptionParser

def get_properties(content, viewType, props, specType):
    # Build a view and get basic properties for all Virtual Machines
    """
    Obtains a list of specific properties for a particular Managed Object Reference data object.

    :param content: ServiceInstance Managed Object
    :param viewType: Type of Managed Object Reference that should populate the View
    :param props: A list of properties that should be retrieved for the entity
    :param specType: Type of Managed Object Reference that should be used for the Property Specification
    """
    #print (viewType)
    objView = content.viewManager.CreateContainerView(content.rootFolder, viewType, True)
    tSpec = vim.PropertyCollector.TraversalSpec(name='tSpecName', path='view', skip=False, type=vim.view.ContainerView)
    pSpec = vim.PropertyCollector.PropertySpec(all=False, pathSet=props, type=specType)
    oSpec = vim.PropertyCollector.ObjectSpec(obj=objView, selectSet=[tSpec], skip=False)
    pfSpec = vim.PropertyCollector.FilterSpec(objectSet=[oSpec], propSet=[pSpec], reportMissingObjectsInResults=False)
    retOptions = vim.PropertyCollector.RetrieveOptions()
    totalProps = []
    retProps = content.propertyCollector.RetrievePropertiesEx(specSet=[pfSpec], options=retOptions)
    totalProps += retProps.objects
    while retProps.token:
        retProps = content.propertyCollector.ContinueRetrievePropertiesEx(token=retProps.token)
        totalProps += retProps.objects
    objView.Destroy()
    # Turn the output in retProps into a usable dictionary of values
    gpOutput = []
    for eachProp in totalProps:
        propDic = {}
        for prop in eachProp.propSet:
            propDic[prop.name] = prop.val
        propDic['moref'] = eachProp.obj
        gpOutput.append(propDic)
    return gpOutput

def get_obj(content, vmname, obj):
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, obj, True)
    for c in container.view:
        if c.name == vmname:
            obj = c
            break
    return obj


def nagios_return(PercentUsage, SurAlloc_percent, warn, crit, warning_suralloc, critical_suralloc, comment):
    if PercentUsage >= crit or SurAlloc_percent >= critical_suralloc:
        print "CRITICAL - " + comment
        return 2
    elif PercentUsage >= warn or SurAlloc_percent >= warning_suralloc:
        print "WARNING - " + comment
        return 1
    else:
        print "OK - " + comment
        return 0
    print "CRITICAL - Unknown value : %d" % PercentUsage
    return 2




"""
Process Datastore Informations:
    datastore.summary.freeSpace
    datastore.summary.capacity
    datastore.summary.accessible
    datastore.summary.maintenanceMode
"""


def process_datastore_info(content, warn, crit, warning_suralloc, critical_suralloc):
    datastore = get_obj(content, opt.name, [vim.HostSystem])
    #print datastore.summary
    if opt.action in "FreeSpace":
        capacity_octet=int(datastore.summary.capacity)
        freespace_octet=int(datastore.summary.freeSpace)
        used_octet=int(capacity_octet-freespace_octet)
        try:
            Uncommitted=int(datastore.summary.uncommitted)
        except:
            Uncommitted=0
        freeSpace = ((float(datastore.summary.freeSpace)/1024/1024/1024))
        Capacity = ((float(datastore.summary.capacity)/1024/1024/1024))
        PercentFree = ((freeSpace/Capacity)*100)
        PercentUsage = ((100-PercentFree))

        SurAlloc_percent = int((((capacity_octet-freespace_octet+Uncommitted) *100)/ capacity_octet))
        #((($result.Summary.Capacity - $result.Summary.FreeSpace) + $result.Summary.Uncommitted)*100)/$result.Summary.Capacity,0)


        snapds = get_obj(content, opt.name, [vim.DatastoreInfo])
        REQ_DS = snapds.summary.datastore
        retProps = get_properties(content, [vim.VirtualMachine], ['name', 'snapshot', 'datastore'], vim.VirtualMachine)
        snap = 0
        for vm in retProps:
            DSVM_NAME = (vm['datastore'])
            if REQ_DS == DSVM_NAME[0]:
                if ('snapshot' in vm):
                    snap = snap+1
   
        comment = str(opt.name) + ".FreeSpace: " + str(round(freeSpace,2)) \
        + " GB, Capacity: " + str(round(Capacity,2)) + " GB, " \
        + str(round(PercentUsage ,2)) \
        + "% Used <br> Surallocation "+  str(SurAlloc_percent) + "% <br> Snapshot Running(" + str(snap)+ ") | 'Used'=" \
        +  str(round(used_octet,2))\
        +"o;;;;" \
        + str(capacity_octet) \
        + " 'Percent_Used'=" + str(PercentUsage) + "%;" +str(warn)+";"+str(crit) + " 'SurAllocation_Percent'="+str(SurAlloc_percent)+"%;"+str(warning_suralloc)+";"+str(critical_suralloc)+";"
        return nagios_return(PercentUsage, SurAlloc_percent, warn, crit, warning_suralloc, critical_suralloc, comment)

    elif opt.action in "HealthStatus":
        accessible = datastore.summary.accessible
        maintenance = datastore.summary.maintenanceMode
        comment = "Datastore is accessible: %s, Maintenance Mode status: %s for %s " % (accessible, maintenance, opt.name)
        if accessible is True and maintenance in "normal":
            print "OK - " + comment
            return 0
        else:
            print "CRITICAL - " + comment
            return 2
    else:
        return parser.print_help()


def main():
    global opt
    global parser

    help_text = """
    This is a bigger help with actions separated by mode


    if mode = datastore
        name = datastore name
            actions =
                FreeSpace
                Health
    """
    parser = OptionParser(usage=help_text, version="%prog 1.0 beta")
    parser.add_option("-H", action="store", help="vCenter Hostname/IP",
                      dest="hostname")
    parser.add_option("-P", action="store",
                      help="vCenter Port (default: %default)",
                      dest="port", default=443, type=int)
    parser.add_option("-A", action="store", help="Authfile",
                      dest="authfile")
    parser.add_option("-n", action="store", help="see usage text",
                      dest="name")
    parser.add_option("-a", action="store", help="see usage text",
                      dest="action")
    parser.add_option("-W", action="store", help="The Warning threshold (default: %default)",
                      dest="warning_suralloc", default=150, type=int)
    parser.add_option("-C", action="store", help="The Critical threshold (default: %default)",
                      dest="critical_suralloc", default=180, type=int)
    parser.add_option("-w", action="store", help="The Warning threshold (default: %default)",
                      dest="warning", default=80, type=int)
    parser.add_option("-c", action="store", help="The Critical threshold (default: %default)",
                      dest="critical", default=90, type=int)

    (opt, args) = parser.parse_args()

    """
    Required Arguments
    """
    if (opt.hostname is None or opt.authfile is None or opt.name is None):
        return parser.print_help()
    file = open(opt.authfile,"rb")

    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE
        

    except:
        python_test_context = "NO"
        #print python_test_context
    
    
    python_test_context = "YES"

    try:
        reader = csv.reader(file)
        for row in reader:
            LIGNE=row[0]
            if LIGNE.startswith("CSV_ENTRY"):
                username = LIGNE.split(';')[1]
                password = LIGNE.split(';')[2]
    finally:
        file.close()    


    try:
        if python_test_context == "NO":
            si = connect.SmartConnect(host=opt.hostname,
                user=username,
                pwd=password,
                port=int(opt.port))
        else:
            si = connect.SmartConnect(host=opt.hostname,
                user=username,
                pwd=password,
                port=int(opt.port), sslContext=context)

        if not si:
            print("Could not connect to %s using "
                  "specified username and password" % opt.username)
            return -1

        atexit.register(connect.Disconnect, si)

        content = si.RetrieveContent()
        warn=opt.warning
        crit=opt.critical
        warning_suralloc = opt.warning_suralloc
        critical_suralloc = opt.critical_suralloc
        process_datastore_info(content, warn, crit, warning_suralloc, critical_suralloc)

    except vmodl.MethodFault, e:
        print "Caught vmodl fault : " + e.msg
        return -1
    except IOError, e:
        print "Could not connect to %s. Connection Error" % opt.hostname
        return -1
    return 0


if __name__ == "__main__":
    main()
