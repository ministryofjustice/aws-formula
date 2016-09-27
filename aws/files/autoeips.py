#!/usr/bin/env python
import argparse
import boto.ec2.autoscale
import boto.ec2
import boto.utils
from boto.exception import EC2ResponseError
import boto3
import json
import logging
import sys


class AutoEIP(object):
    """
    Class to configure and control the automatic assigning of EIP's to instances.
    """
    filter_addresses = None
    ec2_connection = None
    asg_connection = None
    instance_metadata = None
    instance_id = None
    enable_standby_mode = None
    force = False

    def __init__(self,
                 filter_addresses,
                 enable_standby_mode=True,
                 log_level='INFO',
                 log_format='json',
                 log_file=None,
                 force=False):
        """
        Default constructor.
        """
        self.setup_logging(log_level=log_level,
                           log_format=log_format,
                           log_file=log_file)

        self.filter_addresses = filter_addresses
        self.enable_standby_mode = enable_standby_mode
        self.force = force

        self.instance_metadata = self.get_instance_metadata()
        self.instance_id = self.instance_metadata.get('instance-id')
        # Collect details about this instance
        vpc_id = (self.instance_metadata['network']
                  ['interfaces']
                  ['macs'].values()[0]
                  ['vpc-id'])
        region = (self.instance_metadata['placement']
                  ['availability-zone'][:-1]
                  )
        # Setup boto3
        boto3.setup_default_session(region_name=region)
        # Enable required connections
        self.ec2_connection = boto.ec2.connect_to_region(region)
        if self.enable_standby_mode:
            self.asg_connection = boto.ec2.autoscale.connect_to_region(region)

        if self.ec2_connection is None:
            self.logger.critical("Critical error getting EC2 conection...exiting")
            self.safe_exit(1)

    def update_association(self):
        """
        Check on the status of the EIP association for this instance and carry out
        the actions to ensure that the instance has one or is in the correct state
        if one is not available.

        Args:
            force(bool): True to associate an EIP even if we already have one, 
                 False to only associate an EIP if it doesnt have one.
        """
        instance_associations = self.get_instance_association()
        if len(instance_associations) < 1 or self.force:
            self.logger.info("Associating with any available eips in list {}"
                        .format(self.filter_addresses))
            filtered_eips = self.get_unassociated_eips()
            success = self.associate_eip(filtered_eips)
            if not success:
                self.logger.critical("There was a problem associating instance {} "
                                     "with an EIP".format(self.instance_id))
        else:
            self.logger.debug("Already associated with EIP: {}".format(
                instance_associations[0]))

    def get_instance_association(self):
        """
        Get the current EIP association of this instance.

        Returns:
            (list): List of boto.ec2.address.Address objects associated
            with this instance.
        """
        return self.ec2_connection.get_all_addresses(
            filters={'instance-id': self.instance_id})

    def get_instance_metadata(self):
        """
        Returns the instance metadata.

        Returns:
            instance_metadata(dict): Dictionary of instance metadata.
        """
        instance_metadata = boto.utils.get_instance_metadata(timeout=5,
                                                             num_retries=2)
        if instance_metadata is None:
            self.logger.critical("Critical error getting instance metadata, "
                            "exiting")
            self.safe_exit(1)
        return instance_metadata

    def associate_eip(self, eips, retries=3):
        """
        Try to associate an EIP with this instance

        Args:
            eips(list): List of ip address strings that will be
                attempted to associate with.
            retries(int): Number of times to retry associating with
                each eip address.

        Return:
            success(bool): True if association was successful, False otherwise.
        """
        if len(eips) < 1:
            self.logger.critical("There are no free eips available")
            return False
        for retry in range(retries):
            for eip in eips:
                self.logger.info("Associating instance: {} with eip: {}..."
                            .format(self.instance_id,
                                    eip.allocation_id)
                            )

                success = eip.associate(
                    instance_id=self.instance_id, allow_reassociation=False)
                # If the association was successful, update the standby mode and exit
                if success:
                    self.update_standby_mode(False)
                    return success
        logger.warning("Failed to associate with any EIP's")
        self.update_standby_mode(True)
        return False

    def get_unassociated_eips(self):
        """
        Get a list of unassociated EIP's out of the filtered list
        stored in the filter_addresses list variable.

        Returns:
             unassociated_eips(list): List of EIP's in filter_addresses
                 that are unassociated with any instance
        """
        # Disallow unrestricted association attempts,
        # filter addresses must be provided to prevent
        # over-greedy attempts on capturing EIP's
        if len(self.filter_addresses) < 1:
            self.logger.critical("No eip addresses specified, aborting...")
            self.safe_exit(1)
        try:
            eips = self.ec2_connection.get_all_addresses(
                addresses=self.filter_addresses)

            unassociated_eips = \
                [eip for eip in eips if eip.association_id is None]

            self.logger.info("Found {} eips: {}".format(len(eips), eips))
            self.logger.info("Found {} unassociated eips: {}"
                        .format(len(unassociated_eips),
                                unassociated_eips)
                        )

            return unassociated_eips

        except EC2ResponseError as e:
            # This prints a user-friendly error with stacktrace
            self.logger.critical("Error getting EIPS: {}".format(e.message))
            # If we're not associated already, we need to go into standby
            if len(self.get_instance_association()) < 1:
                self.update_standby_mode(True)
            self.safe_exit(exit_code=1)

    
    def update_standby_mode(self,
                            enable_standby):
        """
        Set the instance into standby mode or back into service. These
        actions will only be from InService -> Standby and back again,
        any other states are taken as failure and no change is made.

        Args:
            enable_standby(bool): True to put the instance in Standby mode
                if it isnt already, False to put it into InService, if it
                isnt already.

        Returns:
            (bool): True if the state was changed, false if otherwise.
        """
        # Dont't do anything if this mode is not enabled
        if not self.enable_standby_mode:
            self.logger.warning("Standby mode is not enabled, skipping")
            return False
        autoscaling_groups =  self.asg_connection.get_all_autoscaling_instances(
            instance_ids=[self.instance_id],
            max_records=None,
            next_token=None)

        if len(autoscaling_groups) <1:
            self.logger.critical("Cannot find autoscaling group for instance {}, aborting"
                            .format(self.instance_id))
            self.safe_exit(1)
        if len(autoscaling_groups) >1:
            self.logger.critical("Found multiple autoscaling groups for instance {}, aborting"
                            .format(self.instance_id))
            self.safe_exit(1)
        
        autoscaling_group_name = autoscaling_groups[0].group_name
        instance_lifecycle_state = autoscaling_groups[0].lifecycle_state

        # Connect to ASG through boto3 to use its enter_standby function
        asg_client = boto3.client('autoscaling')

        if enable_standby:
            if instance_lifecycle_state == 'InService':
                self.logger.warn("Enabling standby mode on instance {}, "
                            "this instance will receive no traffic.".format(self.instance_id))
                response = asg_client.enter_standby(
                    InstanceIds=[self.instance_id],
                    AutoScalingGroupName=autoscaling_group_name,
                    ShouldDecrementDesiredCapacity=True
                )
                self.logger.debug(response)
                return True
            else:
                self.logger.warn("Not enabling standby mode on instance {}, "
                            "instance state {} is not InService"
                            .format(self.instance_id,
                                    instance_lifecycle_state)
                            )
                return False
        else:
            if instance_lifecycle_state == 'Standby':
                self.logger.warn("Disabling standby mode on instance {}, "
                            "this instance will now serve traffic.".format(self.instance_id))
                # Connect to ASG through boto3 to use its enter_standby function
                response = asg_client.exit_standby(
                    InstanceIds=[self.instance_id],
                    AutoScalingGroupName=autoscaling_group_name
                )
                self.logger.debug(response)
                return True
            elif instance_lifecycle_state == 'InService':
                self.logger.info("Not disabling standby mode on instance {}, "
                            "instance state is already InService"
                            )
                return False
            else:
                self.logger.warn("Not disabling standby mode on instance {}, "
                            "instance state {} is not Standby"
                            .format(self.instance_id,
                                    instance_lifecycle_state)
                            )
                return False
        return False
            
    def safe_exit(self, exit_code):
        """
        Method to abstract a safe exit from the script to allow for variation
        in exit actions.

        Args:
            exit_code(int): The sys exit code to use.
        """
        sys.exit(exit_code)

    def setup_logging(self,
                      log_level='INFO',
                      log_format='json',
                      log_file=None):
        """
        Setup the logging
        """
        if log_format == 'json':
            logging_format_str = '{"timestamp": "%(asctime)s","name": "%(name)s", "level": "%(levelname)s", "level_no": %(levelno)s, "message": "%(message)s"}'
        else:
            logging_format_str = '%(asctime)s %(name)s: %(levelname)s: %(message)s'

        logging.basicConfig(
            format=logging_format_str,
            filename=log_file,
            level=log_level)
        # Set up the logging
        logging.basicConfig(format=logging_format_str,
                            level=logging.getLevelName(log_level))
        self.logger = logging.getLogger("aws:autoeips")
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger('boto').setLevel(logging.CRITICAL)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Associate instances with an EIP from a supplied list')
    )
    parser.add_argument('--eips',
                        dest='eips',
                        type=str,
                        help='JSON string list of EIPs to associate with',
                        required=True
                        )
    parser.add_argument('--enable-standby-mode',
                        dest='enable_standby_mode',
                        help='Enable automatically putting instances in and out of standby',
                        action='store_true'
                        )
    parser.add_argument('--log-level',
                        dest='log_level',
                        help=('Set the logging level, DEBUG/INFO/WARNING/ERROR/CRITICAL'),
                        default='INFO'
                        )
    parser.add_argument('--log-file',
                        dest='log_file',
                        help=('File to log to.'),
                        default=None
                        )
    parser.add_argument('--log-format',
                        dest='log_format',
                        help=('Logging format, json. default it simple text'),
                        default='json'
                        )
    parser.add_argument('--force',
                        dest='force',
                        help=('Force association of EIP addresses'),
                        action='store_true'
                        )
    args = parser.parse_args()
    #  Load EIP list from string
    try:
        eips_list = json.loads(args.eips)
    except ValueError as e:
        print("Error loading eip list, {}: {}"
              .format(e.message,
                      args.eips))
        sys.exit(1)
    autoeip = AutoEIP(filter_addresses=eips_list,
                      enable_standby_mode=args.enable_standby_mode,
                      log_level=args.log_level,
                      log_format=args.log_format,
                      log_file=args.log_file,
                      force=args.force
                      )
    
    autoeip.update_association()
    sys.exit(0)
