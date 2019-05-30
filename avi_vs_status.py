#!/usr/bin/env python
#
# Created on Jan 14, 2019
# @author: antonio.garcia@avinetworks.com
#
# AVISDK based script to get virtual service status details

# Requirement ("pip install avisdk,argparse,requests,csv,json")
# Usage:- python avi_export_events.py -c <Controller-IP> -u <user-name> -p <password> -a <api_version> -t <tenant>"
# Note:- This script works for Avi Controller version 17.2.10 onwards

# NMDA: No Metric Data Available
# NHDA: No Health Score Data Available
# NODA: No Operation Status Data Available

# The metrics are based on average values based on last 30 minutes of activity.

# Imports...

import urllib3
import json
import argparse
import sys
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

            print "Downloading Records (Page:" + str(page) + ")"
            json_data = json.loads(resp.text)

            for row in json_data['results']:
                vs_list.append(row["uuid"])

            if 'next' in json_data:
                page = page + 1
            else:
                print "Total VS Found: " + str(json_data['count'])
                print "-----------------------------------------------------"
                break
        else:
            print('Error Occurred /w GET:%s' % resp.text)
            exit(0)

    if len(vs_list) < 1:
        print 'No Virtual Services Found!'
        exit(0)
    else:
        for vs in vs_list:
            try:
                data = []
                resp = api.get('virtualservice/' + vs, tenant=tenant)
                if resp.status_code in range(200, 299):
                    vs_data = json.loads(resp.text)
                    data.append(vs_data['name'])
                    data.append(vs_data['uuid'])
                    data.append(str(vs_data['enabled']))
                else:
                    print 'Error: %s' % resp.text
                    exit(0)

                metric_req_payload = {
                    "metric_requests":
                    [
                        {"step":300,"limit":6,"entity_uuid": vs,"id":"l4_client.avg_bandwidth","metric_id":"l4_client.avg_bandwidth"}
                ]}

                resp = api.post('analytics/metrics/collection?include_name&include_refs=true&pad_missing_data=false&dimension_limit=1000', data=metric_req_payload)
                if resp.status_code in range(200, 299):
                    vs_metric = json.loads(resp.text)
                    try:
                        data.append(vs_metric['series']['l4_client.avg_bandwidth'][vs][0]['header']['statistics']['mean'])
                    except Exception as e:
                        data.append('NMDA')
                else:
                    data.append('NMDA')

                resp = api.get('virtualservice-inventory/' + vs + '/?include_name=true&include=health_score%2Cruntime%2Calert%2Cfaults&step=300&limit=6')
                if resp.status_code in range(200, 299):
                    vs_hmdata = json.loads(resp.text)
                    try:
                        data.append(vs_hmdata['health_score']['health_score'])
                    except Exception as e:
                        data.append('NHDA')

                    try:
                        data.append(vs_hmdata['runtime']['oper_status']['state'])
                    except Exception as e:
                        data.append('NODA')
                else:
                    data.append('NHDA')
                    data.append('NODA')

                print 'VS: %s, ENABLED: %s, STATUS: %s, AVG_BW: %s, HS: %s' % (data[1], data[2], data[5], data[3], data[4])

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print "Unexpected Error: %s, %s" % (exc_type, exc_tb.tb_lineno)
                exit(1)

    print "-----------------------------------------------------"
    print 'All Tasks Done!'


if __name__ == "__main__":
    main()








