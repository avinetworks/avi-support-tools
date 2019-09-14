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

    parser = argparse.ArgumentParser(description="AVISDK based Script disable client insights from VS")
    parser.add_argument("-u", "--username", required=True, help="Login username")
    parser.add_argument("-p", "--password", required=True, help="Login password")
    parser.add_argument("-c", "--controller", required=True, help="Controller IP address")
    parser.add_argument("-a", "--api_version", required=True, help="Api Version Name")
    parser.add_argument("-t", "--tenant", required=False, help="Optional: The tenant which get list from. (Default: All Tenants)")
    args = parser.parse_args()

    user = str([args.username if args.username else "admin"][0])
    password = args.password
    controller = args.controller
    api_version = str(args.api_version)
    tenant = str([args.tenant if args.tenant else "*"][0])

    print "Starting Application Profile Check"

    # Get API Session Details
    urllib3.disable_warnings()
    api = ApiSession.get_session(controller, user, password, tenant=tenant, api_version=api_version)
    print "Avi Networks Authentication Successful"

    print "Gathering Virtual Service Information"
    page = 1
    vs_list = list()

    while True:
        print 'Data Page: %s' % str(page)
        resp = api.get("virtualservice", params={ 'page': page, 'page_size': 175 })

        if resp.status_code in range(200, 299):
            json_data = json.loads(resp.text)

            for row in json_data['results']:
                if 'analytics_policy' in row:
                    if row['analytics_policy']['client_insights'] != 'NO_INSIGHTS':
                        vs_list.append(row["uuid"])

            if 'next' in json_data:
                page = page + 1
            else:
                break
        else:
            print('Error Occurred with GET VirtualService: %s' % resp.text)
            exit(0)

    if len(vs_list) < 1:
        print 'No Virtual Services /w Client Insights'
        exit(0)

    print 'Total VS /w Client Insights: %s' % len(vs_list)

    output = raw_input(
        "Type 'y' to continue and disable client insights from the identified VS or any other key to cancel. ")
    if output != 'y':
        print 'Request Cancelled!'
        exit(0)
    else:

        print "Removing 'Client Insights' from selected virtual services."

        for vs in vs_list:

            resp = api.get('virtualservice/' + str(vs))
            if resp.status_code in range(200, 299):
                vs_data = json.loads(resp.text)

                try:
                    vs_data['analytics_policy']['client_insights'] = 'NO_INSIGHTS'
                    resp = api.patch('virtualservice/' + str(vs), tenant=tenant, data={'replace': vs_data})
                    

                    if resp.status_code in range(200, 299):
                        print '- VS[%s]: Client Insights Disabled' % str(vs)
                    else:
                        print 'Error: %s' % resp.text
                except Exception as e:
                    print "Error Updating VS: %s" % vs

            else:
                print 'Error: %s' % resp.text
                exit(0)


if __name__ == "__main__":
    main()
