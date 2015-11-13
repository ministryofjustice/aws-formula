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


Run stuff once ASG group
########################

When asg.py runs on a node, it returns either True or False based on
whether the instance is the first instance of the ASG group.  When run
as a salt call or 0/1 as a standard return code when ran as a python
script.

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
