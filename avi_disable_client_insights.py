#!/usr/bin/env python
#
# Created on Jan 8, 2019
# @author: antonio.garcia@avinetworks.com
#
# AVISDK based script to disable client insights feature from all virtual service that belong to specific tenant.

# Requirement ("pip install avisdk,argparse,requests,csv,json")
# Usage:- python avi_disable_client_insights.py -c <Controller-IP> -u <user-name> -p <password> -a <api_version> -t <tenant>"
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
    args = parser.parse_args()

    user = str([args.username if args.username else "admin"][0])
    password = args.password
    controller = args.controller
    api_version = str([args.api_version if args.api_version else "17.2.10"][0])
    tenant = str([args.tenant if args.tenant else "admin"][0])

    print "Starting Application Profile Check"

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

    print 'Total VS /w Client Insights: %s' % len(vs_list)

    if len(vs_list) < 1:
        print 'No Virtual Services /w Client Insights'
        exit(0)

    output = raw_input("Type 'y' to continue and disable client insights from the identified VS or any other key to cancel.")
    if output != 'y':
        print 'Request Cancelled!'
        exit(0)
    else:
        print "Removing 'Client Insights' from selected virtual services."
        for vs in vs_list:

            resp = api.get('virtualservice/' + str(vs))
            if resp.status_code in range(200, 299):

                vs_data = json.loads(resp.text)
                vs_data['analytics_policy']['client_insights'] = 'NO_INSIGHTS'

                resp = api.put('virtualservice/' + str(vs), tenant=tenant, data=vs_data)
                if resp.status_code in range(200, 299):
                    print '- VS[%s]: Client Insights Disabled' % str(vs)
                else:
                    print 'Error: %s' % resp.text

            else:
                print 'Error: %s' % resp.text
                exit(0)


if __name__ == "__main__":
    main()








