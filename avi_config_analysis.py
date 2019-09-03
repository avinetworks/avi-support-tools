#!/usr/bin/env python
#
# Created on June 25, 2018
# @author: antonio.garcia@avinetworks.com
#
# This script allows the analysis the Avi setup. It will provide insight for sizing and also view of the customers configuration.

# Requirement ("pip install os.path,argparse,json,traceback, sys, code")
# Usage:- python config_analysis -f "path of avi_config file"
# Note:- The avi_config file can be found inside the tech support tar bundle when generated.

#Imports...

import traceback, sys, code
import json
import argparse
import os.path


def get_ref(obj, ref):
    if ref in obj and obj[ref]:
        x = obj[ref].split('name=')[1]
        if '&' in x:
            x = x.split('&')[0]
        return x
    else:
        return 'None'


def get_vs_stats(cdict):
    root_obj = {t['uuid']:
        {
            'tenant': get_ref(t, 'tenant_ref'),
            'cloud': get_ref(t, 'cloud_ref'),
            'enabled': t['enabled'],
            'type': t['type'],
            'ewplacement': False,
            'auto_allocate': False,
            'client_insights': False,
            'network_sec_policy_rules': 0,
            'http_sec_policy_rules': 0,
            'http_request_policy_rules': 0,
            'http_response_policy_rules': 0,
            'full_logs': False,
            'app_prof_compression': False,
            'app_prof_cache': False,
            'rate_limit': False,
            'real_time': False,
            'vs_childs': 0,
            'datascripts': 0,
            'waf_policy': False,
            'services': 0,
            'services_range': 0,
            'pool': 0,
            'pool_group': 0,
            'max_scaleout_per_vs': 0,
            'ipv6': 0,
            'vip_ref': 'None',
            'pool_ref': 'None',
            'pool_group_ref': 'None'
        } for t in cdict['VirtualService']}

    for v in cdict['VirtualService']:

        root_obj[v['uuid']]['type'] = v['type']

        if 'vh_child_vs_uuid' in v['extension']:
            root_obj[v['uuid']]['vs_childs'] = len(v['extension']['vh_child_vs_uuid'])

        if 'metrics_realtime_update' in v.get('analytics_policy', {}):
            root_obj[v['uuid']]['real_time'] = v['analytics_policy']['metrics_realtime_update']['enabled']

        if 'full_client_logs' in v.get('analytics_policy', {}):
            root_obj[v['uuid']]['full_logs'] = v['analytics_policy']['full_client_logs']['enabled']

        if 'client_insights' in v.get('analytics_policy', {}):
            if v['analytics_policy']['client_insights'] != 'NO_INSIGHTS':
                root_obj[v['uuid']]['client_insights'] = True

        if 'vsvip_ref' in v:
            obj = str(get_ref(v, 'vsvip_ref'))
            ref_obj = [x for x in cdict['VsVip'] if x['name'] == obj]
            root_obj[v['uuid']]['ewplacement'] = ref_obj[0]['east_west_placement']
            root_obj[v['uuid']]['auto_allocate'] = ref_obj[0]['vip'][0]['auto_allocate_ip']

            if 'vip' in ref_obj:
                for vip in ref_obj['vip']:
                    for ip in vip['ip_address']:
                        if ip['type'] == 'V6':
                            root_obj[v['uuid']]['ipv6'] += 1

        app_ref = get_ref(v, 'application_profile_ref')
        app_prof = [x for x in cdict['ApplicationProfile'] if x['name'] == app_ref][0]
        root_obj[v['uuid']]['app_prof_type'] = app_prof['type']
        root_obj[v['uuid']]['app_prof_name'] = app_prof['name']

        if 'compression_profile' in app_prof.get('http_profile', {}):
            root_obj[v['uuid']]['app_prof_compression'] = app_prof['http_profile']['compression_profile']['compression']

        if 'cache_config' in app_prof.get('http_profile', {}):
            root_obj[v['uuid']]['app_prof_cache'] = app_prof['http_profile']['cache_config']['enabled']

        if 'client_ip_connections_rate_limit' in app_prof.get('dos_rl_profile', {}).get('rl_profile', {}):
            root_obj[v['uuid']]['rate_limit'] = True

        net_ref = get_ref(v, 'network_profile_ref')
        net_prof = [x for x in cdict['NetworkProfile'] if x['name'] == net_ref][0]
        root_obj[v['uuid']]['net_prof_name'] = net_prof['name']

        ana_ref = get_ref(v, 'analytics_profile_ref')
        ana_prof = [x for x in cdict['AnalyticsProfile'] if x['name'] == ana_ref][0]
        root_obj[v['uuid']]['analytics_prof_name'] = ana_prof['name']

        if 'network_security_policy_ref' in v:
            network_sec_policy_ref = get_ref(v, 'network_security_policy_ref')
            network_sec_policy_obj = [x for x in cdict['NetworkSecurityPolicy'] if x['name'] == network_sec_policy_ref][
                0]
            root_obj[v['uuid']]['network_sec_policy_rules'] = (
                len(network_sec_policy_obj['rules']) if 'rules' in network_sec_policy_obj else 0)

        if 'http_policies' in v:
            for p in v['http_policies']:
                http_policy_ref = get_ref(p, 'http_policy_set_ref')
                http_policy_obj = [x for x in cdict['HTTPPolicySet'] if x['name'] == http_policy_ref][0]

                root_obj[v['uuid']]['http_sec_policy_rules'] = (
                    len(http_policy_obj['http_security_policy']['rules']) if 'rules' in http_policy_obj.get(
                        'http_security_policy', {}) else 0)

                root_obj[v['uuid']]['http_request_policy_rules'] = (
                    len(http_policy_obj['http_request_policy']['rules']) if 'rules' in http_policy_obj.get(
                        'http_request_policy', {}) else 0)

                root_obj[v['uuid']]['http_response_policy_rules'] = (
                    len(http_policy_obj['http_response_policy']['rules']) if 'rules' in http_policy_obj.get(
                        'http_response_policy', {}) else 0)

        root_obj[v['uuid']]['datascripts'] = len(v['vs_datascripts']) if 'vs_datascripts' in v else 0

        waf_ref = get_ref(v, 'waf_policy_ref')
        if waf_ref != 'None':
            root_obj[v['uuid']]['waf_policy'] = True

        root_obj[v['uuid']]['pool'] = (len(v['pool_ref']) if 'pool_ref' in v else 0)
        root_obj[v['uuid']]['pool_group'] = (len(v['pool_group_ref']) if 'pool_group_ref' in v else 0)
        root_obj[v['uuid']]['se'] = (
            len(v['extension']['vip_runtime'][0]['se_list']) if 'se_list' in v['extension']['vip_runtime'][0] else 0)
        root_obj[v['uuid']]['vip_ref'] = get_ref(v, 'vsvip_ref')
        root_obj[v['uuid']]['pool_ref'] = get_ref(v, 'pool_ref')
        root_obj[v['uuid']]['pool_group_ref'] = get_ref(v, 'pool_group_ref')

    return root_obj


