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


First instance in ASG group
###########################

When asg.py runs on a node, it returns either True or False based on
whether the instance is the first instance of the ASG group.  It returns
True/False when ran as salt call or 0/1 when run as python script.

The premise of asg.py is to provide a mechanism to define things that
have to run once per ASG group. Example:

.. code-block::
   
    # On first node of ASG group
    $ python /srv/salt-formules/_modules/asg.py && echo True
    True
    # On any other node of ASG group
    $ python /srv/salt-formules/_modules/asg.py && echo True
    $

The above could be used by shell scripts that run on the minions or
crontab entries.

Also, it can be used in salt states:

.. code-block::
   
    {% if salt['asg.is_first_of_asg_group']() == True %}
    postgresql-client:
      pkg.installed
    {% endif %}

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
    # Enable or disable the use of standby mode to add and remove 
    # instances automatically dependent on whether thay have 
    # acquired an EIP or not
    eip_enable_standby_mode: True
    # Enable or disable the use of failover mode to add and remove
    # instances automatically dependent on whether thay have
    # acquired an EIP or not. This is the same as stnadby mode but
    # does not alert.
    eip_enable_failover_mode: False


Note if the standby mode function is enabled, this requires an additional set of IAM permissions.
The following EC2 permissions are required.

.. code::

  "ec2:AssociateAddress",
  "ec2:DescribeAddresses",

The autoscaling permissions are required if the standby functionality is enabled.

.. code::

	"autoscaling:EnterStandby",
	"autoscaling:ExitStandby"

