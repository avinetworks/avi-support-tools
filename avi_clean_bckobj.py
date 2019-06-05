#!/usr/bin/env python
#
# Created on June 6, 2019
# @author: antonio.garcia@avinetworks.com
#
# AVISDK based script to delete any backup config objects within database.
# Requirement ("pip install avisdk,argparse,requests,csv,json")
# Usage:- python avi_clean_bckobj.py -c <Controller-IP> -u <user-name> -p <password> -a <api_version> "
# Note:- This script works for Avi Controller version 17.2.10 onwards

# Imports...

import urllib3
import json
import argparse
from avi.sdk.avi_api import ApiSession


def main():

    parser = argparse.ArgumentParser(description="AVISDK based Script disable client insights from VS")
    parser.add_argument("-u", "--username", required=False, help="Login username")
    parser.add_argument("-p", "--password", required=True, help="Login password")
    parser.add_argument("-c", "--controller", required=True, help="Controller IP address")
    parser.add_argument("-a", "--api_version", required=False, help="Api Version Name")
    args = parser.parse_args()

    user = str([args.username if args.username else "admin"][0])
    password = args.password
    controller = args.controller
    api_version = str([args.api_version if args.api_version else "17.2.10"][0])

    print "Starting Application Profile Check"

    # Get API Session Details
    urllib3.disable_warnings()
    api = ApiSession.get_session(controller, user, password, tenant='admin', api_version=api_version)
    print "Avi Networks Authentication Successful"

    print "Gathering Virtual Service Information"
    bck_list = list()

    resp = api.get("backup")
    if resp.status_code in range(200, 299):
        json_data = json.loads(resp.text)
        for row in json_data['results']:
            print row['uuid']
            bck_list.append(row["uuid"])

    if len(bck_list) < 1:
        print 'No Backup Objects Found'
        exit(0)

    print 'Total Found: %s' % len(bck_list)


    print "Removing 'Backup Objects' !"

    for bk in bck_list:
        resp = api.delete('backup/' + str(bk))
        if resp.status_code in range(200, 299):
            print "Backup Object Delete: %s" % bk
        else:
            print 'Error: %s' % resp.text
            exit(0)


if __name__ == "__main__":
    main()
