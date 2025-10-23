# Configuring Components

![logo cloud IDE](../_/img/logos/deployment-cloud-ide.png) Cloud IDE

![logo desktop IDE](../_/img/logos/deployment-desktop-ide.png) Desktop IDE

**Open Beta Release** : The **cloud IDE is in open beta**. Any use of Anypoint
Code Builder in its beta state is subject to the applicable beta services
terms and conditions, available from the IDE.

Configure connectors and processors within your implementation and integration
projects from the canvas or configuration XML.

Common tasks include the following:

  * [Work with Code Snippets](int-work-with-code-snippets)

  * Add a Component to Your Project

  * [Configure Expressions](int-configure-dw-expressions)

  * Test a Connection Configuration

  * Import a Connector from Exchange

  * Open a Component in the Canvas from the XML Editor

## Before You Begin

  * Determine which connectors, processors, and snippets you intend to use.

When adding components, you can start from [code snippets](int-work-with-code-
snippets), the canvas, or the configuration XML for your app. You can
configure components from their configuration panels in the canvas or from the
XML. For reference documentation on specific connector and component
configurations, see [Reference](acb-reference).

  * Review [Get Familiar with the Basics](./#get-familiar-with-the-basics) to ensure that you are familiar with important concepts and features.

Understand the basics of Mule flows, the Mule event structure, including the
payload, attributes, and Mule variables. To transform data and add expressions
to your components, have some familiarity of the DataWeave language.

## Add a Component to Your Project

The following example illustrates basic configurations for adding components
to your project from the canvas, and the configuration XML. The example
assumes you are beginning with an empty integration project.

  1. In the Explorer, open the configuration XML file for your project:, such as `my-project-name.xml`.

![Canvas showing visual representation of Mule flow and the Mule configuration
file](_images/int-empty-canvas.png)

__**1** | The canvas provides space for a visual representation of your Mule flows or subflows.  
---|---  
__**2** | The configuration XML editor displays the configuration file for your Mule application.  
  
  2. Select **Build a Flow** from the canvas to create an empty flow within a Mule integration application.

  3. Change the default name of the flow from the canvas or from the configuration XML.

     * From the canvas

     * From the configuration XML

Click **Flow name1** to open the configuration panel for the Flow component,
change the flow name, and click the check mark to set the new name.

![Change name of flow through canvas.](_images/int-flow-name-ui.png)

Replace the default name of the flow (`name1`) with your flow name, such as
`getFlights`, for example:

    
    <flow name="my-flow" >
    
    </flow>

  4. Add a component to your project from the canvas.

For example, add the HTTP Listener component:

     1. In the canvas, click the ![](_images/icon-plus.png) (**Add component**) icon.

     2. In the **Add Component** panel, search for and select **Listener** from the **HTTP** results:

![Listener component highlighted in the Add Component section](_images/main-
tutorial-add-first-listener.png)

The configuration XML file now includes the XML for the HTTP Listener within
the `<flow/>` element, for example:

            
            <flow name="getFlights" >
              <http:listener path="mypath" config-ref="config-ref" doc:name="Listener" doc:id="rrjiqa" />
            
            </flow>

  5. Add another component, this time using the XML configuration menu.

For example, add the `<http:listener-config/>` component from a snippet.

For more information about snippets, see [Working with Code Snippets](int-
work-with-code-snippets).

     1. In the configuration XML, place your cursor before the opening `<flow>` tag, and type `http`.

Ensure that the cursor is not inside the `<flow/>` element.

     2. Type `http`, and select the `http:listener-config` snippet:

![http:listener-config snippet highlighted in the configuration XML
menu](_images/add-http-config-snippet.png)

The snippet adds the following code:

            
            <http:listener-config name="HTTP_Listener_config" >
              <http:listener-connection host="0.0.0.0" port="8081" />
            </http:listener-config>

     3. Notice that the Listener component in the canvas now displays an error:

![Listener error in the canvas](_images/int-canvas-error.png)

     4. To determine where the error is, select the processor in the canvas.

Anypoint Code Builder highlights its location within the configuration XML,
and you can mouse over the issue for more information, for example:

![Selecting configuration reference from configuration panel](_images/int-
select-listener-config.png)

     5. To fix the error, change the value of the `name` attribute in `http:listener-config` to match the name of the `config-ref` value in your `http:listener` configuration:
            
            <http:listener-config name="config-ref" >
              <http:listener-connection host="0.0.0.0" port="8081" />
            </http:listener-config>

The HTTP listener within your flow now references the HTTP listener
configuration, a global connection configuration that resides outside of the
flow. For more information about debugging, see [Debugging Mule
Applications](int-debug-mule-apps).

  6. Add another component to your flow.

For example, add a Set Payload component to your HTTP Listener operation:

     1. In the canvas, click the ![](_images/icon-plus.png) (**Add component**) icon.

     2. In the **Add Component** panel, search for and select **Set payload** from the **Transformer** results.

     3. In the canvas, click **Set payload** to open its configuration panel, and add a string value, DataWeave expression, Mule variable, or configuration property.

        * To add a string, type a value such as `my value`. For example:

![Adding string to Set Payload](_images/int-set-payload-config-string.png)

        * To add a DataWeave expression or a Mule variable as a value, such as `payload`, click **fx** (located before the field), and provide the value, for example:

![Adding expression to Set Payload](_images/int-set-payload-config-fx.png)

For more information about configuring DataWeave expressions, see [Configuring
DataWeave Expressions](int-configure-dw-expressions).

        * To add a configuration property as a value, type a value such as `${secure::mysensitiveprop}`. For example:

![Adding configuration property to Set Payload](_images/int-set-payload-
config-property.png)

For more information about configuration properties, see [Defining and
Securing Properties for a Mule Application](int-create-secure-configs).

Your configuration XML file now looks similar to the following:

    
    
    <http:listener-config name="config-ref" >
      <http:listener-connection host="0.0.0.0" port="8081" />
    </http:listener-config>
    
    <flow name="getFlights" >
      <http:listener path="path" config-ref="config-ref" doc:name="Listener" doc:id="rrjiqa" />
      <set-payload value="my value" doc:name="Set payload" doc:id="gecykt" />
    
    </flow>

## Import a Connector from Exchange

Anypoint Connectors provide operations for retrieving, modifying, and sending
data to and from systems. In addition to the [built-in connectors](acb-
reference#builtin-connectors) that Anypoint Code Builder provides, you can
download many other connectors from Anypoint Exchange.

  * Import a Connector from the Canvas

  * Import a Connector with a Command

## Import a Connector from the Canvas

To import a connector from Exchange and add it to your configuration:

  1. In the Explorer, open the configuration XML file for your project:, such as `my-project-name.xml`.

  2. Click ![](_images/icon-tree-view.png) (**Show Mule graphical mode**) in the activity bar to open the UI canvas if it doesn’t open automatically.

  3. Add the connector the same way you added other components from the canvas:

     1. In the canvas, click the ![](_images/icon-plus.png) (**Add component**) icon.

     2. In the **Add Component** panel, click **Connectors**.

     3. Click the connector name and then click the operation to add, such as **Publish** :

![Add Publish operation from the Anypoint MQ Connector](_images/int-add-
connector-operation.png)

     4. If the connector is not available locally, click the ![](_images/icon-search-exchange.png) (**Search in Exchange**) toggle:

![Search in Exchange toggle](_images/int-connector-search-exchange.png)

__**1** | Search locally  
---|---  
__**2** | Search in Exchange  
  
     5. Select the connector to add to your project.

     6. Select the operation from the **Add Component** panel.

## Import a Connector with a Command

To import a connector from Exchange to use later in your project:

  1. In the Explorer, open the configuration XML file for your project:, such as `my-project-name.xml`.

  2. Click ![](_images/icon-tree-view.png) (**Show Mule graphical mode**) in the activity bar to open the canvas if it doesn’t open automatically.

  3. Open the Command Palette.

Show me how

     * Use the keyboard shortcuts:

       * Mac: Cmd+Shift+p

       * Windows: Ctrl+Shift+p

     * In the desktop IDE, select **View** > **Command Palette**.

     * In the cloud IDE, click the ![](_images/icon-menu.png) (menu) icon, and select **View** > **Command Palette**.

  4. Select the following command:
         
         MuleSoft: Import Asset from Exchange

  5. Select **Connector**.

  6. Search for the connector name to import, such as "MQ," for example:

!["Import Anypoint MQ Connector from Exchange](_images/int-import-connect-
exchange.png)

  7. Select the connector.

  8. At the prompt, select the version of the connector to import, such as `v4.0.3`.

Anypoint Code Builder imports the connector and makes it available in the
Components list.

For more information about the connectors available on Exchange, see
[Connectors](../connectors/). For more information about Exchange, see
[Exchange (US)](https://anypoint.mulesoft.com/exchange/) or [Exchange
(EU)](https://eu1.anypoint.mulesoft.com/exchange/) and [Anypoint Exchange
Overview](../exchange/).

## Test a Connection Configuration

Most connectors provide an operation, such as the HTTP Listener operation,
that triggers the flow to start. These operations typically include connection
configurations that you can test.

## Test Connection from the Configuration Panel

You can test the connection from the connectors **Configuration** panel. For
example, to test an HTTP Listener connection:

![Configuration panel for connectors](_images/acb-configuration-panel-
test.png)

__**1** | Click the **+** icon on the connector to open the configuration panel.  
---|---  
__**2** | After filling in the required fields, click **Test Connection**.  
  
The status bar shows the progress:

  * **Verifying connection** indicates that the test is in progress.

  * **Connection is valid** indicates a successful connection.

  * **Invalid Connection Got status code: 500 when trying to resolve a Mule Runtime operation** indicates a connection error.

## Test Connection from the Configuration XML

You can test the connection from the configuration XML. For example, to test
an HTTP Listener connection, click **Test Connection** in the configuration
XML:

![HTTP Listener Test Connection link in the configuration XML](_images/http-
listener-test-connection.png)

The status bar shows the progress:

  * **Verifying connection inbound-request** indicates that the test is in progress.

  * **Connection is valid** indicates a successful connection.

  * **Invalid Connection Got status code: 500 when trying to resolve a Mule Runtime operation** indicates a connection error.

A common code `500` error is `port 8081: Address already in use`. For port
conflicts, configure a different port, such as `8082`, and retest the
connection.

Before publishing, run your application in debug mode.

## Open a Component in the Canvas from the XML Editor

You can open a component and its configuration panel in the canvas from the
XML editor. This feature is helpful, for example, if you want to configure the
component from the UI, if a component is in another flow than the flow
currently displayed in the canvas, or if the canvas is not open.

  1. From the configuration XML, place your cursor within the component’s XML.

  2. Right-click and select **Configure Component in UI**.

This action displays the component in the canvas and opens its configuration
panel, for example:

![Opening a component in the canvas from the XML](_images/acb-open-component-
ui-from-xml.png)

## Connection Configuration Panel

Use the Connection Management Configuration Panel to easily configure
connections to third-party systems directly from the UI.

In this panel, you can create, edit, delete, and test connections directly
within the ACB interface, automatically populate connection fields using
metadata provided by the connector, and save and manage connection
configurations without switching to the XML view.

To open the configuration panel:

  * Click on an existing component, or add a new one.

  * Click the **+** icon.

This action displays the configuration panel, for example:

![Configuration panel for connectors](_images/acb-configuration-panel-
general.png)

From here, you can:

  * Configure a connection for this project.

You can select a previously saved connection in the **Connection** field and
the form is pre-populated with existing configuration data.

__ |  Changes impact all components using this connection.   
---|---  
  
  * Update connection details without manually editing the XML code.

  * Test the connection directly within the panel to verify it’s correctly configured.

The test functionality helps prevent errors by allowing users to confirm that
the connection is valid before committing changes.

  * Delete an existing connection if it’s no longer needed.

A confirmation message shows any affected components that use the connection.

  * View all components that depend on a connection.

