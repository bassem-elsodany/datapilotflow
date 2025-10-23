# Deploy Applications to Runtime Fabric Using the Mule Maven Plugin

__ |  Mule Maven plugin versions 3.0.0, 3.1.0, 3.1.1, 3.1.2, 3.1.3, 3.1.4, 3.1.5, 3.1.6, 3.1.7, and 3.8.3 are deprecated.   
---|---  
  
__ |  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain terms to avoid any effect on customer implementations.  
---|---  
  
In addition to using Anypoint Runtime Manager, to deploy applications to
Anypoint Runtime Fabric, you can also deploy applications by using the Mule
Maven plugin. To do so, you must meet certain prerequisites, and configure
your Runtime Fabric deployment strategy in your project’s `pom.xml` file.

If you want to deploy applications to Runtime Fabric using a different method,
see:

  * [Deploy Applications to Runtime Fabric Using Runtime Manager](../../runtime-fabric/latest/deploy-to-runtime-fabric)

## Prerequisites

  * Ensure that the Mule Maven Plugin is added to your project

See [Add the Mule Maven Plugin to a Mule Project](mmp-concept#add-mmp) for
instructions.

  * You understand and have available the number of resources required to deploy to Runtime Fabric  
See [Allocating Resources for Application Deployment on Runtime
Fabric](../../runtime-fabric/latest/deploy-resource-allocation-self-
managed)for more information.

  * The application is already published in Exchange  
See [Publish and Deploy Exchange Assets Using Maven](../../exchange/to-
publish-assets-maven).

## Configure the Runtime Fabric Deployment Strategy

Inside the `plugin` element, add a configuration for your Runtime Fabric
deployment, replacing the following placeholder values with your Runtime
Fabric information:

    
    
    <plugin>
      <groupId>org.mule.tools.maven</groupId>
      <artifactId>mule-maven-plugin</artifactId>
      <version>3.7.1</version>
      <extensions>true</extensions>
      <configuration>
        <runtimeFabricDeployment>
          <uri>https://anypoint.mulesoft.com</uri>
          <muleVersion>4.3.0</muleVersion>
          <username>user</username>
          <password>pass</password>
          <applicationName>newapp</applicationName>
          <target>rtf</target>
          <environment>Sandbox</environment>
          <provider>MC</provider>
          <replicas>1</replicas>
          <properties>
            <key>value</key>
          </properties>
          <deploymentSettings>
            <enforceDeployingReplicasAcrossNodes>false</enforceDeployingReplicasAcrossNodes>
            <updateStrategy>recreate</updateStrategy>
            <clustered>false</clustered>
            <forwardSslSession>false</forwardSslSession>
            <lastMileSecurity>false</lastMileSecurity>
            <resources>
              <cpu>
                <reserved>20m</reserved>
                <limit>1500m</limit>
              </cpu>
              <memory>
                <reserved>700Mi</reserved>
              </memory>
            </resources>
            <http>
              <inbound>
                <publicUrl>url</publicUrl>
              </inbound>
            </http>
          </deploymentSettings>
        </runtimeFabricDeployment>
      </configuration>
    </plugin>

## Deploy to Runtime Fabric

From the command line in your project’s folder, package the application and
execute the deploy goal:

    
    
    mvn clean deploy -DmuleDeploy

### Exchange Snapshot Assets

You can also deploy Exchange snapshot assets into Runtime Fabric.

By using `SNAPSHOT` version assets in Anypoint Exchange during the development
and testing phase, you can avoid incrementing your application’s version
number for small changes. After your `SNAPSHOT` version application has been
overwritten in Anypoint Exchange, you can redeploy your `SNAPSHOT` version
application to Runtime Fabric via the Mule Maven plugin to deploy the latest
changes.

To learn more about publishing snapshot assets to Anypoint Exchange, see
[Asset Lifecycle State](../../exchange/to-publish-assets-maven#asset-
lifecycle-state).

__ |  Each time you update your application’s snapshot, redeploy the application to refresh it with the latest snapshot binaries. Because snapshot assets can change after deployment, avoid deploying them into your production environment.  
---|---  
  
## Redeploy to Runtime Fabric

To redeploy the application, run the same command as you did to deploy.  
Runtime Fabric rewrites the application you had deployed.

## Authentication Methods

When you deploy applications using Mule Maven plugin, you can use different
methods to provide your credentials to authenticate against the deployment
platform. Depending on the authentication method you use, the parameters to
set in the deployment configuration differ:

Authentication Method | Description | Configuration Parameters  
---|---|---  
Username and password |  Use a Runtime Fabric username and password to authenticate. | 

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

  
  
For a detailed description of the configuration parameters, see the Runtime
Fabric Deployment Parameters Reference.

## Runtime Fabric Deployment Parameters Reference

Parameter | Description | Required  
---|---|---  
`runtimeFabricDeployment` |  Top-Level Element |  Yes  
`uri` |  Your Anypoint Platform URI.  
If not set, defaults to https://anypoint.mulesoft.com. |  No  
`muleVersion` |  The Mule runtime engine version to run in your Runtime Fabric instance.   
Ensure that this value is equal to or higher than the earliest required Mule
version of your application. By default, the latest available Mule version is
selected.  
Example values: `4.6.0` selects the last build where it defaults to Edge
channel and Java 8. If you want to choose a different LTS or Edge selection or
Java version, specify the full Mule version name as in `4.6.0:1e-java17`.  
When using Mule Maven plugin versions 3.8.0 and 4.0.0 for deployments, the `muleVersion` property doesn’t allow you to specify `releaseChannel` and `javaVersion`. To specify these properties, upgrade the plugin to version 4.1.1 or later. |  No  
`releaseChannel` |  Set the name of the release channel used to select the Mule image. Supported values are `NONE`, `EDGE`, and `LTS`. By default, the value is set to `EDGE`. If the selected release channel doesn’t exist, an error occurs. |  No  
`javaVersion` |  Set the Java version used in the deploy. Supported values are `8` and `17`. By default, the value is set to `8`. If the selected Java version doesn’t exist, an error occurs. |  No  
`username` |  Your Anypoint Platform username |  Only when using Anypoint Platform credentials to login.  
`password` |  Your Anypoint Platform password |  Only when using Anypoint Platform credentials to login.  
`applicationName` |  The application name displayed in Runtime Manager after the app deploys. |  Yes  
`target` |  The Runtime Fabric target name where to deploy the app. |  Yes  
`provider` |  Provider MC (MuleSoft Control Plane) indicates that the deployment is managed through Anypoint Runtime Manager. Set to `MC` for Runtime Fabric. |  Yes  
`environment` |  Target Anypoint Platform environment.  
This value must match an environment configured in your Anypoint Platform
account, as shown here:  

    
    
    <environment>Sandbox</environment>

|  Yes  
`replicas` |  Specifies the number of replicas, or instances, of the Mule application to deploy. The maximum number of replicas per application is 16. |  Yes  
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
`secureProperties` |  Top-Level element  
Use the `secureProperties` top-level element to set properties for the Mule
application and instruct Runtime Fabric to encrypt the values before storing
them:

    
    
    <secureProperties>
      <key>value</key>
    </secureProperties>

For example:

    
    
    <secureProperties>
      <http.port>8081</http.port>
    </secureProperties>

|  No  
`skip` |  When set to `true`, skips the plugin deployment goal.  
Its default value is `false`. |  No  
`skipDeploymentVerification` |  When set to `true`, skips the status verification of your deployed app.  
Its default value is `false`. |  No  
`authToken` |  Specifies the authorization token to access the platform. You can use this authentication method instead of setting username and password.  
See [Identity Management](../../access-management/external-identity) for a list of supported single sign-on (SSO) types. |  Only when using an Authorization token to login.  
`connectedAppClientId` |  Specifies the Connected App `clientID` value. |  Only when using Connected Apps credentials to login.  
`connectedAppClientSecret` |  Specifies the Connected App secret key. |  Only when using Connected Apps credentials to login.  
`connectedAppGrantType` |  Specifies the only supported connection type: `client_credentials`. |  Only when using Connected Apps credentials to login.  
`deploymentSettings` |  Any of the parameters documented in deploymentSettings Reference |  No  
  
### deploymentSettings Parameters Reference

Parameter | Description  
---|---  
`enforceDeployingReplicasAcrossNodes` |  Enforces the deployment of replicas across different nodes. The default value is `false`. Configuration example:
    
    
    <deploymentSettings>
      <enforceDeployingReplicasAcrossNodes>false</enforceDeployingReplicasAcrossNodes>
    </deploymentSettings>  
  
`updateStrategy` |  | Accepted values | Description  
---|---  
`rolling` | Maintains availability by updating replicas incrementally. Requires one additional replica’s worth of resources to succeed.  
If `enforceDeployingReplicasAcrossNodes` is enabled, the maximum number of
replicas you can configure is one less than the total number of nodes.  
`recreate` | Terminates replicas before re-deployment. Re-deployment is quicker than `rolling` and doesn’t require additional resources.  
If `enforceDeployingReplicasAcrossNodes` is enabled, the maximum number of
replicas you can configure is equal to the number of nodes.  
  
The default value is `rolling`.

Configuration example:

    
    
    <deploymentSettings>
      <updateStrategy>recreate</updateStrategy>
    </deploymentSettings>  
  
`forwardSslSession` |  Enables SSL forwarding during a session. The default value is `false`. Configuration example:
    
    
    <deploymentSettings>
      <forwardSslSession>true</forwardSslSession>
    </deploymentSettings>  
  
`clustered` |  Enables clustering across two or more replicas of the application. The default value is `false`.  
Configuration example:

    
    
    <deploymentSettings>
        <clustered>true</clustered>
    </deploymentSettings>  
  
`lastMileSecurity` |  Enable Last-Mile security to forward HTTPS connections to be decrypted by this application  
This requires an SSL certificate to be included in the Mule application, and
also requires more CPU resources. The default value is `false`.  
Configuration example:

    
    
    <deploymentSettings>
        <lastMileSecurity>true</lastMileSecurity>
    </deploymentSettings>  
  
`resources` |  | `cpu` | `reserved` | Specifies the number of cores to allocate for each application replica. The default value is 0.5 vCores.  
---|---|---  
`limit` | Specifies the number of max cores to allocate for each replica of the application.  
If a `reserved` configuration is present, ensure that this value is equal or
higher.  
`memory` | `reserved` | Specifies the amount of memory to allocate for each application replica. The default value is 700 MB.  
`limit` | Specifies the maximum memory allocated per application replica. If a `reserved` configuration is present, ensure that this value is equal or higher.  
  
Configuration example:

    
    
    <deploymentSettings>
      <resources>
        <cpu>
          <reserved>20m</reserved>
          <limit>1500m</limit>
        </cpu>
        <memory>
          <reserved>700Mi</reserved>
        </memory>
      </resources>
    </deploymentSettings>  
  
`http` |  | `inbound` | `publicURL` | URL of the deployed application.  
---|---|---  
  
Configuration example using wildcard URL:

    
    
    <deploymentSettings>
      <http>
        <inbound>
          <publicUrl>myapp.example.com</publicUrl>
        </inbound>
      </http>
    </deploymentSettings>

Configuration example using single cert single URL:

    
    
    <deploymentSettings>
      <http>
        <inbound>
          <publicUrl>wwww.example.com/myapp</publicUrl>
        </inbound>
      </http>
    </deploymentSettings>

Configuration example for Runtime Fabric BYOK:

    
    
    <deploymentSettings>
      <http>
        <inbound>
          <publicUrl>https://www.example.com/myapp</publicUrl>
        </inbound>
      </http>
    </deploymentSettings>  
  
`persistentObjectStore` |  Configures the Mule application to use a persistent object store. By default, it is set to `false`.  
`jvm` |  | `args` | Specifies JVM arguments to pass to Runtime Fabric when deploying the application. Use spaces to separate each argument.  
---|---  
  
Configuration example:

    
    
    <deploymentSettings>
      <jvm>
        <args>
          -XX:MaxMetaspaceSize=500m -XX:MaxRAMPercentage=60.0
        </args>
      </jvm>
    </deploymentSettings>  
  
`generateDefaultPublicUrl` |  When this parameter is set to true, Runtime Fabric generates a public URL for the deployed application.  
`disableAmLogForwarding` |  Disables the application-level log forwarding to Anypoint Monitoring. By default, it is set to `false`.  
  
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
             <runtimeFabricDeployment>
               ...
               <server>my.anypoint.credentials</server>
               ...
             </runtimeFabricDeployment>
             ...
           </configuration>
           ...
         <plugin>

__ |  Make sure that the username and password are not set in the deployment configuration, or they will overwrite the defined server ID.   
---|---  
  

## See Also

  * [Mule Maven Plugin](mmp-concept)