def print_vs_stats(root_obj):
    # Print Virtual Service Scale Details
    print '\n\rTotal VirtualServices: %s (%s Enabled, %s Disabled, %s NS, %s EW, %s WAF) ' % (
        (len(root_obj),
         len([item for item in root_obj if root_obj[item]['enabled'] is True]),
         len([item for item in root_obj if root_obj[item]['enabled'] is False]),
         len([item for item in root_obj if root_obj[item]['ewplacement'] is False]),
         len([item for item in root_obj if root_obj[item]['ewplacement'] is True]),
         len([item for item in root_obj if root_obj[item]['waf_policy'] is True])
         ))


    print '- VS Types:'
    u_app_prof_type = set([root_obj[item]['app_prof_type'] for item in root_obj])
    for u in u_app_prof_type:
        print '   %s: %s' % (u, len([item for item in root_obj if root_obj[item]['app_prof_type'] == u]))

    print '- VIP: Auto Allocate: %s, Manual: %s' % (
        len([item for item in root_obj if
             'auto_allocate' in root_obj[item] and root_obj[item]['auto_allocate'] is True]),
        len([item for item in root_obj if
             'auto_allocate' in root_obj[item] and root_obj[item]['auto_allocate'] is False]))

    print '- IPv6 VIPs: %s' % sum(root_obj[item]['ipv6'] for item in root_obj)

    print '- SNI Parent: %s (Max Child VS on Parent: %s)' % (
        len([item for item in root_obj if root_obj[item]['type'] == 'VS_TYPE_VH_PARENT']),
        max([root_obj[item]['vs_childs'] for item in root_obj]))

    print '- Application Profiles: %s' % len([item for item in root_obj if 'app_prof_name' in root_obj[item]])
    u_app_prof = set([root_obj[item]['app_prof_name'] for item in root_obj])
    for u in u_app_prof:
        print '   %s: %s' % (str(u).lower(), len([item for item in root_obj if root_obj[item]['app_prof_name'] == u]))

    print '- Network Profiles: %s' % len([item for item in root_obj if 'net_prof_name' in root_obj[item]])
    u_net_prof = set([root_obj[item]['net_prof_name'] for item in root_obj])
    for u in u_net_prof:
        print '   %s: %s' % (str(u).lower(), len([item for item in root_obj if root_obj[item]['net_prof_name'] == u]))

    print '- Analytics Profiles: %s' % len([item for item in root_obj if 'analytics_prof_name' in root_obj[item]])
    print '- RT Metrics (Enabled): %s' % len([item for item in root_obj if root_obj[item]['real_time'] is True])
    print '- Full Client Logs (Enabled): %s' % len([item for item in root_obj if root_obj[item]['full_logs'] is True])
    print '- Client Insights (Enabled): %s' % len([item for item in root_obj if root_obj[item]['client_insights'] is True])
    print '- Compression (Enabled): %s' % len(
        [item for item in root_obj if root_obj[item]['app_prof_compression'] is True])
    print '- Cache (Enabled): %s' % len([item for item in root_obj if root_obj[item]['app_prof_cache'] is True])
    print '- Rate Limiters (Enabled): %s' % len([item for item in root_obj if root_obj[item]['rate_limit'] is True])

    print '- Network Security Policy: %s (Max Rules: %s)' % (
        len([item for item in root_obj if root_obj[item]['network_sec_policy_rules'] > 0]),
        max([root_obj[item]['network_sec_policy_rules'] for item in root_obj]))
    print '- HTTP Security Policy: %s (Max Rules: %s)' % (
        len([item for item in root_obj if root_obj[item]['http_sec_policy_rules'] > 0]),
        max([root_obj[item]['http_sec_policy_rules'] for item in root_obj]))
    print '- HTTP Request Policy: %s (Max Rules: %s)' % (
        len([item for item in root_obj if root_obj[item]['http_request_policy_rules'] > 0]),
        max([root_obj[item]['http_request_policy_rules'] for item in root_obj]))
    print '- HTTP Response Policy: %s (Max Rules: %s)' % (
        len([item for item in root_obj if root_obj[item]['http_response_policy_rules'] > 0]),
        max([root_obj[item]['http_response_policy_rules'] for item in root_obj]))
    print '- VS /w DataScripts: %s' % len([item for item in root_obj if root_obj[item]['datascripts'] > 0])
    print '- Services (Max in any VS): %s' % max(root_obj[item]['services'] for item in root_obj)
    print '- Pools (Max in any VS): %s' % max(root_obj[item]['pool'] for item in root_obj)
    print '- Pool Groups (Max in any VS): %s' % max(root_obj[item]['pool_group'] for item in root_obj)
    print '- Service Engines (Max in any VS): %s' % max(root_obj[item]['se'] for item in root_obj)

    u_pool_obj = set([root_obj[item]['pool_ref'] for item in root_obj])
    u_pool_obj = {t:
        {
            'count': 0
        } for t in u_pool_obj}

    for pool in u_pool_obj:
        u_pool_obj[pool]['count'] = len([item for item in root_obj if root_obj[item]['pool_ref'] == pool])

    print '- Pool Sharing (Max): %s' % max(u_pool_obj[item]['count'] for item in u_pool_obj if item != "None")

    u_pool_grp_obj = set([root_obj[item]['pool_group_ref'] for item in root_obj])
    u_pool_grp_obj = {t:
        {
            'count': 0
        } for t in u_pool_grp_obj}

    for pool_grp in u_pool_grp_obj:
        u_pool_grp_obj[pool_grp]['count'] = len(
            [item for item in root_obj if root_obj[item]['pool_group_ref'] == pool_grp])
    print '- Pool Group Sharing (Max): %s' % max(u_pool_obj[item]['count'] for item in u_pool_obj if item != "None")

    u_vip_obj = set([root_obj[item]['vip_ref'] for item in root_obj])
    u_vip_obj = {t:
        {
            'count': 0
        } for t in u_vip_obj}

    for vip in u_vip_obj:
        u_vip_obj[vip]['count'] = len([item for item in root_obj if root_obj[item]['vip_ref'] == vip])

    print '- VIP Sharing (Max): %s' % max(u_vip_obj[item]['count'] for item in u_vip_obj if item != "None")


