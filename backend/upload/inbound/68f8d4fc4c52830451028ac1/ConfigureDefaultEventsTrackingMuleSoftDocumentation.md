# Configure Default Events Tracking

Because event tracking requires processing and network overhead to aggregate
and store the events that Mule runtime engine generates, it is disabled by
default. However, you can enable and configure default events tracking for
connectors or message processors that support it, at one of two levels:

  * At the flow level

  * At the message processor (connector or component) level, which takes precedence over the flow-level setting

After you enable event tracking, customize the transaction ID to identify
specific tracked events so that you can analyze them at runtime.

## Flow-Level Event Tracking

Use this option in the [Flow](flow-component) component to enable default
event tracking for all elements in a flow that support event tracking. You can
disable tracking for specific processors or connectors to override the flow
level setting.

Steps to enable default events tracking for all components in a flow:

  1. Select your flow component to open the properties view.

  2. Enable default business events using either the UI or XML:

     * In the UI, select **Enable default events tracking** :

![A flow configuration interface for JMS processing with options to enable
event tracking](_images/mruntime-business-event-flow.png)

     * In the XML, add attribute `tracking:enable-default-events="true"` to the `flow` element:
           
           <flow name="testFlow" tracking:enable-default-events="true">

  3. Save your settings.

## Message Processor-Level Event Tracking

You can enable event tracking on individual connectors and Mule components
that support event tracking.

The following Mule components provide a configuration for enabling business
events:

  * [Choice](choice-router-concept) router

  * [Round Robin](round-robin) router

  * [First Successful](first-successful) router

Steps to enable default events tracking for an individual component:

  1. Open the connector or component properties view.

  2. Enable default business events using any of the following options:

     * In the UI, select **Enable default events tracking** :

![A business event tracking within a choice component](_images/mruntime-
business-event-component.png)

     * In the XML, add attribute `tracking:enable-default-events="true"` inside your component element:
           
           <flow name="flow">
             ...
               <choice doc:name="Choice" tracking:enable-default-events="true"/>
             ...
           </flow>

  3. Save your settings.

## Customize the Transaction ID

The Set Transaction Id component enables you to set an identifier for all
tracked events so that meaningful information, such as an order number, is
displayed for a transaction when analyzing tracked events at runtime, whether
using Anypoint Runtime Manager or CloudHub.

The transaction ID supports DataWeave expressions, which enables you to create
an ID dynamically and include information related to the event into the ID.

Follow these steps to set a transaction ID either in Anypoint Studio or by
editing the configuration XML:

  * In the Studio UI:

    1. Drag the **Set Transaction Id** component to your flow.

    2. In the **Set Transaction ID** configuration screen, set an ID value for the **Transaction ID** field:

![Configuration for setting a transaction ID in a Mule flow](_images/mruntime-
custom-transaction-id.png)

  * In the XML editor:

    * Add a child element to the `flow` element:
          
          <flow name="flow">
          ...
            <tracking:transaction id="#[payload.orderId]" />
          ...
          </flow>

## See Also

[Business Events](business-events)

