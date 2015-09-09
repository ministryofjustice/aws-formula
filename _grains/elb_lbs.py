#!/usr/bin/env python
import boto.ec2.elb
import boto.utils
import logging
import salt.log


# configure a logger in case we are running it directly from python
# (eg: command line or testing)
if not salt.log.is_logging_configured():
    salt.log.setup_console_logger()
log = logging.getLogger(__name__)


def get_elb_lbs():
    """
    Returns a dictionary of load balancer names as keys
    each with their respective attributes
    """

    # attributes to extract from the load balancer boto objects
    # this could possibly be a named argument too
    extract_attrs = ['scheme', 'dns_name', 'vpc_id', 'name', 'security_groups']

    try:
        instance_metadata = boto.utils.get_instance_metadata(timeout=5, num_retries=2)
    except Exception as e:
        log.exception("Error getting ELB names: {}".format(e))
        return {'custom_grain_error': True}

    # Setup the lbs grain
    lbs_grain = {'lbs': {}}

    # Collect details about this instance
    vpc_id = instance_metadata['network']['interfaces']['macs'].values()[0]['vpc-id']
    region = instance_metadata['placement']['availability-zone'][:-1]

    # Collect load balancers of this instance (in the same vpc)
    try:
        elb_connection = boto.ec2.elb.connect_to_region(region)

        # find load balancers by vpc_id
        all_lbs = [lb for lb in elb_connection.get_all_load_balancers()
                   if lb.vpc_id == vpc_id]
        log.debug('all lbs before filtering by instance id: {}'.format(all_lbs))

        # further filter the load balancers by instance id
        lbs = [lb for lb in all_lbs for inst in lb.instances
               if inst.id == instance_metadata['instance-id']]
        # initialise and populate the output of load balancers
        out = {}
        [out.update({l.name: {}}) for l in lbs]
        [out[l.name].update({attr: getattr(l, attr, None)})
         for attr in extract_attrs for l in lbs]

        if not out:
            # This loglevel could perhaps be adjusted to something more visible
            log.warning("No ELBs found for this instance, this is unusual, "
                        "but we will not break highstate")

        lbs_grain['lbs'] = out

    except Exception as e:
        # This prints a user-friendly error with stacktrace
        log.exception("Error getting ELB names: {}".format(e))
        return {'custom_grain_error': True}

    return lbs_grain

if __name__ == '__main__':
    print get_elb_lbs()