def get_se_stats(cdict):
    root_obj = {t['uuid']:
        {
            'name': t['name'],
            'tenant': get_ref(t, 'tenant_ref'),
            'cloud': get_ref(t, 'cloud_ref'),
            'seg': get_ref(t, 'se_group_ref'),
            'vss': 0,
            'max_conn_per_server': 0,
            'request_queue': False,
            'request_queue_depth': 0,
            'hms': 0,
            'app_pers_prof': "NONE",
            'flavor': "NONE",
            'data_vnics': 0,
            'vss_list': []

        } for t in cdict['ServiceEngine']}

    for s in cdict['ServiceEngine']:
        if 'VirtualService' in cdict:
            for v in cdict['VirtualService']:
                if 'se_list' in v['extension']['vip_runtime'][0]:
                    for se in v['extension']['vip_runtime'][0]['se_list']:
                        if se['se_ref'] == s['uuid']:
                            root_obj[s['uuid']]['vss'] += 1
                            root_obj[s['uuid']]['vss_list'].append(v['uuid'])

        root_obj[s['uuid']]['data_vnics'] = (len(s['data_vnics']) if 'data_vnics' in s else 0)
        root_obj[s['uuid']]['flavor'] = s['flavor'] if s['flavor'] != "" else "NONE"
        root_obj[s['uuid']]['cores_per_socket'] = s['resources']['cores_per_socket'] if 'resources' in s else 0
        root_obj[s['uuid']]['memory'] = (s['resources']['memory'] / 1024) if 'resources' in s else 0

    return root_obj


