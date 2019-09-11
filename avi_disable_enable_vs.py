#!/usr/bin/env python
#
# Created on Jan 14, 2019
# AVISDK based script to disable virtual services that belong to specific tenant.

# Requirement ("pip install avisdk,argparse,requests,csv,json")
# Usage:- python avi_disable_enable_vs.py -c <Controller-IP> -u <user-name> -p <password> -a <api_version> -t <tenant>" -e (option to enable vs instead of disable)

# Imports...

import urllib3
import json
import argparse
import threading
from Queue import Queue
from avi.sdk.avi_api import ApiSession


def crawl_update(q, result, api, tenant, enableonly):

    while not q.empty():
        work = q.get()
        try:
                status = True if enableonly else False
                data = {'enabled': status}

                resp = api.patch('virtualservice/' + work[1], tenant=tenant, data={'replace': data})

                if resp.status_code in range(200, 299):
                    print '- VS[%s]: Status Changed' % work[1]
                    result[work[0]] = {'- VS[%s]: Status Changed' % work[1]}
                else:
                    print 'Error: %s' % resp.text
                    result[work[0]] = {'Error: %s' % resp.text}

        except:
            result[work[0]] = {'Exception Error'}

        q.task_done()

    return True


def main():

    parser = argparse.ArgumentParser(description="AVISDK based Script to export list of virtual services ")
    parser.add_argument("-u", "--username", required=True, help="Login username")
    parser.add_argument("-p", "--password", required=True, help="Login password")
    parser.add_argument("-c", "--controller", required=True, help="Controller IP address")
    parser.add_argument("-a", "--api_version", required=True, help="Api Version Name")
    parser.add_argument("-t", "--tenant", required=False, help="The tenant which get list from.")
    parser.add_argument("-e", "--enable", action='store_true', required=False, help="Flag if you want to enable virtual services instead.")
    args = parser.parse_args()

    user = str([args.username if args.username else "admin"][0])
    password = args.password
    controller = args.controller
    api_version = str(args.api_version)
    tenant = str([args.tenant if args.tenant else "admin"][0])
    enableonly = args.enable

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
                break
        else:
            print('Error Occurred /w GET:%s' % resp.text)
            exit(0)

    if len(vs_list) < 1:
        print 'No Virtual Services Found!'
        exit(0)

    output = raw_input("Type 'y' to continue and disable/enable listed virtual services or any other key to cancel.: ")
    if output != 'y':
        print 'Request Cancelled!'
        exit(0)
    else:

        q = Queue(maxsize=0)
        num_theads = min(100, len(vs_list))
        results = [{} for x in vs_list]
        for i in range(len(vs_list)):
            q.put((i, vs_list[i]))

        for i in range(num_theads):

            # print 'Starting Thread: %s' % i
            worker = threading.Thread(target=crawl_update, args=(q, results, api, tenant, enableonly))
            worker.setDaemon(True)
            worker.start()

        q.join()
        print 'All Tasks Done!'


if __name__ == "__main__":
    main()








