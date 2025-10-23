# Deploy Applications to CloudHub Using the Mule Maven Plugin

__ |  Mule Maven plugin versions 3.0.0, 3.1.0, 3.1.1, 3.1.2, 3.1.3, 3.1.4, 3.1.5, 3.1.6, 3.1.7, and 3.8.3 are deprecated.   
---|---  
  
__ |  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain terms to avoid any effect on customer implementations.  
---|---  
  
In addition to using Anypoint Studio, Anypoint Runtime Manager, or the
Anypoint Platform CLI to deploy applications to CloudHub, you can also deploy,
redeploy, or undeploy applications by using the Mule Maven plugin. To do so,
you must meet certain prerequisites, and configure your CloudHub deployment
strategy in your project’s `pom.xml` file.

If you want to deploy applications to CloudHub using a different method, see:

  * [Deploy Applications to CloudHub Using Anypoint Studio](../../studio/latest/deploy-mule-application-task)

  * [Deploy Applications to CloudHub Using the Anypoint CLI](../../anypoint-cli/latest/cloudhub-apps#deploy-to-cloudhub)

  * [Deploy Applications to CloudHub Using Runtime Manager](../../cloudhub/deploying-to-cloudhub)

## Prerequisites

Before you can deploy to CloudHub using the Mule Maven plugin, you must
complete the following tasks:

  * Add the Mule Maven plugin to your project

See [Add the Mule Maven Plugin to a Mule Project](mmp-concept#add-mmp) for
instructions.

  * If you are using the HTTP Listener as source for your flow, you need to set its host to **0.0.0.0** and its port to **${http.port}**

  * Declare all external classes and resources in the `exportedPackages` and `exportedResources` fields on the `mule-artifact.json` file

## Configure the CloudHub Deployment Strategy

Configure the CloudHub deployment strategy in your project’s `pom.xml` file so
you can deploy, redeploy and undeploy your Mule application using the Mule
Maven plugin.

Inside the `plugin` element in your project’s `pom.xml` file, configure your
CloudHub deployment, replacing the placeholder values with your CloudHub
information:

    
    
    <plugin>
      <groupId>org.mule.tools.maven</groupId>
      <artifactId>mule-maven-plugin</artifactId>
      <version>3.7.1</version>
      <extensions>true</extensions>
      <configuration>
        <cloudHubDeployment>
          <uri>https://anypoint.mulesoft.com</uri>
          <muleVersion>${app.runtime}</muleVersion>
          <username>${username}</username>
          <password>${password}</password>
          <applicationName>${cloudhub.application.name}</applicationName>
          <environment>${environment}</environment>
          <region>${region}</region>
          <workers>${workers}</workers>
          <workerType>${workerType}</workerType>
          <properties>
            <key>value</key>
          </properties>
        </cloudHubDeployment>
      </configuration>
    </plugin>

## Deploy to CloudHub

From the command line in your project’s folder, package the app and execute
the deploy goal:

    
    
    mvn clean deploy -DmuleDeploy

## Redeploy to CloudHub

To redeploy a Mule application using Mule Maven plugin, run `mvn clean deploy
-DmuleDeploy` as you did to previously deploy the app. CloudHub rewrites the
app you had deployed.

## Undeploy from CloudHub

To undeploy a Mule application using Mule Maven plugin, run the following
command:

    
    
    mvn mule:undeploy

The undeploy command also deletes the app in Mule Maven plugin 3.3.0 and later
versions.

## Authentication Methods

When you deploy applications using Mule Maven plugin, you can use different
methods to provide your credentials to authenticate against the deployment
platform. Depending on the authentication method you use, the parameters to
set in the deployment configuration differ:

Authentication Method | Description | Configuration Parameters  
---|---|---  
Username and password |  Use a CloudHub username and password to authenticate. | 

  * `username`  

  * `password`

  
Server |  Use credentials stored in a Maven server, configured inside the Maven `settings.xml` file. | 

  * `server`

  
Authorization Token |  Use an authorization token to access the platform.  
See [Identity Management](../../access-management/external-identity) for a list of supported single sign-on (SSO) types. | 

  * `authToken`

  
Connected Apps |  Use a Connected App to perform the authentication programmatically by communicating with Anypoint Platform.  
Note that the Connected App credentials must have the `Design Center
Developer` access scope.  
See [Connected Apps for Developers](../../access-management/connected-apps-developers) for instructions about creating Connected Apps. | 

  * `connectedAppClientId`  

  * `connectedAppClientSecret`  

  * `connectedAppGrantType`

  
  
For a detailed description of the configuration parameters, see the CloudHub
Deployment Reference.

## CloudHub Deployment Reference

The following table shows the available parameters to configure the CloudHub
deployment strategy in your project’s `pom.xml` file.

Parameter | Description | Required  
---|---|---  
`cloudHubDeployment` |  Top-level element |  Yes  
`uri` |  Your Anypoint Platform URI  
If not set, by default this value is set to https://anypoint.mulesoft.com. |  No  
`muleVersion` |  The Mule runtime engine version to run in your CloudHub instance.   
Ensure that this value is equal to or higher than the earliest required Mule
version of your application.  
Example value: `4.3.0`  
Starting with Mule 4.5, deployments to CloudHub accept the Mule version exact
name or the semantic versioning, which deploys the latest version of Mule
runtime.  
Example values: `4.6`, `4.6-e-java8` (Edge), `4.6-e-java17` (Edge),
`4.6-java8` (LTS), `4.6-java17` (LTS)  
When using Mule Maven plugin versions 3.8.0 and 4.0.0 for deployments, MuleSoft doesn’t guarantee support for LTS channel. We recommend that you use Mule Maven plugin version 4.1.1 or later. For example, specifying `<muleVersion>4.6-java17</muleVersion>` in the plugin 3.8.0 or 4.0.0 deploys the application with an Edge release channel and a Java 8 selection. To specify `releaseChannel` and `javaVersion`, upgrade the plugin to version 4.1.1 or later. |  Yes  
`releaseChannel` |  Set the name of the release channel to use for the selected Mule version. Supported values are `NONE`, `EDGE`, and `LTS`. If you don’t specify a Mule version, the default Mule version for the selected release channel is used. If the selected release channel doesn’t exist, an error occurs. |  No  
`javaVersion` |  Set the name of the Java version to use for the selected Mule version. Supported values are `8` and `17`. If you don’t specify a Mule version, the default Mule version for the selected Java version is used. If the Java version you select isn’t available for the specified Mule version, an error occurs. |  No  
`username` |  Your CloudHub username |  Only when using Anypoint Platform credentials to login.  
`password` |  Your CloudHub password |  Only when using Anypoint Platform credentials to login.  
`applicationName` |  The name of your application in CloudHub  
This name is part of the domain of your deployed app. For example, naming your application application-1 makes your app’s public domain application-1.cloudhub.io. |  Yes  
`artifact` |  The absolute path of the JAR file to be deployed  
If not set, the path defaults to the location of the JAR file generated at the package phase. |  No  
`environment` |  The CloudHub environment to which you want to deploy  
This value must match any environment configured in your CloudHub account.  

    
    
    <environment>Sandbox</environment>

|  Yes  
`properties` |  Top-Level element  
If you need to set properties for the Mule application you are deploying, you
can use the `<properties>` top-level element:

    
    
    <properties>
      <key>value</key>
    </properties>

For example:

    
    
    <properties>
      <http.port>8081</http.port>
    </properties>

|  No  
`workers` |  The number of workers  
By default, this value is 1. |  No  
`workerType` |  Size of each worker; one of the following values:

  * `MICRO` (default; 0.1 vCores)
  * `SMALL` (0.2 vCores)
  * `MEDIUM` (1 vCore )
  * `LARGE` (2 vCores)
  * `XLARGE` (4 vCores)
  * `XXLARGE` (8 vCores)
  * `4XLARGE` (16 vCores)

|  No  
`region` |  Region of worker clouds; one of the following values:

  * `us-east-1` (default; US East, N. Virginia)
  * `us-east-2` (US East, Ohio)
  * `us-west-1` (US West, N. California)
  * `us-west-2` (US West, Oregon)
  * `us-gov-west-1` (MuleSoft Government Cloud)
  * `eu-central-1` (EU, Frankfurt)
  * `eu-west-1` (EU, Ireland)
  * `eu-west-2` (EU, London)
  * `ap-southeast-1` (Asia Pacific, Singapore)
  * `ap-southeast-2` (Asia Pacific, Sydney)
  * `ap-northeast-1` (Asia Pacific, Tokyo)
  * `ca-central-1` (Canada, Central)
  * `sa-east-1` (South America, São Paulo)

|  No  
`objectStoreV2` |  Enables Object Store V2  
By default, this value is set to `true` to match the Runtime Manager configuration of OSv2. |  No  
`persistentQueues` |  Enables persistent queues  
By default, it is set to `false`. |  No  
`businessGroup` |  The Business group path of the deployment  
Specify the full hierarchical path from the parent organization to the target
Business group, for example:

    
    
    <businessGroup>ParentOrg\SubOrg1\myBusinessGroup</businessGroup>

This value is omitted if `businessGroupId` is set. If `businessGroup` and `businessGroupId` are not set, the value defaults to the main business group of the user. |  No  
`businessGroupId` |  The Business group ID of the deployment  
Instead of specifying the Business group path, you can specify the Business
group ID to deploy your application. If `businessGroupId` and `businessGroup`
are not set, the value defaults to the main business group of the user.  
The Business group ID is a mandatory parameter when you have access only to a
specific Business group but not to the parent organization.  
This parameter is available in plugin version 3.2.7 and later. |  No  
`deploymentTimeout` |  The allowed elapsed time, in milliseconds, between the start of the deployment process and the confirmation that the artifact has been deployed The default value is `1000000`. |  No  
`server` |  Maven server with Anypoint Platform credentials  
This is only needed if you want to use your credentials stored in your Maven `settings.xml` file. This is not the Mule server name. |  No  
`skip` |  When set to `true`, skips the plugin deployment goal.  
Its default value is `false`. |  No  
`skipDeploymentVerification` |  When set to `true`, skips the status verification of your deployed app.  
Its default value is `false`. |  No  
`authToken` |  Specifies the authorization token to access the platform. You can use this authentication method instead of setting username and password.  
See [Identity Management](../../access-management/external-identity) for a list of supported single sign-on (SSO) types. |  Only when using an Authorization token to login.  
`connectedAppClientId` |  Specifies the Connected App `clientID` value. |  Only when using Connected Apps credentials to login.  
`connectedAppClientSecret` |  Specifies the Connected App secret key. |  Only when using Connected Apps credentials to login.  
`connectedAppGrantType` |  Specifies the only supported connection type: `client_credentials`. |  Only when using Connected Apps credentials to login.  
`applyLatestRuntimePatch` |  When set to `true`, the plugin instructs CloudHub to update the worker to the latest available patch for the Mule runtime engine version specified in the deployment configuration, and then deploys the application.  
By default, it is set to `false`. |  No  
`disableCloudHubLogs` |  When set to `true`, the plugin instructs CloudHub to disable CloudHub logging and instead use the application configured in the `log4j2.xml` file.  
By default, it is set to `false`. |  No  
  
## Encrypt Credentials

To use encrypted credentials when deploying, you need to set up your Maven
master encrypted password and your `settings-security.xml` file.

  1. Create a master password for your Maven configuration.
         
         mvn --encrypt-master-password <yourMasterPassword>

Maven returns your master password encrypted:

         
         {l9vZ2uM5SdgHy+H12z4pX7LEOZn3Kbnqmt3kIquLjnQ=}

  2. Create a `settings-security.xml` file in your ~/.m2 repository and add your encrypted master password:
         
         <settingsSecurity>
           <master>{l9vZ2uM5SdgHy+H12z4pX7LEOZn3Kbnqmt3kIquLjnQ=}</master>
         </settingsSecurity>

  3. Encrypt your Anypoint platform password:
         
         mvn --encrypt-password <yourAnypointPlatformPassword>

Maven returns your Anypoint platform password encrypted:

         
         {HTWFGH5BG9QmvJ1B=}

  4. Add your encrypted Anypoint Platform password to your `settings.xml` file in the <server> section:
         
         <settings>
          ...
           <servers>
            ...
             <server>
               <id>my.anypoint.credentials</id>
               <username>my.anypoint.username</username>
               <password>{HTWFGH5BG9QmvJ1B=}</password>
             </server>
            ...
           </servers>
          ...
         </settings>

  5. In your configuration deployment, reference the credentials injecting the server ID configured in your `settings.xml` file:
         
         <plugin>
           ...
           <configuration>
             ...
             <cloudHubDeployment>
               ...
               <server>my.anypoint.credentials</server>
               ...
             </cloudHubDeployment>
             ...
           </configuration>
           ...
         <plugin>

__ |  Make sure that the username and password are not set in the deployment configuration, or they will overwrite the defined server ID.   
---|---  
  

## See also

  * [Mule Maven Plugin](mmp-concept)

  * [Export Resources](how-to-export-resources)