def print_se_stats(root_obj):
    print '\n\rTotal Service Engines: %s' % len(root_obj)
    print '- Max VS in any SE): %s' % max(root_obj[item]['vss'] for item in root_obj)
    print '- Max Data NICs in any SE): %s' % max(root_obj[item]['data_vnics'] for item in root_obj)
    print '- Core Size (Min: %s, Max: %s)' % (min(root_obj[item]['cores_per_socket'] for item in root_obj),
                                              max(root_obj[item]['cores_per_socket'] for item in root_obj))
    print '- Memory (Min: %sGB, Max: %sGB)' % (
        min(root_obj[item]['memory'] for item in root_obj), max(root_obj[item]['memory'] for item in root_obj))
    print '- Number of Flavors of SE: %s' % len([item for item in root_obj if root_obj[item]['flavor'] != "NONE"])


def get_pool_stats(cdict):
    root_obj = {t['name']:
        {
            'servers': 0,
            'max_conn_per_server': 0,
            'request_queue': False,
            'request_queue_depth': 0,
            'hms': 0,
            'app_pers_prof': "NONE",
            'pool_ref': "NONE"

        } for t in cdict['Pool']}

    for p in cdict['Pool']:
        root_obj[p['name']]['servers'] = (len(p['servers']) if 'servers' in p else 0)
        root_obj[p['name']]['lb'] = p['lb_algorithm']

        if 'application_persistance_profile_ref' in p:
            app_pers_ref = get_ref(p, 'application_persistance_profile_ref')
            app_pers_obj = [x for x in cdict['ApplicationPersistenceProfile'] if x['name'] == app_pers_ref][0]
            root_obj[p['name']]['app_pers_prof'] = app_pers_obj['name']

        root_obj[p['name']]['max_conn_per_server'] = p['max_concurrent_connections_per_server']
        root_obj[p['name']]['request_queue'] = p['request_queue_enabled']
        root_obj[p['name']]['request_queue_depth'] = (
            p['request_queue_depth'] if p['request_queue_enabled'] is True else 0)
        root_obj[p['name']]['hms'] = (len(p['health_monitor_refs']) if 'health_monitor_refs' in p else 0)

    return root_obj


