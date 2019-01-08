from avi.sdk.avi_api import ApiSession
import argparse
import requests
import json

requests.packages.urllib3.disable_warnings()

def main():
    parser = argparse.ArgumentParser(description="AVISDK based Script query gslb services on multiple pages ")
    parser.add_argument("-u", "--username", required=True, help="Login username")
    parser.add_argument("-p", "--password", required=True, help="Login password")
    parser.add_argument("-c", "--controller", required=True, help="Controller IP address")
    parser.add_argument("-a", "--api_version", required=False, help="Api Version Name")
    parser.add_argument("-t", "--tenant", required=False, help="Tenant, if left blank Admin is selected")
    args = parser.parse_args()

    user = args.username
    controller = args.controller
    api_version = str(args.api_version if args.api_version else '17.2.14')
    tenant = str(args.tenant if args.tenant else 'admin')
    password = args.password

    session = ApiSession(controller, user, password, tenant=tenant, api_version=api_version)


    page = 1
    while True:
        resp = session.get("gslbservice?page_size=1000&page=" + str(page))
        if resp.status_code in range(200, 299):
            json_data = json.loads(resp.text)
            print(json_data['results'])
            if 'next' in json_data:
                page += 1
            else:
                print("End of entries")
                break
        else:
            print("Error: %s" % resp.text)


if __name__ == "__main__":
    main()