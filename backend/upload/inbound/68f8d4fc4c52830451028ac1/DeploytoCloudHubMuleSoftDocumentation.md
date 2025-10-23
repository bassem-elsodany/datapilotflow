# Deploy to CloudHub

You can deploy Mule applications to CloudHub using:

  * Anypoint Runtime Manager

  * Anypoint Studio

  * [Anypoint Code Builder](../anypoint-code-builder/int-deploy-mule-apps)

  * CloudHub CLI

  * [CloudHub API](https://anypoint.mulesoft.com/exchange/portals/anypoint-platform/f1e97bc6-315a-4490-82a7-23abe036327a.anypoint-platform/cloudhub-api/)

  * [Mule Maven plugin](../mule-runtime/latest/deploy-to-cloudhub)

You can also deploy an API proxy directly from API Manager to CloudHub. See
[Configure a Proxy and Deploy to CloudHub](../api-manager/latest/getting-
started-proxy#configure_and_deploy_to_cloudhub).

To be notified by email when an error occurs during deployment, set up a
**Deployment failed** alert. See [Create an Alert](../runtime-manager/alerts-
on-runtime-manager#create-an-alert).

## Deploy an Application from Runtime Manager

To deploy from Runtime Manager to CloudHub:

  1. Sign in to Anypoint Platform.

  2. Select **Runtime Manager**.

  3. In the **Applications** page, click **Deploy application**.

You see the **Deploy Application** page:

![Application Name field](_images/cloudhub-deploy-app.png)

  4. Provide a name for your application.

See Application Names.

  5. In the **Deployment Target** menu, select **CloudHub** , if it is not already selected.

  6. Specify the application file:

     * Import a file from Exchange:

       1. Click **Choose file** > **Import file from Exchange**.

       2. Select **Application** for the type.

       3. Enter the name of your application in the search box.

       4. Select the application to deploy, select a version from the **Version** menu, and then click **Select**.

     * Upload an application archive (ZIP or JAR) file:

       1. Select **Choose file** > **Upload file**.

       2. Select the file to upload and then click **Open**.

The application file size limit is 200 MB.

     * Copy an application from a nonproduction environment.

See Copy an Application from Sandbox to Production.

  7. Click tabs to configure application options.

See Configure Application Settings.

  8. Click **Deploy Application**.

## Deploy an Application from Studio

You can deploy your applications directly from Studio to CloudHub. This option
is helpful if you want to test your application while developing it.

__ |  You can deploy an application from Studio to any environment except **Design**.  
---|---  
  
To deploy from Studio to CloudHub:

  1. Open your application in Studio.

  2. In **Package Explorer** , right-click the project folder and select **Anypoint Platform > Deploy to CloudHub**.

  3. If this is your first time deploying from Studio, provide your Anypoint Platform credentials at the prompt.

Studio stores your credentials for future use. You can manage these
credentials by selecting **Anypoint Studio > Preferences > Anypoint Studio >
Authentication**.

After you sign in, you see the **Deploying Application** page:

![Application Name field and the Deploy Application button](_images/cloudhub-
deploy-app-studio.png)

Figure 1. The screenshot shows (**1**) the **Application Name** field, (**2**)
the **Deploy Application** button on the **Deploying Application** page.

  4. Change the application name, if necessary.

  5. Click tabs to configure application options.

See Configure Application Settings.

  6. Click **Deploy Application**.

## Deploy an Application from the Command Line

To deploy a Mule app from the CloudHub command-line interface (CLI):

  1. If you do not already have access to the Anypoint command-line tool, install it.

See [Anypoint Platform CLI](../anypoint-cli/latest/).

  2. Log into your Anypoint Platform account from the command line:

     1. Enter your username:

`anypoint-cli --username="user"`

     2. At the prompt, enter your password.

  3. Run the following command, replacing `myMuleApp` with the deployment name of your app and `/Users/exported-app-folder/my-mule-app.jar` with the path to the deployable archive (JAR or ZIP) file on your file system:
         
         runtime-mgr cloudhub-application deploy myMuleApp /Users/exported-app-folder/my-mule-app.zip

The command-line utility displays a table of deployment information:

         
         Deploying myMuleApp ...
         ┌──────────────────────────────┬────────────────────────────────────────┐
         │ Domain                       │ mymuleapp.cloudhub.io                  │
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ Status                       │ UNDEPLOYED                             │
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ Updated                      │ a few seconds ago                      │
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ Runtime                      │ 4.1.0                                  │
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ File name                    │ my-mule-app.zip                        │
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ Persistent queues            │ false                                  │
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ Persistent queues encrypted  │ false                                  │
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ Static IPs enabled           │ false                                  │
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ Monitoring                   │ Enabled. Auto-restart if not responding│
         ├──────────────────────────────┼────────────────────────────────────────┤
         │ Workers                      │ 1 vCore * 1                            │

After you deploy the app on CloudHub, you can view and manage it on Runtime
Manager.

  4. If you want to stop the app from the command line, run the following command, replacing `app-name` with the deployment name of your app:

`runtime-mgr cloudhub-application stop app-name`

To exit the command-line tool, press Ctrl+c twice.

For a complete list of the commands, see [Anypoint Platform CLI](../anypoint-
cli/latest/).

## Copy an Application from Sandbox to Production

If you create and test an application in a sandbox environment, you must move
it to the production environment before deploying it. You must have the
CloudHub Admin role to move applications between environments.

To avoid name conflicts, rename the application before you deploy it to
another environment.

Runtime Manager prevents you from duplicating applications in a single
environment, so you cannot move an application into the environment it’s
already in. If you want to duplicate an application in a single environment,
rename the filename of one application before you deploy it.

To move an application from sandbox to production:

  1. Sign in to Anypoint Platform.

  2. Select **Runtime Manager** and switch to your production environment.

See [Switch Environments Using Runtime Manager](../runtime-manager/runtime-
manager-switch-env#switch-environments-using-runtime-manager).

  3. In the **Applications** page, click **Deploy application**.

You see the **Deploy Application** page:

![Application Name field and Get from sandbox and Deploy Application
buttons](_images/cloudhub-deploy-app-sandbox.png)

  4. Provide a unique name for your application in production and click **Get from sandbox**.

This button is unavailable if no nonproduction environment exists.

  5. Select your sandbox environment and then the application that you want to move to production.

Only applications that are deployed to CloudHub appear in the list because you
can move only apps that are currently deployed to CloudHub to other CloudHub
workers. For example, you can’t move an app that is currently deployed on a
local server to CloudHub.

  6. If you want to copy the environment variables and Mule version from the source application, select **Merge environment variables and mule version**.

If your source application contains safely hidden application properties, you
must redefine them in the **Properties** tab. For information about safely
hidden application properties, see [Safely Hide Application
Properties](secure-application-properties).

  7. Click **Apply**.

  8. Click tabs to configure application options.

See Configure Application Settings.

  9. Click **Deploy Application**.

## Application Names

The application name can contain between 3 and 42 alphanumeric characters
(a-z, A-Z, 0-9) and dashes (-). They cannot contain spaces or other
characters.

__ |  You cannot change the name of an app after you deploy it. To change the name, you must delete and redeploy the app using the new name.   
---|---  
  
The application name identifies your application not only in Runtime Manager
but also in the public `cloudhub.io` domain. For example, an application named
`myapplication` is accessible at `http://myapplication.cloudhub.io`.

To avoid domain conflicts, the application name must be globally unique across
CloudHub. For this reason, create a naming convention to ensure unique
application names. For example, you could prepend your company name and
department to all application names, such as `mycompany-mydept-myapplication`.
You can then add DNS records to hide the complex application name. For
example, you might route requests to `myapplication.mycompany.com` to
`mycompany-mydept-myapplication.cloudhub.io`.

Using the CloudHub dedicated load balancer, you can also implement mapping
rules to set your application’s public URL to any other path, as long as you
own the domain. See [Mapping Rules](lb-mapping-rules).

## Configure Application Settings

You can configure the application deployment by clicking the tabs on the
**Deploy Application** page:

![Configuration tabs on the Deploy Application page](_images/cloudhub-deploy-
app-config-tabs.png)

Figure 2. The arrow shows the configuration tabs on the **Deploy Application**
page.

  * Runtime

  * Autoscaling

  * Properties

  * Insight

  * Logging

  * Static IPs

### Runtime Tab Settings

The **Runtime** tab includes the following settings:

Release Channel

    

Starting with Mule 4.5, MuleSoft introduces two new release channels, [Edge
and Long-term Support (LTS)](../release-notes/mule-runtime/lts-edge-release-
cadence).

For new applications, the Edge channel is selected by default in the **Release
Channel** drop-down menu.

For existing applications using a legacy version, the **Release Channel**
drop-down list is selected as `None` by default. Use the **Release Channel**
drop-down list to select the desired release channel.

For existing applications using an Edge version, the **Release Channel** drop-
down list is selected as `Edge`. The **Runtime Version** dropdown list
indicates if there is an update available, as well as the previous, latest and
recommended version of the application. Use the **Release Channel** drop-down
list to change to a legacy version.

For existing applications using an Edge or an LTS version on extended support,
a warning message appears indicating the version’s EOL.

Runtime version

    

The runtime version must be the same Mule version used to develop your
application.

After you deploy the app, CloudHub automatically alerts you when updates for
the selected runtime version are available. See [CloudHub Runtime Continuous
Updates](cloudhub-app-runtime-version-updates).

__ |  After End of Extended Support for Mule runtime 4.3 and 4.4, Mule applications deployed to CloudHub or CloudHub 2.0 environments are stopped.   
---|---  
  
Java Version

    

Select the Java version for your application. For more information, visit
[Java Support](../general/java-support).

Worker size

    

See Worker Size and vCores.

Workers

    

When you deploy an application with more than one worker, CloudHub
automatically balances any incoming traffic load across your allocated
workers. See [Clustering](cloudhub-fabric).

Region

    

If you have global deployment enabled on your account, you can change the
deployment region.

When you change the region, the domain is automatically updated.

See [Regional Services](cloudhub-networking-guide#regional-services).

Automatically restart application when not responding

    

CloudHub automatically restarts your application when the monitoring system
discovers an issue.

See [Application Monitoring and Automatic Restarts](worker-monitoring).

Persistent queues

    

You can use persistent queues on your application to store data in an input
queue to disk. Persistent queues protect against message loss and enable you
to distribute workloads across a set of workers.

See [Manage Queues](managing-queues).

Before you can take advantage of persistent queueing, you must set up your
application to use queues.

See [Clustering](cloudhub-fabric).

Encrypt persistent queues

    

If you enable persistent queues, you can optionally encrypt the data stored in
the input queue on disk.

Use Object Store v2

    

Object Store v2 is enabled by default in Mule 4. In Mule 3, select this option
to access Object Store v2.

See [Object Store V2](../object-store/).

Enable Monitoring and Visualizer

    

Use Anypoint Monitoring and Visualizer for Mule applications running on
supported versions of Mule.

This feature is available only if your organization has the Anypoint
Integration Advanced package or a Titanium subscription to Anypoint Platform.
For more information, see the [Pricing and Packaging](../general/pricing)
documentation.

See [Anypoint Monitoring](../monitoring/) and [Anypoint
Visualizer](../visualizer/).

### Autoscaling Tab Settings

Autoscaling enables you to define policies that respond to CPU or memory usage
thresholds by scaling up or down the processing resources used by an
application.

This tab doesn’t appear by default. See [Autoscaling in CloudHub](autoscaling-
in-cloudhub) for information.

### Properties Tab Settings

On the **Properties** tab, you can specify properties (key-value pairs) that
the application uses during deployment and while running.

__ |  When you deploy an application from a nonproduction environment (**Get from sandbox**), the new application inherits any properties defined in the original application. You can update these properties as required on the **Properties** tab before deploying the application.   
---|---  
  
For more information about specifying properties, including hiding them in
Runtime Manager, see [Manage Properties for Applications on
CloudHub](cloudhub-manage-props) and [Safely Hide Application
Properties](secure-application-properties).

### Insight Tab Settings

You can enable the Insight analytics feature and specify metadata options on
the **Insight** tab. For information about using this tool, see
[Insight](../runtime-manager/insight).

### Logging Tab Settings

CloudHub stores activity logs, which you can view or download from Runtime
Manager. See [View Log Data](viewing-log-data).

You can configure the logging level (`DEBUG`, `WARN`, `ERROR`, or `INFO`) for
the application on the **Logging** tab.

Alternatively, you can configure logging by modifying the `level` value in the
`log4j2.xml` file. See [Configuring Custom Logging Settings](../mule-
runtime/latest/logging-in-mule#configuring-custom-logging-settings) and
[Apache Logging
Services](https://logging.apache.org/log4j/2.x/manual/configuration.html).

### Static IPs Tab Settings

Use the **Static IPs** tab to allocate a static IP address to your application
deployed in a specific region.

You can also preconfigure static IP addresses for multiple regions for
disaster recovery (DR) scenarios. If an application has static IP addresses
allocated in multiple regions, the static IP address is assigned when the
application is deployed to a new region.

If your application is already running, applying the static IP address change
restarts it using the newly applied static IP address.

By default, the number of static IP addresses allocated to your organization
is equal to twice the number of production vCores in your subscription and
appears under the **Use Static IP** checkbox.

If you need to free some of your static IP allocations, you can release unused
IP addresses from an application. To increase your allocation of static IP
addresses, contact your Customer Success Manager. For more information about
adding more static IPs, see [How to Request Additional Static IPs for your
Anypoint
Organization](https://help.salesforce.com/s/articleView?id=001121221&type=1).

## Worker Size and vCores

On each application, workers are responsible for executing the application
logic.

Worker sizes have different compute, memory, and storage capacities.

For information about worker size and vCores, see [CloudHub Workers](cloudhub-
architecture#cloudhub-workers).

## Change Settings of a Deployed Application

You can change most application settings after deploying an application to
CloudHub.

To edit the settings of a deployed application:

  1. On the **Applications** tab, select the application name.

  2. Click the **Settings** tab.

  3. Make your changes and click **Apply Changes**

CloudHub redeploys the application with zero downtime.

__ |  Cancelling a deployment and starting a new one for the same application before the cancellation is complete can lead to a one-to-three-minute downtime.   
---|---  
  
## Deployment Progress

When CloudHub uploads your application and begins deploying it, CloudHub
switches its user interface to the **Logs** view so that you can monitor
deployment progress.

The application status changes to `Deploying` to indicate the deployment is in
progress. When the deployment is complete, the application status changes to
`Started` and a message appears in the status area and in the logs to indicate
that the application is successfully deployed.

__ |  While you deploy an application on Mule runtime engine version 4.1.x and later, the [Gatekeeper](../mule-gateway/mule-gateway-gatekeeper#how-gatekeeper-works) mechanism works with [API Autodiscovery](../mule-gateway/mule-gateway-autodiscovery-overview) to help determine the readiness of a deployment. If Gatekeeper considers the application not ready within five minutes of deployment initiation, the application status is `Deploy failed`.   
---|---  
  
## Deployment Failure

If an error occurs and the application cannot be deployed, the application
status changes to `Deploy failed`. The **Logs** tab includes details on the
application deployment errors.

## See Also

  * [Manage CloudHub-Specific Settings](managing-cloudhub-specific-settings)

  * [Manage Applications on CloudHub](managing-applications-on-cloudhub)

  * [Application Status States](../runtime-manager/managing-deployed-applications#application_status_states)

  * [Monitor Applications](../runtime-manager/monitoring)

  * [Develop Applications for CloudHub](developing-applications-for-cloudhub)

  * [Anypoint Platform Command-Line Interface](../anypoint-cli/latest/)

  * [CloudHub REST API](cloudhub-api)