def print_pool_stats(root_obj):
    print '\n\rTotal Pools: %s' % len(root_obj)

    print '- Max Servers in Pools: %s' % max([root_obj[item]['servers'] for item in root_obj])

    print '- LB Algorithm Type:'
    u_lb_type = set([root_obj[item]['lb'] for item in root_obj])
    for u in u_lb_type:
        print '   %s: %s' % (u, len([item for item in root_obj if root_obj[item]['lb'] == u]))

    print '- Persistence Type:'
    u_pers_type = set([root_obj[item]['app_pers_prof'] for item in root_obj])
    for u in u_pers_type:
        print '   %s: %s' % (u, len([item for item in root_obj if root_obj[item]['app_pers_prof'] == u]))

    print '- Max Conn per Server: (Low %s, Max: %s)' % (
        min([root_obj[item]['max_conn_per_server'] for item in root_obj]),
        max([root_obj[item]['max_conn_per_server'] for item in root_obj]))
    print '- Request Queue: %s VS (Low %s, Max: %s)' % (
        len([item for item in root_obj if root_obj[item]['request_queue'] is True]),
        min([root_obj[item]['request_queue_depth'] for item in root_obj]),
        max([root_obj[item]['request_queue_depth'] for item in root_obj]))
    print '- Max HMs in Pools: %s' % max([root_obj[item]['hms'] for item in root_obj])


def get_tenant_stats(cdict):
    root_obj = {t['name']:
        {
            'clouds': 0,
            'vs': 0
        } for t in cdict['Tenant']}

    for i in cdict['Cloud']:
        obj = get_ref(i, 'tenant_ref')
        root_obj[obj]['clouds'] += 1

    if 'VirtualService' in cdict:
        for i in cdict['VirtualService']:
            obj = get_ref(i, 'tenant_ref')
            root_obj[obj]['vs'] += 1

    return root_obj


def print_tenant_stats(root_obj):
    print '\n\rTotal Tenants: %s' % len(root_obj)
    print '- Max Clouds in Tenant: %s' % max([root_obj[x]['clouds'] for x in root_obj])
    print '- Max VS in Tenant: %s' % max([root_obj[x]['vs'] for x in root_obj])


def get_cloud_stats(cdict):
    root_obj = {t['uuid']:
        {
            'tenant': get_ref(t, 'tenant_ref'),
            'name': t['name'],
            'vrf': len([i for i in cdict['VrfContext'] if get_ref(i, 'cloud_ref') == t['name']]),
            'vs': len([i for i in cdict['VirtualService'] if get_ref(i, 'cloud_ref') == t['name']]),
            'seg': len([i for i in cdict['ServiceEngineGroup'] if get_ref(i, 'cloud_ref') == t['name']]),
            'se': len([i for i in cdict['ServiceEngine'] if get_ref(i, 'cloud_ref') == t['name']]),
            'vtype': t['vtype']
        } for t in cdict['Cloud']}

    return root_obj


