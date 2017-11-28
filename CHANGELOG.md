## v1.0.0

* First major release 

## 0.10.0

Features:
* Add AWSlogs agent state

## v0.9.1

Fixes:
* Ensure standby is called when we dont get an eip

## v0.9.0

Features
* Add failover mode

## v0.8.2

Fixes:
* Fix broken logic on no available eips
* fix logger call typo
* Add critical logging

## v0.8.1

Fixes:
* fix level_no logging key typo

## v0.8.0

Features:
* Add error level number to logging
* Allow script to accept args
Fixes:
* Cleanup crontab
* Fix early exit on EIP association

## v0.7.2

Fixes:
* Fixup autoip logging

## Version 0.7.1

Fixes:
* Fix sls that installs boto3

## Version 0.7.0

Features:
* Add EIP associaton script
* Allow enabling standby mode on instances without EIPs

## Version 0.6.0

* Add python/grains script that will return True if instance is first in ASG

## Version 0.5.0

* Add custom grains containing the redis elasticsearch endpoints

## Version 0.4.0

* Adds elb grains to be used in zero downtime deployment

## Version 0.3.0

* Migrate back to using grain data

## Version 0.2.0

* Migrate from grains to pillar data 

## Version 0.1.0

* Initial version with ec2 grains
