# Mule Runtime Engine Overview

Mule runtime engine (Mule) is a lightweight integration engine that runs Mule
applications and supports domains and policies. Mule applications, domains,
and policies share an XML DSL (domain-specific language).

## Mule Applications

Mule applications connect systems, services, APIs, and devices using API-led
connectivity instead of point-to-point integrations. Mule applications provide
functionality for message routing, data mapping, orchestration, reliability,
security, and scalability.

Anypoint Studio supports Mule application development.

## Mule Domains

Domains enable you to share global configurations that Mule applications need
to reuse, such as default error handlers, shared properties, scheduler pools,
and component configurations. You can only deploy domains when running Mule
runtime engine on premises.

See [Shared Resources](shared-resources) for information about developing and
configuring Mule domains by using Anypoint Studio.  
See [Deploy a Domain](deploy-on-premises#deploy-a-domain) for domain
deployment instructions.

## Policies

Policies on HTTP-based APIs can enforce security, regulate traffic through
Mule applications, and adapt APIs to your business needs.

Mule includes an embedded API Gateway, which enables you to apply security
policies to an API, enrich incoming or outgoing messages, and add capabilities
to an API without having to write any code.  
See [API Gateway Capabilities](../../mule-gateway/mule-gateway-capabilities-
mule4) for additional information.

API Manager supports the configuration of automated policies. Custom policy
development and configuration are also supported.

## Maven Support

Maven is a project management utility that Mule implements to enhance project
development. Mule provides built-in Maven functionality. For the Mule runtime
engine, you can integrate the packaging, testing, and deployment of your Mule
applications, domains, and custom policies with your Maven lifecycle using the
Mule Maven plugin.

For details, see [Maven Support in Mule](using-maven-with-mule).

## Mule Installation, Deployment, and Management

For a Mule app to run, it must be deployed to an environment where the Mule
runtime engine is installed.

Mule is packaged within the [Studio](../../studio/latest/) IDE and with
[Design Center](../../design-center/) on Anypoint Platform so that you can run
a Mule app as you design it.

MuleSoft provides different options for hosting the Anypoint Platform runtime
plane:

  * CloudHub 2.0

CloudHub 2.0 is a fully managed, containerized integration platform as a
service (iPaaS) where you can deploy APIs and integrations as lightweight
containers in the cloud.

CloudHub 2.0 provides for deployments across 12 regions globally, either
single or shared tenancy, and dynamically scales infrastructure and built-in
services up or down to support elastic transaction volumes. See [CloudHub
2.0](../../cloudhub-2/) for more information.

  * CloudHub 1.0

CloudHub is MuleSoft’s cloud-based environment for hosting the Mule runtime
server and related services. CloudHub enables you to deploy an API or a Mule
application on a platform that’s managed by MuleSoft.

CloudHub also provides high availability, clustering and failover of your APIs
and Mule applications and performs load balancing for them. See
[CloudHub](../../cloudhub/) for more information.

CloudHub can be managed only by version of the cloud control plane that exists
in the same environment (US cloud, EU cloud, or MuleSoft Government Cloud).

  * Runtime Fabric

Runtime Fabric is a container service that enables you to run Mule
applications and API gateways within a data center or third-party cloud
environment that you control and manage. You can install Runtime Fabric on a
set of physical servers, virtual machines, or within Amazon Web Services and
Microsoft Azure.

Runtime Fabric comes bundled with technology such as Docker and Kubernetes,
which offer benefits such as high availability, failover, clustering, and load
balancing. See [Anypoint Runtime Fabric Overview](../../runtime-
fabric/latest/) for more information.

Runtime Fabric can be managed only by Cloud control planes (US cloud, EU
cloud). MuleSoft Government Cloud and Anypoint Platform PCE do not support
Runtime Fabric.

  * Hybrid Standalone Runtimes

Hybrid standalone runtimes enable you to host the Mule runtime engine in an
environment you control. This model provides the control and security of
deployments within customer trust boundary combined with the flexibility,
scalability, and centralized management of cloud-based services.

With hybrid standalone runtimes, the Mule runtime engine can run on a physical
server, a virtual machine, or within a third-party cloud service like Amazon
Web Services (AWS) or Microsoft Azure.

  * Standalone Runtimes

Standalone runtimes are useful for isolated environments where connecting to
the internet or Anypoint Control Plane isn’t feasible. These environments
enable you to host Mule runtime engine on a single instance, such as a
physical server, virtual machine, or within a third-party cloud service like
AWS or Azure. This setup offers simplicity and control, but it requires that
you manually manage infrastructure tasks like high availability, failover,
clustering, and load balancing. No connection to Anypoint Control Plane is
required, and you manage these Mule instances entirely within your own
environment.

You can manage standalone runtimes by using cloud control planes (US Cloud, EU
Cloud, MuleSoft Government Cloud) or a customer-hosted control plane (Anypoint
Platform PCE).

In addition to using Runtime Manager, you can perform deployments and manage
Mule apps with [Anypoint CLI 3.x](../../anypoint-cli/latest/anypoint-platform-
cli-commands), which includes commands for deployments and a number of
Anypoint Platform use cases.

## See Also

  * [Mule Application Development](mule-app-dev)

  * [Domains](../../studio/latest/domain-support-concept)

  * [Policies](../../gateway/latest/flex-gateway-secure-apis)

  * [Mule Configuration XML](about-mule-configuration)

  * [Deployment Strategies](../../runtime-manager/deployment-strategies)

  * [Download, Install, Upgrade Mule](runtime-installation-task)

