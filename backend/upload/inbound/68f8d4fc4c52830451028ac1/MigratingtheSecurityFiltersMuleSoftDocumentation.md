# Migrating the Security Filters

__ |  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain terms to avoid any effect on customer implementations.  
---|---  
  
In Mule 3, the Security Filters where part of the Mule Module Security. In
Mule 4, this where migrated to the [Mule Validation Module](../../validation-
connector/latest/).

## IP filters

In mule 3 we had three different options to filter by IP: * `<filters:filter-
by-ip>` * `<filters:filter-by-ip-range>` * `<filters:filter-by-ip-range-cidr>`

### Filtering By one IP

Example: Filtering by one IP in Mule 3

    
    
    <filters:filter-by-ip regex="127.0.0.1"/>

This will filter those IPs that matches the regex. In mule4:

Example: Filtering by one IP in Mule 4

    
    
    <validation:is-blacklisted-ip blacklist="iplist" ip="#[vars.ip]">
    <validation:ip-filter-list>
    	<validation:ips>
    		<validation:ip value="127.0.0.1"/>
    	</validation:ips>
    </validation:ip-filter-list>

Where is necessary to set that `ip` variable (or whichever variable suits).

### Filtering by range of IPs

In mule 3, we had two ways of defining subnet mask to filter with:

Example: Filtering by IP range in Mule 3

    
    
    <filters:filter-by-ip-range net="127.0.0.1" mask="255.255.255.0"/>
    <!-- or -->
    <filters:filter-by-ip-range-cidr cidr="127.0.0.1/24"/>

Both are replaced by:

Example: Filtering by IP range in Mule 4

    
    
    <validation:is-blacklisted-ip blacklist="iplist" ip="#[vars.ip]">
    <validation:ip-filter-list>
    	<validation:ips>
    		<validation:ip value="127.0.0.1/24"/>
    	</validation:ips>
    </validation:ip-filter-list>

Where is necessary to set that `ip` variable (or whichever variable suits).

  1. _Are there other similar validations added in mule 4?_

Yes, there is also a WhiteList validation, which only allows IPs from a IP
Filter List.

## Time Expiration Filters

In mule 3 we could filter the message if it had elapsed some defined time from
a starting date. For example:

Example: Filtering by elapsed time in Mule 3

    
    
    <filters:filter-expired dateTime="#[vars.startingTime]" expiresIn="1000"/>

In Mule 4, this validation is in the validations module:

Example: Filtering by elapsed time in Mule 4

    
    
    <validation:is-not-elapsed time="1" timeUnit="SECONDS" since="#[vars.startingTime]"/>

  1. _Are there other similar validations added in mule 4?_

Yes, there is also a Time Elapsed validation, which validates if the time
elapsed has exceeded a certain amount of time.

## See Also

[Validation Connector Technical Reference](../../validation-
connector/latest/validation-documentation)

