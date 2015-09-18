#!/usr/bin/env python

import sys
import boto.ec2
import boto.cloudformation
import boto.ec2.autoscale
import boto.elasticache
from boto.utils import get_instance_identity, get_instance_metadata
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def get_elasticache_endpoints():
    """
    Get elasticache endpoints. 
    
    For redis types, this will consist of
    a primary (read-write) endpoint, a list of read-only endpoints,
    and a default endpoint. These endpoints will only be collected
    if there is already a grain ElasticacheReplicationGroupName
    containing the replication group name.
    
    Returns:
        For redis types, a dictionary containing the primary endpoint
        and a list of read endpoints. The default_endpoint is set to
        be the primary_endpoint.
        {
            'elasticache':  {
            'primary_endpoint': {'address': <address>, 'port': <port>},
            'default_endpoint': {'address': <address>, 'port': <port>},
            'read_endpoints': [
                {'address': <address>, 'port': <port>},
                {'address': <address>, 'port': <port>},
                {'address': <address>, 'port': <port>}
            ]
        }
    """
    # Collect together instance data
    try:
        instance_identity = boto.utils.get_instance_identity()
        instance_id = instance_identity['document']['instanceId']
        instance_region = instance_identity['document']['availabilityZone'].strip()[:-1]
        conn = boto.ec2.connect_to_region(instance_region)
        instance_data = conn.get_all_instances(
            instance_ids=[instance_id])[0].instances[0]
    except boto.exception.AWSConnectionError as e:
        log.error("There was a problem collecting instance data, '{}'").format(e.message)
        return {}
     
    # Collect together clouformation data
    try:   
        cf_conn = boto.cloudformation.connect_to_region(instance_region)
        stack_name = instance_data.tags['aws:cloudformation:stack-name']
        stack_outputs = cf_conn.describe_stacks(stack_name)[0].outputs
    except boto.exception.AWSConnectionError as e:
        log.error("There was a problem collecting Cloudformation data, '{}'").format(e.message)
        return {}

    outputs = {o.key: o.value for o in stack_outputs}
    if outputs.get('ElasticacheEngine', None) == 'redis':
        replication_group_id = outputs.get('ElasticacheReplicationGroupName', None)

        # If we have a redis  elasticache engine but no replication group then something is broken
        if not replication_group_id:
            log.error("Found elasticache engine 'redis' but no ElasticacheReplicationGroupName in AWS output grains")
            return {}
        log.info("Found elasticache engine 'redis' with group id '%s'" % (replication_group_id))

        # Try to get the replication group data from AWS 
        replication_group = None
        try:
            es_conn = boto.elasticache.connect_to_region(instance_region)
            # We're assuming one replication group with one node group in this setup
            replication_group = es_conn.describe_replication_groups(replication_group_id).get('DescribeReplicationGroupsResponse',{}).get('DescribeReplicationGroupsResult', {}).get('ReplicationGroups', [None])[0]
        except Exception:
            log.error("There was a problem connecting to AWS Elasticache")
            return {}
            
        if not replication_group:
            log.error("Could not find any replication group info on AWS for group id '%s'" % (replication_group_id))
            return {}
        
        # Check the replication group status.
        # In creation we go through 'creating'->'modifying'->'available'
        # Endpoints are ready only in the available stage, this is likely
        # to not be the case on first highstate, so we want to notify
        replication_group_status = replication_group.get('Status')
        if replication_group_status in ['creating', 'modifying', 'deleting']:
            log.error('The Elasticache replication group is not available yet, please update grains after AWS creation has completed.')
            return {}

        node_group = replication_group.get('NodeGroups', [None])[0]
        
        if not node_group:
            log.error("Could not find any node group info on AWS for group id '%s'" % (replication_group_id))
            return {}
            
        primary_endpoint = node_group.get('PrimaryEndpoint', {})
        read_endpoints = []
        for member in node_group.get('NodeGroupMembers', []):
            read_endpoint = member.get('ReadEndpoint', None)
            if read_endpoint:
                read_endpoints.append(read_endpoint)
        
        grain = {
            'elasticache':  {
                'default_endpoint': primary_endpoint,
                'primary_endpoint': primary_endpoint,
                'read_endpoints': read_endpoints
            }
        }
    else:
        log.info(("No known elasticache engine type found '%s'" ) % (outputs.get('ElasticacheEngine', None)))
        return {}
    
    return grain

if __name__ == '__main__':
    print get_elasticache_endpoints()
