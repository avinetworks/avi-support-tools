#!/usr/bin/env python
#
# Created on May 23, 2018
# @author: antonio.garcia@avinetworks.com
#
# AVISDK based Script to import certificate.
#
# The script imports the content of the certificate files and install them in Avi Vantage
# It will accept certificate with private keys or not as well p12 certificated
# Accepts Certiciated with Password and No Password
#
# Requires AVISDK ("pip install avisdk")
# Usage:- python avi_import_cert.py -c <Controller-IP> -u <user-name> -p <password> -cf <cert-path> -n <name>
# Note:- This script was tested for Avi Controller version 17.2.4 onwards

#Imports...
from requests import urllib3
import json
import argparse
from os import path
from avi.sdk.avi_api import ApiSession
from requests.packages import urllib3
from OpenSSL import crypto

def main():
    parser = argparse.ArgumentParser(description="AVISDK based Script to import a a certificate based on tenant.")
    parser.add_argument("-u", "--username", required=False, help="Login username")
    parser.add_argument("-p", "--password", required=False, help="Login password") #Required
    parser.add_argument("-c", "--controller", required=False, help="Controller IP address") #Required
    parser.add_argument("-t", "--tenant", required=False, help="Tenant Name")
    parser.add_argument("-a", "--api_version", required=False, help="Api Version Name")

    parser.add_argument("-ck", "--certkey", required=False, help="Path of Certificate Key (Optional)")
    parser.add_argument("-cf", "--certfile", required=False, help="Path of Certificate File")
    parser.add_argument("-n","--name", required=False, help="Name of Certificate") #Required
    parser.add_argument("-cp","--certpwd", required=False, help="Certificate Password (If certificate type if p12 or pfx format.")

    args = parser.parse_args()

    user = args.username
    password = args.password
    controller = args.controller
    tenant = str([args.tenant if args.tenant else "admin"][0])
    api_version = str([args.api_version if args.api_version else "17.2.4"][0])

    certfile = args.certfile
    certkey = args.certkey
    certpwd = args.certpwd
    certname = args.name

    print "Starting Certificate Import"
    file_ext = path.splitext(certfile)[1]

    if file_ext == '.pfx' or file_ext == '.p12':
        print "-p12 Certificate Selected\r\n"
        certobj = crypto.load_pkcs12(open(certfile, 'rb').read(), certpwd if certpwd else "")
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, certobj.get_privatekey())
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, certobj.get_certificate())
    else:
        print "-Non-p12 Certificate Selected\r\n"
        certobj = crypto.load_certificate(crypto.FILETYPE_PEM,open(certfile, 'rb').read())
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, certobj)
        keyobj = crypto.load_privatekey(crypto.FILETYPE_PEM,open(certkey, 'rb').read(), certpwd if certpwd else "")
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, keyobj)

    print cert
    print key

    data = {"certificate":
        {
            "certificate": cert
        },
        "key": key,
        "name": certname,
        "key_passphrase": certpwd
    }

    #Get API Session Details
    urllib3.disable_warnings()
    api = ApiSession.get_session(controller, user, password, tenant=tenant, api_version=api_version)

    #Post Cerificate
    resp = api.post('sslkeyandcertificate',data=data)
    if resp.status_code in range(200, 299):
        print "Certificate Added Successfully"
        print json.dumps(json.loads(resp.text), indent=2)
        print "\n\n"
    else:
        print('Error in SSLKeyandCertificate :%s' % resp.text)
        exit(0)

if __name__ == "__main__":
    main()