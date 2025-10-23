# Prepare to Migrate to Mule 4

Mule 4 introduces many changes, so plan accordingly before attempting to
migrate from Mule 3.

## When to Start Using Mule 4

MuleSoft recommends that you develop all **new** projects on Mule 4, provided
that:

  * You and your team have updated your skills for Mule 4 through the documentation or formal training.

  * You have the proper deployment environment.

For projects deployed on Mule 3, use the Mule Migration Assistant (MMA) to
avoid re-creating the application in Mule 4.

Migrate your applications if any one of the following conditions is met:

  * The 3.x version you are using reaches end of life.

  * You want to make significant updates to the existing applications.

  * You want to take advantage of key Mule 4 capabilities.

  * You decide to upgrade all your apps to Mule 4 because your organization requires all apps to be on one version (for some on-prem scenarios).

## Setting up Your Local Development Environment

First, download and install Anypoint Studio 7. If the Mule version that comes
with Anypoint Studio does not match the Mule version you want to use for local
deployments, download the desired 4.x version of Mule runtime engine.

## Getting Ready to Deploy

Next, you need to make sure your deployment environment is ready. Depending on
which environment you have, different steps may be required.

Deployment Mechanism | Instructions  
---|---  
CloudHub | CloudHub is Mule 4 ready.  
Hybrid Deployment | Install Mule 4 on your servers.  
Anypoint Runtime Fabric | Runtime Fabric supports Mule 4.  
Anypoint Platform Private Cloud Edition (PCE) | PCE supports Mule 4.  
  
## Writing the Code

If you are performing a completely manual migration, you are ready to start
building and deploying Mule 4 applications. Simply review [Introduction to
Mule 4](intro-overview) topics to get an overview of the migration process and
understand changes introduced in Mule 4.

For guidance with an assisted migration using the Mule Migration Assistant
(MMA), it is important to review the [MMA documentation (on
GitHub)](https://github.com/mulesoft/mule-migration-
assistant/blob/master/docs/migration-intro.adoc#migration_process).

Important

    

**Mule Migration Assistant (MMA) is subject to the terms and conditions
described for[Community](https://www.mulesoft.com/legal/versioning-back-
support-policy#community) connectors. Additionally, Mule Migration Assistant
is distributed under the terms of the [3-Clause BSD
License](https://github.com/mulesoft/mule-migration-
assistant/blob/master/LICENSE.txt).**

