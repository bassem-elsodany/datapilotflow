# Distributed File Polling

**_Enterprise Edition_**

Some connectors, such as the File connector or FTP connector, poll directories
and read certain files as they are created in the directories polled. These
files can reside on a remote file system, including file systems of nodes
belonging to a Mule High Availability (HA) Cluster.

In Mule 4, distributed file polling makes it possible to poll files in all
cluster nodes. Enabled by default, this feature is used by the following
connectors:

  * [File Connector](../../file-connector/latest/)

  * [FTP Connector](../../ftp-connector/latest/)

  * [SFTP Connector](../../sftp-connector/latest/)

You can configure connectors to only poll from the primary node,
`@PrimaryNodeOnly`, which ignores the default setting set by the Mule runtime
engine. This feature is only available in Mule 4.x

## See Also

  * [Creating and Managing a Cluster Manually](creating-and-managing-a-cluster-manually)

  * [Mule High Availability (HA) Cluster](mule-high-availability-ha-clusters)

  * [Migrating File Connector](migration-connectors-file)

  * [Migrating FTP and SFTP Connectors](migration-connectors-ftp-sftp)

