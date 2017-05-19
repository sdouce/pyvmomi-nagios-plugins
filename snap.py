#!/usr/bin/python2.7

# Copyright 2016 Abdul Anshad <abdulanshad33@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Written by Abdul Anshad
Github: https://github.com/Abdul-Anshad-A
Email: abdulanshad33@gmail.com

Credits:
Thanks to "reuben.13@gmail.com" for the initial code.

Note: Example code For testing purposes only
vSphere Python SDK program to perform snapshot operations.
"""

from __future__ import print_function
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl, vim
from datetime import datetime

import csv
import sys
import os
import argparse
import atexit
import pytz
import getpass
import ssl


# Alter this to change the number of days for aged snapshots to display a warning in the output
warning_age = 7


def GetArgs():
    """
    Supports the command-line arguments listed below.
    """
    parser = argparse.ArgumentParser(description='Process args for retrieving all the Virtual Machines')
    parser.add_argument('-s', '--host', required=True, action='store', help='Remote host to connect to')
    parser.add_argument('-v', '--vm', required=True, action='store', help='VM Name')
    parser.add_argument("-a", "--authfile", action="store",help="Le fichier d authentification contenant user:pass")
    parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on')
                      
    args = parser.parse_args()
    return args



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


def print_snap_info(vm_snap):
    """
    This function will loop through 3 levels of snapshots and print out the name, description and
    age in a tree-type view
    :param vm_snap: The snapshot property and all values
    """
    current_snap = vm_snap.currentSnapshot
    print(vm_snap.rootSnapshotList[0].name + ' : ' + vm_snap.rootSnapshotList[0].description + ' : '
          + snap_age_check(vm_snap.rootSnapshotList[0])
          + current_snap_check(current_snap, vm_snap.rootSnapshotList[0].snapshot))
    if (vm_snap.rootSnapshotList[0].childSnapshotList):
        for snapshot in vm_snap.rootSnapshotList[0].childSnapshotList:
            print('\t|- ' + snapshot.name + ' : ' + snapshot.description + ' : ' + snap_age_check(snapshot)
                  + current_snap_check(current_snap, snapshot.snapshot))
            snap = snapshot
            if (snap.childSnapshotList):
                for snapshot in snap.childSnapshotList:
                    print('\t\t|-- ' + snapshot.name + ' : ' + snapshot.description + ' : ' + snap_age_check(snapshot)
                          + current_snap_check(current_snap, snapshot.snapshot))
                    snap = snapshot
                    if (snap.childSnapshotList):
                        for snapshot in snap.childSnapshotList:
                            print('\t\t\t|--- ' + snapshot.name + ' : ' + snapshot.description + ' : '
                                  + snap_age_check(snapshot) + current_snap_check(current_snap, snapshot.snapshot))
                            snap = snapshot
                            if (snap.childSnapshotList):
                                print('\t\t\tWARNING: Only three levels of snapshots supported, but this Virtual Machine has more.')


def snap_age_check(snapshot):
    """
    This function checks the age of each snapshot.

    :param snapshot: The current snapshot property and value in the tree
    :return: Return WARNING text with the age or just the age.
    """
    snap_age = datetime.utcnow().replace(tzinfo=pytz.utc) - snapshot.createTime
    if snap_age.days > warning_age:
        return '!WARNING! Snapshot is ' + str(snap_age.days) + ' days old'
    else:
        return str(snap_age.days) + ' days old'


def current_snap_check(current_snap, tree_snap):
    """

    :param current_snap: The current live snapshot state MORef of the Virtual Machine
    :param tree_snap: The current tree snapshot state MORef of the Virtual Machine
    :return: Return text stating where the live VM currently is in the tree or return nothing.
    """
    if current_snap == tree_snap:
        return ' : *You are here*'
    else:
        return ''


def main():
    args = GetArgs()
    authfile = args.authfile

    file = open(authfile,"rb")
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    #context.verify_mode = ssl.CERT_NONE




    try:
        reader = csv.reader(file)
        for row in reader:
            LIGNE=row[0]
            if LIGNE.startswith("CSV_ENTRY"):
                user = LIGNE.split(';')[1]
                password = LIGNE.split(';')[2]


    finally:
        file.close()
    try:
        si = None
        try:
            si = SmartConnect(host=args.host,user=user,pwd=password,port=int(args.port))#, sslContext=context)
        except IOError, e:
            pass
        if not si:
            print('Could not connect to the specified host using specified username and password')
            return -1

        atexit.register(Disconnect, si)
        content = si.RetrieveContent()

        retProps = get_properties(content, [vim.VirtualMachine], ['name', 'snapshot'], vim.VirtualMachine)
        
        VM = args.vm
        for vm in retProps:
            VM_NAME = (vm['name'])
            if str(VM_NAME) == str(VM):
                if ('snapshot' in vm):
                    print_snap_info(vm['snapshot'])
                else:
                    print ("No snapshot for " + VM )
                

    except vmodl.MethodFault as e:
        print('Caught vmodl fault : ' + e.msg)
        return -1
    except Exception as e:
        print('Caught exception : ' + str(e))
        return -1

    return 0

# Start program
if __name__ == "__main__":
    main()
