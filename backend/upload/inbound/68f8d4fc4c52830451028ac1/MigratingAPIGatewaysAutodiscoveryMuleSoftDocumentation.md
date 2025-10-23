# Migrating API Gateways: Autodiscovery

The Autodiscovery element was updated after Mule 4 release.

  * APIs are referenced by an ID instead of a name and version.

  * Creation of APIs from the runtime is no longer possible.

Simple Mule app with an HTTP listener and an Autodiscovery element defined:

Mule 3 Example: All Configurable Attributes

    
    
    <?xml version="1.0" encoding="UTF-8"?>
    <mule xmlns="http://www.mulesoft.org/schema/mule/core"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xmlns:api-platform-gw="http://www.mulesoft.org/schema/mule/api-platform-gw"
          xmlns:http="http://www.mulesoft.org/schema/mule/http"
          xsi:schemaLocation="
           http://www.mulesoft.org/schema/mule/core http://www.mulesoft.org/schema/mule/core/current/mule.xsd
           http://www.mulesoft.org/schema/mule/http http://www.mulesoft.org/schema/mule/http/current/mule-http.xsd
           http://www.mulesoft.org/schema/mule/api-platform-gw http://www.mulesoft.org/schema/mule/api-platform-gw/current/mule-api-platform-gw.xsd">
    
        <api-platform-gw:api id="apiId" create="true" apiName="name" version="1.0.0" flowRef="flow_api">
            <api-platform-gw:description>This is a test API</api-platform-gw:description>
            <api-platform-gw:tag>tag1</api-platform-gw:tag>
            <api-platform-gw:tag>tag2</api-platform-gw:tag>
        </api-platform-gw:api>
    
        <http:listener-config name="httpConfig" host="localhost" port="${port}" />
    
        <flow name="flow_api">
            <http:listener config-ref="httpConfig" path="api" />
            <logger message="Executing empty" level="INFO"/>
        </flow>
    
    </mule>

Mule 4 Example: All Configurable Attributes

    
    
    <?xml version="1.0" encoding="UTF-8"?>
    <mule xmlns="http://www.mulesoft.org/schema/mule/core"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xmlns:http="http://www.mulesoft.org/schema/mule/http"
          xmlns:api-gateway="http://www.mulesoft.org/schema/mule/api-gateway"
          xsi:schemaLocation="
           http://www.mulesoft.org/schema/mule/core http://www.mulesoft.org/schema/mule/core/current/mule.xsd
           http://www.mulesoft.org/schema/mule/http http://www.mulesoft.org/schema/mule/http/current/mule-http.xsd
           http://www.mulesoft.org/schema/mule/api-gateway http://www.mulesoft.org/schema/mule/api-gateway/current/mule-api-gateway.xsd">
    
        <api-gateway:autodiscovery apiId="1" flowRef="flow_api" />
    
        <http:listener-config name="httpConfig" basePath="api">
            <http:listener-connection host="localhost" port="${port}"/>
        </http:listener-config>
    
        <flow name="flow_api">
            <http:listener config-ref="httpConfig" path="api" />
            <logger message="Executing empty" level="INFO"/>
        </flow>
    
    </mule>

## See Also

[Migrating API Gateways](migration-api-gateways)

[Migrating API Gateways: Policies](migration-api-gateways-policies)

[Migrating API Gateways: Mule Runtime Configuration](migration-api-gateways-
runtime-config)