def print_cloud_stats(root_obj):
    print '\n\rTotal Clouds %s' % (len(root_obj))
    print '- Cloud-Type:'

    u_clouds = set([root_obj[item]['vtype'] for item in root_obj])
    for u in u_clouds:
        print '   %s: %s ' % (u, len([item for item in root_obj if root_obj[item]['vtype'] == u]))

    print '- Max VRF in Clouds: %s' % max(root_obj[x]['vrf'] for x in root_obj)
    print '- Max VS in Clouds: %s' % max(root_obj[x]['vs'] for x in root_obj)
    print '- Max SE-Group in Clouds: %s' % max(root_obj[x]['seg'] for x in root_obj)
    print '- Max SE in Clouds: %s' % max(root_obj[x]['se'] for x in root_obj)


def get_seg_stats(cdict):
    root_obj = {t['uuid']:
        {
            'name': t['name'],
            'tenant': get_ref(t, 'tenant_ref'),
            'cloud': get_ref(t, 'cloud_ref'),
            'min_scaleout_per_vs': (t['min_scaleout_per_vs'] if 'min_scaleout_per_vs' in t else 0),
            'max_scaleout_per_vs': (t['max_scaleout_per_vs'] if 'max_scaleout_per_vs' in t else 0),
            'auto_rebalance': (t['auto_balance'] if 'auto_balance' in t else 0),
            'extra_shared_config_memory': (t['extra_shared_config_memory'] if 'extra_shared_config_memory' in t else 0),
            'se': len([i for i in cdict['ServiceEngine'] if get_ref(i, 'se_group_ref') == t['name']]),
            'ha_mode': t['ha_mode']
        } for t in cdict['ServiceEngineGroup']}

    return root_obj


def print_seg_stats(root_obj):
    print '\n\rTotal SE Groups %s' % (len([root_obj]))
    print '- Max SE in SE Group: %s' % (x['se'] for x in root_obj)

    u_ha_mode = set([root_obj[item]['ha_mode'] for item in root_obj])
    for u in u_ha_mode:
        print '   %s: %s ' % (u, len([item for item in root_obj if root_obj[item]['ha_mode'] == u]))

    print '- Max (min_scaleout_per_vs) in SE Group: %s' % max(root_obj[x]['min_scaleout_per_vs'] for x in root_obj)
    print '- Max (max_scaleout_per_vs) in SE Group: %s' % max(root_obj[x]['max_scaleout_per_vs'] for x in root_obj)
    print '- Auto Re-Balance: %s' % str(
        'True' if len([item for item in root_obj if root_obj[item]['auto_rebalance'] == True]) > 0 else "False")
    print '- Extra Config Shared Memory: %s' % str('True' if len(
        [item for item in root_obj if root_obj[item]['extra_shared_config_memory'] > 0]) > 0 else "False")


