import requests
import sys
requests.packages.urllib3.disable_warnings()

ctrl_IP = raw_input("Whats the leader controller IP address? ")
ctrl_usr = raw_input("Authentication (Username)? ")
ctrl_pwd = raw_input("Authentication (Password)? ")
lic_path = raw_input("Whats the local full path location of the license file? ")

if not ctrl_IP or not ctrl_usr or not ctrl_pwd or not lic_path:
    print("Warning: Not all details provided for script.")
    sys.exit(1)

try:
    file_obj=open(lic_path, "r")
    lic_data = file_obj.read()
except IOError as e:
        print("Error: The license file provided either does not exist or corrupted.")
        sys.exit(1)

try:
    login = requests.post('https://' + ctrl_IP + '/login', verify=False,data={'username': ctrl_usr, 'password': ctrl_pwd})
    login.raise_for_status()
except requests.exceptions.HTTPError as e:
    print e
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print e
    sys.exit(1)

try:
    head = {'X-CSRFToken': login.cookies['csrftoken'], 'Referer': 'https://' + ctrl_IP}
    resp = requests.put('https://' + ctrl_IP + '/api/license', verify=False, json={"license_text": lic_data},headers=head, cookies=login.cookies)
except requests.exceptions.RequestException as e:
    print e
    sys.exit(1)

json = resp.json()
print json['result']


