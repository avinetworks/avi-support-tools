#!/usr/bin/env python
#
# Created on Feb 28, 2019
# @author: antonio.garcia@avinetworks.com
#
# AVISDK based script to export data of networks (All Tenants)
# Requirement ("pip install avisdk,argparse,requests")
# Usage:- python avi_export_events.py -c <Controller-IP> -u <user-name> -p <password> -a <api_version> -t <tenant> 
# Note:- This script works for Avi Controller version 17.2.1 onwards

# Imports...

import urllib3
import json
import argparse
import os
from avi.sdk.avi_api import ApiSession

def main():

    parser = argparse.ArgumentParser(
        description="AVISDK based Script to export data of all networks across tenants.")
    parser.add_argument("-u", "--username", required=True,
                        help="Login username")
    parser.add_argument("-p", "--password", required=True,
                        help="Login password")
    parser.add_argument("-c", "--controller", required=True,
                        help="Controller IP address")
    parser.add_argument("-a", "--api_version",
                        required=False, help="Api Version Name")
    parser.add_argument("-t", "--tenant", required=False,
                        help="The tenant which get list from.")

    args = parser.parse_args()

    user = args.username
    password = args.password
    controller = args.controller
    api_version = str([args.api_version if args.api_version else "17.2.1"][0])
    tenant = str([args.tenant if args.tenant else "admin"][0])
    filename = 'avi_network_data.json'

    print "Starting Network Data Export"

    # Get API Session Details
    urllib3.disable_warnings()
    api = ApiSession.get_session(
        controller, user, password, tenant=tenant, api_version=api_version)
    print "Avi Networks Authentication Successful"
    print "Starting Network Data Download"

    page = 1
    data = []
    while True:
        resp = api.get("vimgrnwruntime", tenant='*', params={'page_size': 500, 'page': page})
        if resp.status_code in range(200, 299):
            print "Downloading Records (Page:" + str(page) + ")"
            json_data = json.loads(resp.text)

            for row in json_data['results']:
                data.append(row)
            if 'next' in json_data:
                page = page + 1
            else:
                print "Total Records Found: " + str(json_data['count'])
                print 'Network Data Written to File (%s)' % (os.getcwd() + '/' + filename)
                break
        else:
            print('Error Occurred with Analytics :%s' % resp.text)
            exit(0)

    with open('avi_network_data.json', 'w') as file:
        file.write(json.dumps(data, ensure_ascii=False))

if __name__ == "__main__":
    main()
