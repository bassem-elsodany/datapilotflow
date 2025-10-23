# Getting Started

Anypoint Monitoring provides data on Mule apps that are running on either
CloudHub or an on-premises server. It is part of the Management Center in
Anypoint Platform, and you need to have the Required Permission to use it.

__ |  Functional Monitoring is covered in [API Functional Monitoring](../api-functional-monitoring/).   
---|---  
  
## Supported Versions of Mule Runtime Engine

Run your Mule app on a supported Mule runtime version. For supported versions,
see [Mule Runtime Release Notes](../release-notes/mule-runtime/mule-esb).

## Use Anypoint Monitoring

  1. Log in to Anypoint Platform with a user account that has [permission to access Anypoint Monitoring content](am-permissions).

  2. Navigate to **Anypoint Monitoring**.

If you do not see Anypoint Monitoring or are unable to use it, it might be a
permissions issue. See Required Permission.

  3. From Anypoint Monitoring, you can find and use the monitoring tools:

     * [Using Logs](logs)

     * [Alerts](alerts)

## Configurations

Custom dashboards and alerts require configuration before you can use them.
For guidance, see:

  * [Configuring Custom Dashboards](dashboard-custom-config)

  * [Configuring Alerts](alerts)

## Required Permission

To use Anypoint Monitoring, you need this permission:

  * Anypoint Monitoring User

Typically, administrators set permissions through Access Management. See
[Granting Permissions and Roles to Users](../access-management/users#granting-
permissions-and-roles-to-users).

## Enable Anypoint Monitoring on CloudHub

For Anypoint Monitoring to start monitoring your Mule apps, you must deploy
them to the appropriate version of Mule runtime engine. See [Configure
Anypoint Monitoring for Mule Apps (CloudHub)](configure-monitoring-cloudhub).

## Enable Anypoint Monitoring On-Premises

You can [install Anypoint Monitoring](am-installing) on an on-premises server
to monitor applications that are running on that server and managed via
Runtime Manager (hybrid apps).

## Access Key Metrics through the Anypoint Monitoring Agent

Access to [Key Metrics in API Manager](../api-manager/latest/analytics-chart)
relies on the Anypoint Monitoring agent. The agent is available by default for
some Mule app deployment models. Other models require enablement of Anypoint
Monitoring or installation of the agent.

Mule App Deployment Model | Action  
---|---  
CloudHub 1.0 | Enable Anypoint Monitoring for your Mule Apps. See [Setting Up Monitoring for CloudHub Deployments](configure-monitoring-cloudhub).  
CloudHub 2.0 | No action is required. Key Metrics and Anypoint Monitoring are available by default.  
Runtime Fabric | No action is required. Key Metrics and Anypoint Monitoring are available by default. See also, [Setting Up Monitoring for Runtime Fabric Deployments](monitor-applications-on-rtf) and [Supported Versions of Mule Runtime Engine](monitor-applications-on-rtf#supported-versions-of-mule-runtime-engine).  
Hybrid Deployments | Install the Anypoint Monitoring agent. See [Setting Up Monitoring for Hybrid Deployments](am-installing). If you proxy your monitoring data as it leaves the data center, you must configure the Anypoint Monitoring agent to communicate through the proxy. See [Proxy Settings](am-installing#proxy-settings).  
Standalone Deployments On-Prem | Key Metrics are not supported because standalone deployments are not managed in Anypoint Platform. If you require Key Metrics, convert your standalone deployment to a hybrid deployment (see [Add Servers to Runtime Manager](../runtime-manager/servers-create)), and install the Anypoint Monitoring agent (see Hybrid Deployments).  
  
## See Also

  * [Anypoint Monitoring Settings](monitoring-settings-page)

  * [Configure Anypoint Monitoring for Mule Apps](configure-monitoring-cloudhub)

  * [Install Anypoint Monitoring On-Premises](am-installing)

  * [Create a Monitor](../api-functional-monitoring/afm-create-monitor)

