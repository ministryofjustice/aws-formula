#!/usr/bin/env python

import sys
import boto.cloudformation
import boto.ec2
import boto.ec2.autoscale
from boto.utils import get_instance_identity
import logging
import operator

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def is_first_of_asg_group():
    """
    Returns True if the current instance is the first instance in the
    sorted by instance_id ASG group.

    XXX: some methods can be generalized and moved to a common.py file
    """
    # Collect together instance data
    try:
        instance_identity = get_instance_identity()
        instance_id = instance_identity['document']['instanceId']
        instance_region = instance_identity['document']['availabilityZone'].strip()[:-1]
        conn = boto.ec2.connect_to_region(instance_region)
        instance_data = conn.get_all_instances(
            instance_ids=[instance_id])[0].instances[0]
    except boto.exception.AWSConnectionError as e:
        log.error("There was a problem collecting instance data, '{}'").format(e.message)
        return False

    # my autoscaling group
    asg_group = instance_data.tags['aws:autoscaling:groupName']

    try:
        autoscale = boto.ec2.autoscale.connect_to_region(instance_region)
        group = autoscale.get_all_groups(names=[asg_group])[0]
        sorted_instances = sorted(group.instances, key=operator.attrgetter('instance_id'))
    except boto.exception.AWSConnectionError as e:
        log.error("There was a problem collecting instance data, '{}'").format(e.message)
        return False

    if sorted_instances[0].instance_id == instance_id:
        return True
    else:
        return False


if __name__ == '__main__':
    ret = is_first_of_asg_group()
    if ret:
        sys.exit(0)
    else:
        sys.exit(-1)
