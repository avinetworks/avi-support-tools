#!/usr/bin/env python
#
# Created on Jan 14, 2019
# @author: antonio.garcia@avinetworks.com
#
# AVISDK based script to get virtual service list with pool server information.

# Requirement ("pip install avisdk,argparse,PTable,json")
# Usage:- python avi_export_events.py -c <Controller-IP> -u <user-name> -p <password> -a <api_version> -t <tenant>"
# Note:- This script works for Avi Controller version 17.2.10 onwards

# The metrics are based on average values based on last 30 minutes of activity.

# Imports...

import urllib3
import json
import argparse
import sys
from prettytable import PrettyTable
from avi.sdk.avi_api import ApiSession

def main():

    parser = argparse.ArgumentParser(description="AVISDK based Script to export list of virtual services ")
    parser.add_argument("-u", "--username", required=True, help="Login username")
    parser.add_argument("-p", "--password", required=True, help="Login password")
    parser.add_argument("-c", "--controller", required=True, help="Controller IP address")
    parser.add_argument("-a", "--api_version", required=True, help="Api Version Name")
    parser.add_argument("-t", "--tenant", required=False, help="Optional: The tenant which get list from. (Default: All Tenants)")
    args = parser.parse_args()

    user = str([args.username if args.username else "admin"][0])
    password = args.password
    controller = args.controller
    api_version = str([args.api_version if args.api_version else "17.2.10"][0])
    tenant = str([args.tenant if args.tenant else "*"][0])

    print "Starting Virtual Service Check"

    # Get API Session Details
    urllib3.disable_warnings()
    api = ApiSession.get_session(controller, user, password, tenant=tenant, api_version=api_version)
    print "Avi Networks Authentication Successful"

    print "Gathering Virtual Service Information"
    page = 1
    vs_list = list()
    while True:

        resp = api.get("virtualservice", params={'page_size': 100, 'page': str(page)})

        if resp.status_code in range(200, 299):

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
    else:
        data = {}
        pretty_table = t = PrettyTable(['vs_name','vs_uuid','pool_uuid','pool_servers'])
        for vs in vs_list:
            try:
                resp = api.get('virtualservice/' + vs, tenant=tenant)
                if resp.status_code in range(200, 299):
                    vs_data = json.loads(resp.text)
                    data["vs_name"] = vs_data['name']
                    data["vs_uuid"] = vs_data['uuid']
                    data["vs_enabled"] = vs_data['enabled']
                else:
                    print 'Error: %s' % resp.text
                    exit(0)

                if 'pool_ref' in vs_data:

                    pool_uuid = 'pool-' + vs_data['pool_ref'].split('pool-')[-1]
                    data["pool_uuid"] = pool_uuid

                    resp = api.get('pool/' + data["pool_uuid"], tenant=tenant)
                    if resp.status_code in range(200, 299):
                        pool_data = json.loads(resp.text)
                        data["pool_name"] = pool_data['name']
                        pool_lst = []
                        if 'servers' in pool_data:
                            for srv in pool_data['servers']:
                                pool_lst.append(srv['ip']['addr'])
                            data['pool_servers'] = pool_lst
                    else:
                        print 'Error: %s' % resp.text
                        exit(0)

                else:
                    data["pool_name"] = 'none'
                    data["pool_uuid"] = 'none'
                    data["pool_servers"] = 'none'

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print "Unexpected Error: %s, %s" % (exc_type, exc_tb.tb_lineno)
                exit(1)

            pretty_table.add_row([data['vs_name'], data['vs_uuid'], data['pool_uuid'], data['pool_servers']])
        print pretty_table


if __name__ == "__main__":
    main()








