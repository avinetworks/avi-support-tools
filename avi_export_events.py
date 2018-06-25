#!/usr/bin/env python
#
# Created on June 20, 2018
# @author: antonio.garcia@avinetworks.com
#
# AVISDK based script to export all system events into a CSV format for easy filtering.

# Requirement ("pip install avisdk,argparse,requests,datetime,csv,json")
# Usage:- python avi_export_events.py -c <Controller-IP> -u <user-name> -p <password> -a <api_version> -sd <startdate> -st <starttime> -ed <enddate> -et <endtime>
# Note:- This script works for Avi Controller version 17.2.1 onwards
# Note:- The start and end timestamps for the events should be in UTC timezone.

#Imports...
from requests import urllib3
import json
import argparse
from os import path
from avi.sdk.avi_api import ApiSession
from datetime import datetime
import csv

def main():

    parser = argparse.ArgumentParser(description="AVISDK based Script to import a a certificate based on tenant.")
    parser.add_argument("-u", "--username", required=False, help="Login username")
    parser.add_argument("-p", "--password", required=False, help="Login password")
    parser.add_argument("-c", "--controller", required=False, help="Controller IP address")
    parser.add_argument("-a", "--api_version", required=False, help="Api Version Name")
    parser.add_argument("-sd", "--startdate", required=False, help="The start date to gather logs format:<yyyy-mm-dd>")
    parser.add_argument("-st", "--starttime", required=False, help="The start time to gather logs format:<hh:mm:ss>")
    parser.add_argument("-ed", "--enddate", required=False, help="The end date to gather logs format:<yyyy-mm-dd>")
    parser.add_argument("-et", "--endtime", required=False, help="The end time to gather logs format:<hh:mm:ss>")

    args = parser.parse_args()

    user = args.username
    password = args.password
    controller = args.controller
    api_version = str([args.api_version if args.api_version else "17.2.1"][0])

    print "Starting Event Export"
    print "!!Note 1: The filtering of events is in UTC timezone."
    print "!!Note 2: Do not use size pull bigger than 1000 events to allow the api engine to work more gracefully."

    date_start = str([args.startdate if args.startdate else datetime.today().strftime('%Y-%m-%d')][0])
    time_start = str([args.starttime if args.starttime else "00:00:00"][0])
    date_end = str([args.enddate if args.enddate else datetime.today().strftime('%Y-%m-%d')][0])
    time_end = str([args.endtime if args.endtime else "23:59:59"][0])

    #Get API Session Details
    urllib3.disable_warnings()
    api = ApiSession.get_session(controller, user, password, tenant="*", api_version=api_version)
    print "Avi Networks Authentication Successful"

    with open('avi_system_events_export.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([u'event_time',u'obj_type',u'tenant',u'event_id',u'event_description',u'module',u'int_or_ext',u'event_pages',u'context',u'obj_uuid',u'event_details'])

        print "Starting Event Data Download"
        page = 1
        while True:

            #print "uri: " + "analytics/logs?type=2&start=" + str(date_start) + "T" + time_start + ".000Z&end=" + str(date_end) + "T" + time_end + ".999Z&page_size=1000&page=" + str(page) + "&orderby=-report_timestamp"
            resp = api.get("analytics/logs?type=2&start=" + str(date_start) + "T" + time_start + ".000Z&end=" + str(date_end) + "T" + time_end + ".999Z&page_size=1000&page=" + str(page) + "&orderby=-report_timestamp")

            if resp.status_code in range(200, 299):
                print "Downloading Records (Page:" + str(page) + ")"
                json_data = json.loads(resp.text)
                for row in json_data['results']:

                    writer.writerow([row['report_timestamp'],row['obj_type'], row['tenant'], row['event_id'], row['event_description'], row['module'], row['internal'],
                                    ";".join(row['event_pages']), row['context'], row['obj_uuid'],str(json.dumps(row['event_details'])).replace('"',"'")])

                if 'next' in json_data:
                    page = page + 1
                else:
                    print "Total Records Found: " + str(json_data['count'])
                    print "Export of System Events Completed"
                    break
            else:
                print('Error Occurred with Analytics :%s' % resp.text)
                exit(0)

if __name__ == "__main__":
    main()










