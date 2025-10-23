# Introduction to Mule 4: Mule Message

Mule 4 includes a simplified Mule message model in which each Mule event has a
message and associated variables.  

  * A Mule message is composed of a payload and its attributes (metadata, such as file size).

  * Variables (`vars`) which hold arbitrary user information such as operation results, auxiliary values, and so on. In general, operations do not automatically propagate variables to other components, like a listener. Though, if you use the Flow Reference component it does propagate variables within flows.

This simplified message model makes it easier to work with data in a
consistent way across connectors without overwriting information.

![A Mule message including attributes, payload, and
variables](_images/mruntime-message-diagram.png)

Figure 1. Mule Event and Message.

## Inbound Properties Are Now Attributes

In Mule 3, inbound properties stored additional information about a payload
obtained through a Mule event source, such as the query parameters coming
through an HTTP listener. **Attributes** in Mule 4 replace inbound properties
and have these advantages:

  * They are strongly typed, so you can easily see what data is available.

  * They can easily be stored in variables that you can access throughout your flow. Here’s an HTTP listener example of a typical Mule Message in Mule 4:

![A Mule message showing types of attributes and payload](_images/mule-
message.png)

Attributes can be easily accessed through expressions, just as inbound
properties were in Mule 3, for example:

    
    
    #[attributes.requestPath]
    #[attributes.queryParams.searchCriteria]

When any Source or Operation produces a new Message as a result of its
execution, **both parts of the Message (the payload and attributes) are
replaced with the new values** , and the previous attributes are lost. If you
need to preserve any information from the attributes across operation
invocations, you can either store the previous attributes in a variable or
[set the `target` parameter in the invoked operation](target-variables).

Here is an example of how the Message is updated during the execution of a
flow:

    
    
    <flow name="messageExample">
      <http:listener config-ref="HTTP_Listener_config" path="/invoices"/> __**(1)**
      <logger level="INFO" message="#['New invoice from customer' ++ attributes.queryParams.customer_id]"> __**(2)**
      <set-variable name="requestAttributes" value="#[attributes]"> __**(3)**
      <jms:publish-consume config-ref="JMS_Config" destination="invoiceProcessor">
        <jms:message>
          <jms:body>#[output application/xml --- {
            data: payload,
            customer: attributes.queryParams.customer_id __**(4)**
          }]</jms:body>
        </jms:message>
      </jms:publish-consume> __**(5)**
      <jms:publish config-ref="JMS_Config" destination="eventTracker">
        <jms:message>
          <jms:body>#[output application/json --- {
            customer: requestAttributes.queryParams.customer_id, __**(6)**
            invoiceTrackingNumber: attributes.properties.userProperties.invoiceTrackingNumber
          }]</jms:body>
        </jms:message>
      </jms:publish>__**(7)**
      <logger level="INFO" message="#['Invoice accepted ' ++ attributes.properties.userProperties.invoiceTrackingNumber]"> __**(8)**
    </flow>

__**1** | A request is received, and the `http:listener` produces a Message with the request payload and the HTTP Attributes.  
---|---  
__**2** | Because the `logger` is a void operation and does not produce any output, the Message remains the same after its execution.  
__**3** | The example stores the current HTTP Attributes in a variable to make use of them later in the flow because the next operation will replace the current Message.  
__**4** | HTTP Attributes are still available to configure the `jms:publish-consume` operation input.  
__**5** | Once the `jms:publish-consume` is invoked, the output of the operation is a Message with a different payload and the JMS Attributes.  
__**6** | Since the HTTP Attributes are stored in a variable, it is possible to use both the current JMS Attributes (as `attributes`) and the previously stored HTTP information.  
__**7** | The `jms:publish` operation is also void. Because no output is produced, the Message remains unmodified.  
__**8** | At this point, JMS Attributes from the `jms:publish-consume` invocation still exist.  
  
## Outbound Properties

In Mule 3, Mule connectors and transports that need to send additional data,
such as headers, must explicitly specify Outbound properties. For example,
with the HTTP listener, you might want to specify the outgoing status code
response or headers. In Mule 4, you can set each of those separately using an
individual DataWeave expression for each one of them, without introducing any
side effects in the main flow:

    
    
    <http:request path="issues" config-ref="http" method="GET">
        <http:headers>#[{'path':'input/issues-list.json'}]</http:headers>
        <http:query-params>#[{'provider':'memory-provider'}]</http:query-params>
    </http:request>

The previous example performs an HTTP request in which individual DataWeave
scripts generate headers and query parameters without the need to set message
properties and without generating any side effects on the message.

The same concept can be applied for Mule event sources that emit responses,
such an HTTP listener:

    
    
    <http:listener config-ref="api-httpListenerConfig" path="/api/*" doc:name="Listener">
        <http:response statusCode="#[vars.httpStatus default 200]">
            <http:headers>#[vars.outboundHeaders default {}]</http:headers>
        </http:response>
        <http:error-response statusCode="#[vars.httpStatus default 500]">
            <http:body>#[payload]</http:body>
            <http:headers>#[vars.outboundHeaders default {}]</http:headers>
        </http:error-response>
    </http:listener>

In the previous example, `http:headers` settings like `vars.httpStatus default
200` set a default value for a variable if the actual value resolves to
`null`.

## Session Properties

Session properties are no longer needed and have been removed in Mule 4.
Instead, store data in target variables using the Target (`target`) parameter.

These properties are not needed because Mule 3 transports and their associated
transport barriers do not exist in Mule 4. Mule 3 transport barriers determine
how to handle Mule message data that moves through Mule 3 flows. Transports
are replaced by corresponding Mule connectors (such as the FTP connector) in
Mule 4, which handle networking transport protocols differently.

For examples, see [Migrating the Enricher to a Target Variable](migration-
core-enricher) and [Enrich Data with Target Variables](target-variables).

## Attachments

Inbound and outbound attachments have been removed. The affected connectors
now handle the attachment concept on their own:

  * HTTP now relies on DataWeave’s multipart format support.

  * Email and Web Service Consumer allow attachments to be explicitly added using DataWeave.

## Message Collections

One of the benefits of the new Mule Message structure is when dealing with
collections. In Mule 3, components that returned multiple payloads, used a
special structure called the `MuleMessageCollection`. In Mule 4, any component
that needs to deal with multiple messages can simply set the payload of the
message to a List of Mule Messages. You can then iterate over these messages
using DataWeave, For Each, or other components.

For example, the `<file:list>` operation retrieves a List of Messages. Each
message has attributes for each file, which makes it easy to make decisions
based on file size, whether it’s a directory, and so on.

## See Also

  * [Migrating HTTP Connector Uses](migration-connectors-http)

  * [Supported Data Formats](../../dataweave/latest/dataweave-formats)

  * [DataWeave Variables](../../dataweave/latest/dataweave-variables)

  * [Migrating the Enricher to a Target Variable](migration-core-enricher)

