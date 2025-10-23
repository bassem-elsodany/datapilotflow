# Migrating API Gateways: Mule Runtime Configuration

Configuration properties for API Gateway Runtime changed in Mule 4.

These properties have to be defined in the `wrapper.conf` for Mule 3 to work
as API Gateway:

    
    
    -M-Danypoint.platform.client_id=clientId
    -M-Danypoint.platform.client_secret=clientSecret
    -M-Danypoint.platform.platform_base_uri=https://anypoint.mulesoft.com/apiplatform
    -M-Danypoint.platform.coreservice_base_uri=https://anypoint.mulesoft.com/accounts
    -M-Danypoint.platform.contracts_base_uri=https://anypoint.mulesoft.com/apigateway/ccs
    -M-Danypoint.platform.analytics_base_uri=https://analytics-ingest.anypoint.mulesoft.com

Starting from Mule 4, these properties have to be defined in the
`wrapper.conf` in order to work as an API Gateway:

    
    
    -M-Danypoint.platform.client_id=clientId
    -M-Danypoint.platform.client_secret=clientSecret
    -M-Danypoint.platform.base_uri=https://anypoint.mulesoft.com
    -M-Danypoint.platform.analytics_base_uri=https://analytics-ingest.anypoint.mulesoft.com

## See Also

[Migrating API Gateways](migration-api-gateways)

[Migrating API Gateways: Autodiscovery](migration-api-gateways-autodiscovery)

[Migrating API Gateways: Policies](migration-api-gateways-policies)

