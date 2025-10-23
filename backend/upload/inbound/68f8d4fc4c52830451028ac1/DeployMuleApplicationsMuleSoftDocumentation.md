# Deploy Mule Applications

All Mule applications require deployment to a Mule runtime engine instance to
run. MuleSoft supports three different deployment targets: CloudHub, Anypoint
Runtime Fabric, and on-premises Mule instances.

When you deploy applications to CloudHub or to Anypoint Runtime Fabric, these
services automatically manage the Mule runtime engine instances needed to run
the applications.

If you deploy applications on-premises, the installation of Mule runtime
engine is required.  
See [On-Premises Deployment Model](mule-deployment-model) for more information
about characteristics specific to on-premises deployments.

In addition, different tools are available to deploy applications to each of
the deployment targets:

Deployment Target | Available Deployment Tools | Mule Runtime Engine Installation  
---|---|---  
CloudHub | 

  * Anypoint Studio
  * Anypoint Runtime Manager
  * Anypoint Platform CLI
  * Mule Maven plugin

|

  * No installation of Mule runtime engine is required, because CloudHub workers start Mule instances as part of the deployment process.

  
CloudHub 2.0 | 

  * Anypoint Studio
  * Anypoint Runtime Manager
  * Anypoint Platform CLI
  * Mule Maven plugin

|

  * No installation of Mule runtime engine is required, because CloudHub 2.0 replicas start Mule instances as part of the deployment process.

  
Anypoint Runtime Fabric | 

  * Anypoint Runtime Manager
  * Runtime Manager in Anypoint Platform Private Cloud Edition
  * Mule Maven plugin

|

  * No installation of Mule runtime engine is required, because Anypoint Runtime Fabric internally starts Mule instances as part of the deployment process.
  * Installation of Anypoint Runtime Fabric in your desired infrastructure is required

  
On-premises | 

  * Anypoint Studio
  * Anypoint Runtime Manager
  * Runtime Manager in Anypoint Platform Private Cloud Edition
  * Anypoint Platform CLI
  * Mule Maven plugin

|

  * Installation of Mule runtime engine in your desired infrastructure is required.
  * You are responsible for the installation and configuration of your Mule instances.

  
  
## See Also

  * [CloudHub](../../cloudhub/)

  * [CloudHub 2.0](../../cloudhub-2/)

  * [Anypoint Runtime Fabric](../../runtime-fabric/latest/)

  * [Anypoint Runtime Manager](../../runtime-manager/)

  * [Anypoint Platform Private Cloud Edition](../../private-cloud/latest/)

  * [Shared Resources](shared-resources)

  * [Mule High Availability Clusters](mule-high-availability-ha-clusters)