def get_tenant_full_details(cdict, tenant_dict, cloud_dict, vs_dict, seg_dict, se_dict):
    print "\n\rConfiguration Details"

    for t in cdict['Tenant']:
        print '\n\rTenant: %s (Clouds: %s, VRF: %s, VS: %s, AA: %s, SNI-P: %s, SNI-C: %s, NS: %s, ES: %s)' % (
            t['name'], len([item for item in cloud_dict if cloud_dict[item]['tenant'] == t['name']])
            , len([item for item in cdict['VrfContext'] if get_ref(item, 'tenant_ref') == t['name']]) - len(
                [item for item in cdict['Cloud'] if get_ref(item, 'tenant_ref') == t['name']]),
            len([item for item in cdict['VirtualService'] if
                'VirtualService' in cdict and get_ref(item, 'tenant_ref') == t['name']]), len([item for item in vs_dict if
                                                                                            vs_dict[item]['tenant'] ==
                                                                                            t['name'] and vs_dict[item][
                                                                                                'auto_allocate'] is True]),
            len([item for item in vs_dict if
                vs_dict[item]['tenant'] == t['name'] and vs_dict[item][
                 'type'] == "VS_TYPE_VH_PARENT"]), len([item for item in vs_dict if
                                                        vs_dict[item]['tenant'] == t[
                                                            'name'] and
                                                        vs_dict[item][
                                                            'type'] == 'VS_TYPE_VH_CHILD']),
            len([item for item in vs_dict if
                vs_dict[item]['tenant'] == t['name'] and vs_dict[item][
                 'ewplacement'] is True]), len([item for item in vs_dict if
                                                vs_dict[item]['tenant'] == t['name'] and
                                                vs_dict[item][
                                                    'ewplacement'] is False]))

        for c in [item for item in cloud_dict if cloud_dict[item]['tenant'] == t['name']]:

            print '\n\rTenant: %s (Clouds: %s, VRF: %s, VS: %s, AA: %s, SNI-P: %s, SNI-C: %s, NS: %s, ES: %s)' % (
                t['name'], len([item for item in cloud_dict if cloud_dict[item]['tenant'] == t['name']])
                , len([item for item in cdict['VrfContext'] if get_ref(item, 'tenant_ref') == t['name']]) - len(
                    [item for item in cdict['Cloud'] if get_ref(item, 'tenant_ref') == t['name']]),
                len([item for item in cdict['VirtualService'] if
                     'VirtualService' in cdict and get_ref(item, 'tenant_ref') == t['name']]),
                len([item for item in vs_dict if
                     vs_dict[item]['tenant'] ==
                     t['name'] and vs_dict[item][
                         'auto_allocate'] is True]),
                len([item for item in vs_dict if
                     vs_dict[item]['tenant'] == t['name'] and vs_dict[item][
                         'type'] == "VS_TYPE_VH_PARENT"]), len([item for item in vs_dict if
                                                                vs_dict[item]['tenant'] == t[
                                                                    'name'] and
                                                                vs_dict[item][
                                                                    'type'] == 'VS_TYPE_VH_CHILD']),
                len([item for item in vs_dict if
                     vs_dict[item]['tenant'] == t['name'] and vs_dict[item][
                         'ewplacement'] is True]), len([item for item in vs_dict if
                                                        vs_dict[item]['tenant'] == t['name'] and
                                                        vs_dict[item][
                                                            'ewplacement'] is False]))

            print 'asdas'

        # ''   Cloud: %s (Clouds: %s, VS: %s, AA: %s, SNI-P: %s, SNI-C: %s, NS: %s, ES: %s' % (c['name'],


        for seg in [seg_dict[item] for item in seg_dict if seg_dict[item]['tenant'] == t['name']]:

            vss_list = []
            se_obj = [se_dict[item] for item in se_dict if
                      se_dict[item]['tenant'] == t['name'] and se_dict[item]['cloud'] == seg['cloud'] and se_dict[item][
                          'seg'] ==
                      seg['name']]

            for v in se_obj:
                vss_list += v['vss_list']

            print '\n\r- SE Group: %s (VS: %s)' % (seg['name'], len(set(vss_list)))

    print '\n\rDone'


def main():
    parser = argparse.ArgumentParser(description="Script to Export Configuration Summary")
    parser.add_argument("-f", "--file", required=False, help="Location of JSON formatted configuration file.")
    args = parser.parse_args()

    cfile = str([args.file if args.file else "avi_config"][0])

    try:
        if not os.path.isfile(cfile):
            print "The configuration file selected is not valid.\n\r"
            exit(1)

        with open(cfile, 'r') as f:
            cdict = json.load(f)

        tenant_dict = get_tenant_stats(cdict)
        print_tenant_stats(tenant_dict)

        cloud_dict = get_cloud_stats(cdict)
        print_cloud_stats(cloud_dict)

        seg_dict = get_seg_stats(cdict)
        print_seg_stats(seg_dict)

        if 'ServiceEngine' in cdict:
            se_dict = get_se_stats(cdict)
            print_se_stats(se_dict)

        if 'VirtualService' in cdict:
            vs_dict = get_vs_stats(cdict)
            print_vs_stats(vs_dict)

        if 'Pool' in cdict:
            pool_dict = get_pool_stats(cdict)
            print_pool_stats(pool_dict)

        print "\n\rCompleted"

    except Exception, err:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        last_frame = lambda tb=tb: last_frame(tb.tb_next) if tb.tb_next else tb
        frame = last_frame().tb_frame
        ns = dict(frame.f_globals)
        ns.update(frame.f_locals)
        code.interact(local=ns)


if __name__ == '__main__':
    main()
