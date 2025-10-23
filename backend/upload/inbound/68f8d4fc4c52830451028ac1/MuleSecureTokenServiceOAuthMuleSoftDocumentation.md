# Mule Secure Token Service OAuth 2.0

The Mule runtime engine supports the OAuth 2.0 protocol. The way to configure
OAuth 2.0 authorization differs, depending on the OAuth role and your
objective:

  * Configure authentication in your client Mule app when sending requests to a service that requires authentication, such as the Github OAuth2 server. Use the [OAuth Module](../../oauth-module/latest/oauth-module-reference) for the OAuth2 configuration.

  * Use the [Mule OAuth2 Provider Connector](../../oauth2-provider-module/latest/oauth2-provider-module-reference) to create a Mule application that grants and validates the tokens needed to access a protected resource.

To protect your API or app from receiving unauthorized requests, use an API
Manager policy, such as the `OAuth 2.0 Access Token Enforcement Using External
Provider` policy. To expose a web service protected by OAuth 2.0 security, see
the [API Manager documentation](../../api-manager/latest/mule-oauth-provider-
landing-page).

## See Also

  * [OAuth Authorization Grant Types](authorization-grant-types)

