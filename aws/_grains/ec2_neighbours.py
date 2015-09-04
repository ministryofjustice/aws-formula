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
    aws_grain = {'aws':{'ec2':{}}}
    
    # Collect details about this instance
    current_ip = instance_metadata['local-ipv4']
    current_dns_name = instance_metadata['local-hostname']
    vpc_id = instance_metadata['network']['interfaces']['macs'].values()[0]['vpc-id']
    region = instance_metadata['placement']['availability-zone'][:-1]
    
    # Add this instances details to the grain
    aws_grain['aws']['ec2']['local_private_ip_address'] = current_ip
    aws_grain['aws']['ec2']['local_private_dns_name'] = current_dns_name
    
    # Collect neighbours of this instance (in the same vpc)
    try:
        ec2_conn = boto.ec2.connect_to_region(region)
        all_vpc_instances = ec2_conn.get_only_instances(filters={'vpc_id':vpc_id, 'instance-state-name': 'running'})
        vpc_instances = [i for i in all_vpc_instances if i.vpc_id == vpc_id and i.private_ip_address != current_ip ]
        aws_grain['aws']['ec2']['neighbours'] = current_ip = {str(i.private_ip_address): str(i.private_dns_name) for i in vpc_instances}
    except Exception as e:
      sys.stderr.write("Error getting VPC ips: {}".format(e))
      return {'custom_grain_error': True}
    
    return aws_grain

if __name__ == '__main__':
    print set_grain_instances_by_vpc()