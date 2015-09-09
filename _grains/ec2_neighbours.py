#!/usr/bin/env python
import boto.ec2
import boto.utils
import logging
import sys
  

def set_grain_instances_by_vpc():
    """
    Prints a mapping of private ip addresses to private dns names
    """
    try:
        instance_metadata = boto.utils.get_instance_metadata(timeout=5, num_retries=2)
    except Exception as e:
        sys.stderr.write("Error getting VPC ips: {}".format(e))
        return {'custom_grain_error': True}
    
    # Setup the aws grain
    ec2_local = {}
    
    # Collect local details about this instance
    ec2_local['private_ip_address'] = instance_metadata['local-ipv4']
    ec2_local['private_dns_name'] = instance_metadata['local-hostname']
    ec2_local['private_dns_name_safe'] =  ec2_local['private_dns_name'].split('.')[0].replace('.','-')
    ec2_local['vpc_id'] = instance_metadata['network']['interfaces']['macs'].values()[0]['vpc-id']
    ec2_local['region'] = instance_metadata['placement']['availability-zone'][:-1]
    
    
    # Collect neighbours of this instance (in the same vpc)
    ec2_neighbours = {}
    try:
        ec2_conn = boto.ec2.connect_to_region(ec2_local['region'])
        all_vpc_instances = ec2_conn.get_only_instances(
            filters={
                'vpc_id':ec2_local['vpc_id'],
                'instance-state-name': 'running'
            }
        )
        vpc_instances = [i for i in all_vpc_instances if i.vpc_id == ec2_local['vpc_id'] and i.private_ip_address != ec2_local['private_ip_address'] ]
        for i in vpc_instances:
            ec2_neighbours[str(i.private_ip_address)] = {
                'private_dns_name': str(i.private_dns_name),
                'private_dns_name_safe': str(i.private_dns_name).split('.')[0].replace('.','-')
            }
    except Exception as e:
      sys.stderr.write("Error getting VPC ips: {}".format(e))
      return {'custom_grain_error': True}
    
    return {
        'ec2_local': ec2_local,
        'ec2_neighbours': ec2_neighbours
    }
            

if __name__ == '__main__':
    print set_grain_instances_by_vpc()
