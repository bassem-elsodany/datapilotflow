# CloudHub Overview

[CloudHub](http://www.mulesoft.com/cloudhub/ipaas-cloud-based-integration-
demand) is an integration platform as a service (iPaaS) where you can deploy
sophisticated cross-cloud integration applications in the cloud, create new
APIs on top of existing data sources, integrate on-premises applications with
cloud services, and much more.

## Create an Application for CloudHub

![app](_images/logo-app.png)

  * See [Deploy to CloudHub](deploying-to-cloudhub).

  * See [Build an HTTPS Service](../mule-runtime/latest/build-an-https-service) to include HTTPS support in this application.

__ |  For examples of more applications, see [Anypoint Exchange](../exchange/).   
---|---  
  
You can deploy the same Mule applications to CloudHub or to an [on-premises
server](../runtime-manager/deploying-to-your-own-servers). There are some
differences in how features work between the environments, which you need to
consider when you plan your deployment strategy. See [Deployment
Options](../runtime-manager/deployment-strategies).

## Deploy your Application to CloudHub

![deploy](_images/logo-deploy.png)

Learn how you can deploy your applications to CloudHub:

  * [Deploy to CloudHub](deploying-to-cloudhub)

  * [Anypoint Platform Command-Line Interface (CLI)](../anypoint-cli/latest/)

### Easy Scalability

CloudHub is an elastic cloud, meaning it scales on demand. You can start small
and scale up as your needs grow, without changing your applications or
experiencing downtime. CloudHub provides a scalable architecture – one on
which you can build integration applications, publish REST APIs, or Web
services, and much more.

### Integration with Anypoint Studio

Using [Anypoint Studio (Studio)](../studio/latest/), you can build integration
applications and deploy them to CloudHub with just a few clicks. You can then
access them like any other application deployed through the platform, by
[signing in to](http://anypoint.mulesoft.com) Anypoint Platform and then
navigating to Runtime Manager. See [Deploy an Application from
Studio](deploying-to-cloudhub#from-anypoint-platform).

### Integrate Cloud and Enterprise Applications

The CloudHub [Anypoint Virtual Private Cloud (Anypoint VPC)](virtual-private-
cloud) enables you to construct a secure pipe to on-premises applications
through an IPsec VPN tunnel, Anypoint VPC peering, a transit gateway, or AWS
Direct Connect.

### CloudHub API

To automate tasks or automatically deploy to CloudHub, use the [CloudHub
API](https://anypoint.mulesoft.com/exchange/portals/anypoint-
platform/f1e97bc6-315a-4490-82a7-23abe036327a.anypoint-platform/cloudhub-api).
This enables you to perform tasks such as manage and monitor your
applications, and scale your applications.

## Manage your Application

![manage](_images/logo-manage.png)

Learn how you can manage an application that is currently running in CloudHub:

  * [Manage Deployed Applications](../runtime-manager/managing-deployed-applications) has information about settings that are general to all applications—both those deployed to CloudHub and to on-premises servers.

  * [Manage Applications on CloudHub](managing-applications-on-cloudhub) has information about settings that are specific to applications on CloudHub.

### Manage Applications in Runtime Manager

Maintain your applications on CloudHub through the [Runtime
Manager](../runtime-manager/), an intuitive cloud console where you can
[manage](../runtime-manager/managing-deployed-applications) and
[monitor](../runtime-manager/monitoring) every aspect of your applications in
a centralized location.

__ |  You can view the live status and detailed service history for the Runtime Manager console, platform services, and the CloudHub worker cloud on [`status.mulesoft.com`](https://status.mulesoft.com/) for the US platform. For the EU platform, visit [`eu1-status.mulesoft.com`](https://eu1-status.mulesoft.com/).   
---|---  
  
## Monitor your Applications

![monitor](_images/logo-monitor.png)

Through various tools, Runtime Manager enables you to triage problems, view
logs, set up alerts, view dashboards, and more. See [Monitor
Applications](../runtime-manager/monitoring) for an overview on the different
ways that Runtime Manager enables you to monitor your running applications.

__ |  Heap dumps cannot be shared. Instead, our **Support Center** representatives can analyze the dumps and share the required information with you.   
---|---  
  
## Limitations

When deploying to CloudHub, keep in mind the following limitation:

  * CloudHub blocks outbound SMTP traffic when more than 20 emails are sent in one hour.

## See Also

  * [Deploy to CloudHub](deploying-to-cloudhub)

  * [Deployment Options](../runtime-manager/deployment-strategies)

  * [Develop Applications for CloudHub](developing-applications-for-cloudhub)

  * [CloudHub FAQ](cloudhub-faq)

  * [CloudHub Architecture](cloudhub-architecture)

  * [High Availability](cloudhub-fabric)

  * [CloudHub Networking Guide](cloudhub-networking-guide)

  * [Manage Deployed Applications](../runtime-manager/managing-deployed-applications)

  * [Manage Applications on CloudHub](managing-applications-on-cloudhub)

  * [Penetration Testing Policies](penetration-testing-policies)

  * [Cloud Security and Compliance Whitepaper](https://www.mulesoft.com/lp/whitepaper/saas/cloud-security)

  * [CloudHub Overview](http://www.mulesoft.com/cloudhub/ipaas-cloud-based-integration-demand)

