=====================
AWS Saltstack formula
=====================


Features
--------


Local EC2 Data
##############


.. code-block::

  ec2_local:
    private_ip_address      # The local private ip address of the current EC2 instance
    private_dns_name        # The local private dns name of the current EC2 instance
    private_dns_name_safe   # The shortened safe version of the dns name 
  ec2_neighbours:           # A list of running EC2 instances within this vpc
        <ip-address>: 
            private_dns_name: <private_dns_name>
            private_dns_name_safe: <private_dns_name_safe>

  lbs:                      # A dictionary of {lb_name1:{attrs..}, {lb_name2:{attrs..}}
    <load-balancer-name>:   # A load balancer name that shares the same vpc_id as this instance
                            # and has this instance's instance_id in its "instances" list.
      dns_name:             # The dns name of the load balancer as taken from elb            
      name:                 # The load balancer resource name (short). This is the same
                            # as the <load-balancer-name> key name.
      scheme:               # The type of load balancer eg. internet-facing
      security_groups:      # A list of the load balancer's security groups 
      vpc_id:               # The vpc_id (also used to filter this instance's load balancers)


Elasticsearch Endpoints
#######################

Sets grains for elasticache endpoints for a redis type, consisting of a primary (read-write) endpoint,
and a list of read-only endpoints. These endpoints will only be collected if there is already a grain
ElasticacheReplicationGroupName containing the replication group name.

.. code::

   'elasticache':  {
     'primary_endpoint': {'address': <address>, 'port': <port>},
     'default_endpoint': {'address': <address>, 'port': <port>},
     'read_endpoints': [
       {'address': <address>, 'port': <port>},
       {'address': <address>, 'port': <port>},
       {'address': <address>, 'port': <port>}
     ]
   }
   
Auto EIP's
##########

By specifying a list of elastic ips in the pillar data and running the state `aws.autoeips`,
instances can be setup to automatically poll for available EIP's in the specified list, and,
if they do not have an EIP attached, associate with an available one. This can prove useful 
when there is a group of instances that need to be whitelisted in a firewall by IP, providing
a more resilient and automated solution than assigning EIP's manually.

.. code::

	aws:
		# A list of eips to attempt to associate with (required) 
		eips:
			- 1.2.3.4
			- 5.6.7.8
		# File path to autoeip log (optional)
		auto_eip_log: /var/log/autoeips.log
    # Level of logging output (optional)
    log_level': 'INFO'
			