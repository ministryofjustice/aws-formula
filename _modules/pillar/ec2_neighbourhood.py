# -*- coding: utf-8 -*-
"""
Retrieve EC2 neighbourhood data for minions.

.. code-block:: yaml

    ext_pillar:
      - ec2_neighbourhood: {}

This is a pillar that retrieves the EC2 ip data within the same VPC.
"""

# Import python libs
from __future__ import absolute_import
from distutils.version import StrictVersion  # pylint: disable=no-name-in-module
import logging
import sys

# Import AWS Boto libs
try:
    import boto.ec2
    import boto.utils
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

# Set up logging
log = logging.getLogger(__name__)

def __virtual__():
    '''
    Check for required version of boto and make this pillar available
    depending on outcome.
    '''
    if not HAS_BOTO:
        return False
    boto_version = StrictVersion(boto.__version__)
    required_boto_version = StrictVersion('2.8.0')
    if boto_version < required_boto_version:
        log.error("%s: installed boto version %s < %s, can't retrieve instance data",
                __name__, boto_version, required_boto_version)
        return False
    return True

def ext_pillar(minion_id,
               pillar,
			   *args,
			   **kwargs):
	ec2_local = _get_ec2_local()
	ec2_neighbours = _get_ec2_neighbours(ec2_local['vpc_id'], ec2_local['region'], ec2_local['private_ip_address'])
	ec2_data = {"ec2_neighbours": ec2_neighbours, "ec2_local": ec2_local}
	return ec2_data

def _get_ec2_local():
	instance_metadata = boto.utils.get_instance_metadata(timeout=5, num_retries=2)
    # Collect details about this instance
	current_ip = str(instance_metadata['local-ipv4'])
	current_dns_name = str(instance_metadata['local-hostname'])
    current_dns_name_safe = current_dns_name.split('.')[0].replace('.','-')
	vpc_id = str(instance_metadata['network']['interfaces']['macs'].values()[0]['vpc-id'])
	region = str(instance_metadata['placement']['availability-zone'][:-1])
	return {"private_ip_address": current_ip,
			"private_dns_name": current_dns_name,
			"private_dns_name_safe": current_dns_name_safe,
			"vpc_id": vpc_id,
			"region": region
		}

def _get_ec2_neighbours(vpc_id, region, local_ip):
    """
    Prints a mapping of private ip addresses to private dns names
    """
    # Collect neighbours of this instance (in the same vpc)
    ec2_conn = boto.ec2.connect_to_region(region)
    all_vpc_instances = ec2_conn.get_only_instances(filters={'vpc_id':vpc_id, 'instance-state-name': 'running'})
    vpc_instances = [i for i in all_vpc_instances if i.vpc_id == vpc_id and i.private_ip_address != local_ip ]
    neighbours = {}
    for i in vpc_instances:
       	neighbours[str(i.private_ip_address)] = {
            'private_dns_name': str(i.private_dns_name),
            'private_dns_name_safe': str(i.private_dns_name).split('.')[0].replace('.','-')
        }
    return neighbours
