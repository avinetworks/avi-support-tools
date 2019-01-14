#!/usr/bin/env python
#
# Created on Jan 14, 2019
# @author: antonio.garcia@avinetworks.com
#
# AVISDK based script to disable virtual services that belong to specific tenant.

# Requirement ("pip install avisdk,argparse,requests,csv,json")
# Usage:- python avi_export_events.py -c <Controller-IP> -u <user-name> -p <password> -a <api_version> -t <tenant>" -e (option to enable vs instead of disable)
# Note:- This script works for Avi Controller version 17.2.10 onwards

# Imports...

import urllib3
import json
import argparse
from avi.sdk.avi_api import ApiSession


def main():

    parser = argparse.ArgumentParser(description="AVISDK based Script to export list of virtual services ")
    parser.add_argument("-u", "--username", required=False, help="Login username")
    parser.add_argument("-p", "--password", required=False, help="Login password")
    parser.add_argument("-c", "--controller", required=False, help="Controller IP address")
    parser.add_argument("-a", "--api_version", required=False, help="Api Version Name")
    parser.add_argument("-t", "--tenant", required=False, help="The tenant which get list from.")
    parser.add_argument("-e", "--enable", action='store_true', required=False, help="Flag if you want to enable virtual services instead.")
    args = parser.parse_args()

    user = str([args.username if args.username else "admin"][0])
    password = args.password
    controller = args.controller
    api_version = str([args.api_version if args.api_version else "17.2.10"][0])
    tenant = str([args.tenant if args.tenant else "admin"][0])
    enableonly = args.enable

    print "Starting Virtual Service Check"

    # Get API Session Details
    urllib3.disable_warnings()
    api = ApiSession.get_session(controller, user, password, tenant=tenant, api_version=api_version)

    print "Avi Networks Authentication Successful"

    resp = api.get("virtualservice", params={'page_size': 1000})

    vs_list = list()
    if resp.status_code in range(200, 299):
        json_data = json.loads(resp.text)
        for row in json_data['results']:
            if 'analytics_policy' in row:
                if row['analytics_policy']['client_insights'] != 'NO_INSIGHTS':
                    vs_list.append(row["uuid"])
    else:
        print('Error Occurred with GET VirtualService :%s' % resp.text)
        exit(0)

    print "Gathering Virtual Service Information"
    page = 1
    vs_list = list()

    while True:

        resp = api.get("virtualservice", params={'page_size': 999, 'page': str(page)})

        if resp.status_code in range(200, 299):

            print "Downloading Records (Page:" + str(page) + ")"
            json_data = json.loads(resp.text)

            for row in json_data['results']:
                vs_list.append(row["uuid"])

            if 'next' in json_data:
                page = page + 1
            else:
                print "Total VS Found: " + str(json_data['count'])
                break
        else:
            print('Error Occurred /w GET:%s' % resp.text)
            exit(0)

    if len(vs_list) < 1:
        print 'No Virtual Services Found!'
        exit(0)

    output = raw_input("Type 'y' to continue and disable/enable listed virtual services or any other key to cancel.")
    if output != 'y':
        print 'Request Cancelled!'
        exit(0)
    else:
        print "Changing Virtual Service Statuses"
        for vs in vs_list:

            resp = api.get('virtualservice/' + str(vs))
            if resp.status_code in range(200, 299):

                status = 'true' if enableonly else 'false'
                vs_data = json.loads(resp.text)
                vs_data['enabled'] = status

                resp = api.put('virtualservice/' + str(vs), tenant=tenant, data=vs_data)
                if resp.status_code in range(200, 299):
                    print '- VS[%s]: Status Changed' % str(vs)
                else:
                    print 'Error: %s' % resp.text

            else:
                print 'Error: %s' % resp.text
                exit(0)


if __name__ == "__main__":
    main()








