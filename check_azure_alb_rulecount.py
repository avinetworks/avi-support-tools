from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.network import NetworkManagementClient

#Add parameters here before running the script.
#----------------------------------------------

auth_info = {}
auth_info['application_id'] = ''
auth_info['authentication_token'] = ''
auth_info['tenant_id'] = ''
auth_info['subscription_id'] = '' 
RG = ''
LB_NAME = ''

#--------------------------------------------

class Cleanup(object):
    def __init__(self):
        
        self.credentials = ServicePrincipalCredentials(
                client_id=auth_info['application_id'],
                secret=auth_info['authentication_token'],
                tenant=auth_info['tenant_id'],
                timeout=120)

        self.network_client = NetworkManagementClient(self.credentials, auth_info['subscription_id'])

    def get_load_balancer_rules(self):
        count = 0
        for rules in self.network_client.load_balancer_load_balancing_rules.list(RG, LB_NAME):
            count+=1
        print 'total rules are %s'%str(count)
        


obj = Cleanup()
obj.get_load_balancer_rules()

