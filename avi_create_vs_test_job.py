# Imports
import urllib3
import json
import argparse
from avi.sdk.avi_api import ApiSession

def main():

    controller = '10.52.0.2'
    user = 'admin'
    password = 'Avi12345!'
    tenant = 'admin'
    api_version = '18.2.3'
    maxcount = 25

    print "Starting Script"
    urllib3.disable_warnings()
    api = ApiSession.get_session(controller, user, password, tenant=tenant, api_version=api_version)
    print "Avi Networks Authentication Successful"

    count = 0
    while count < maxcount:
        vsname = 'test-vs-' + str(count)
        vsvip = 'test-vip-' + str(count)

        data = {
                "model_name": "VirtualService",
                "data": {
                    "name": vsname,
                    "pool_ref": "https://10.52.0.2/api/pool/pool-5f1ec987-d4a2-4346-a01c-2433e374c273#web.pool.server",
                    "application_profile_ref": "https://10.52.0.2/api/applicationprofile/applicationprofile-87c0d164-34ed-4afa-9cc5-e0620e994356#System-HTTP",
                    "enabled": True,
                    "services": [
                        {
                            "port": 80
                        }
                    ],
                    "vsvip_ref_data": {
                        "name": vsvip,
                        "vip": [
                            {
                                "auto_allocate_ip": True,
                                "enabled": True,
                                "auto_allocate_ip_type": "V4_ONLY",
                                "ipam_network_subnet": {
                                    "network_ref": "https://10.52.0.2/api/network/dvportgroup-1003-cloud-64d637c6-2e90-4a96-a8be-320f2c59b3a3#pg-70",
                                    "subnet": {
                                        "mask": 24,
                                        "ip_addr": {
                                            "type": "V4",
                                            "addr": "10.52.70.0"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }

        count = count + 1

        resp = api.post('macro', data=data)
        if resp.status_code in range(200, 299):
            print 'VS CREATED: %s' % vsname
        else:
            print 'ERR: %s' % resp.text


if __name__ == "__main__":
    main()
