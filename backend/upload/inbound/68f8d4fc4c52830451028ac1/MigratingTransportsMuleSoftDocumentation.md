# Migrating Transports

Mule 3 transports have been replaced by connectors, which follow an operation
model in Mule 4. Most Mule transports are replaceable by a corresponding
connector in Mule 4.

Some migration issues are common to all transports. For transport-specific
migration documentation, refer to [Migrating Connectors and Modules to Mule
4](migration-connectors) and its child pages, instead.

## Endpoint Addresses

In Mule 3, an endpoint could be configured with either transport-specific
attributes (for example, an HTTP endpoint could use `host`, `port`, and
`path`) or with the generic `address` attribute.

Whenever the generic `address` attribute was used, it was possible to
reference a property, for example:

    
    
    <http:inbound-endpoint address="${External.URL}"/>

The properties configuration for `External.URL` looks something like this:

    
    
    External.URL=http://0.0.0.0:8080/rootPath

In Mule 4, the connectors define the connection attributes separately, so any
full address property has to be split into its components.

    
    
    <http:listener-config name="listenerConfig">
        <http:listener-connection host="${External.URL.host}" port="${External.URL.port}"/>
    </http:listener-config>
    
    <flow>
        <http:listener config-ref="listenerConfig" path="${External.URL.path}"/>
    
        ...
    </flow>

The configuration for the properties becomes:

    
    
    External.URL.host=0.0.0.0
    External.URL.port=8080
    External.URL.path=/rootPath

Connector-specific documentation (such as for the HTTP or Email connector)
provides detail on the exact properties that the connector requires.

## Service Overrides

In Mule 4, service override customizations through custom Java code are not
supported in Mule 4.

In Mule 3, it is possible to customize the behavior of a transport through a
connector’s `service-overrides` element. This element provides a way to
reference Java classes with custom code that provides the new functionality.

Mule 3 Example: Connector with `service-overrides`

    
    
    <imap:connector name="imapConnector" moveToFolder="processed" deleteReadMessages="false" checkFrequency="200">
        <service-overrides messageReceiver="org.mule.transport.email.functional.RetrieveMessageReceiverPollCounter"/>
    </imap:connector>

The way to migrate such customizations to Mule 4 depends on what the custom
code does, so you might:

  * Provide the functionality through another Mule feature or component, such as a [DataWeave](dataweave) transformation, a [Java Module](../../java-module/latest/), or a [Scripting Module](../../scripting-module/latest/)).

  * Use the [Mule SDK](../../mule-sdk/latest/) to create a connector that provides your customized transport functionality. As a starting point, you can use open-source connectors as dependencies (for example, <https://github.com/mulesoft/mule-http-connector>).

  * Similar to the previous approach, you can fork an open-source connector repository and add your custom code to the fork. MuleSoft welcome Pull Requests for your changes.

  * Provide a feature request to MuleSoft. You can request that MuleSoft add the functionality that your custom code provided through `service-overrides`. Visit [MuleSoft Support Ideas](https://help.mulesoft.com/s/ideas) to submit such requests.

## See Also

[Migrating Connectors and Modules to Mule 4](migration-connectors)

[Java Integration](intro-java-integration)

[Mule SDK](../../mule-sdk/latest/)

