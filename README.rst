=====================
AWS Saltstack formula
=====================


Features
--------

* Creates grain details to summarise useful information on the current instance and vpc.


.. code-block::

  ec2_local:
    private_ip_address      # The local private ip address of the current EC2 instance
    private_dns_name        # The local private dns name of the current EC2 instance
    private_dns_name_safe   # The shortened safe version of the dns name 
  ec2_neighbours:           # A list of running EC2 instances within this vpc
        <ip-address>: 
            private_dns_name: <private_dns_name>
            private_dns_name_safe: <private_dns_name_safe>
