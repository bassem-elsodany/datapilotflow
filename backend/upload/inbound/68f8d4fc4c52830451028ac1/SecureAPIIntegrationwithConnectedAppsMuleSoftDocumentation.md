# Secure API Integration with Connected Apps

Connected apps provide the framework for a safe way for external applications
to integrate with your Anypoint Platform org using
[APIs](https://anypoint.mulesoft.com/exchange/portals/anypoint-platform)
through OAuth 2.0 and OpenID Connect without giving the external apps full
access to everything. Connected apps enable you to use secure authentication
protocols and control an app’s access to user data.

Connected apps:

  * Establish a trusted relationship with the external application.

  * Manage and enforce the specific permissions granted to that external application.

  * Provide secure and temporary access to your Anypoint Platform resources without exposing your sensitive information.

Actions taken by connected apps are audited, and you can revoke access at any
time.

## Authentication and Authorization

Anypoint Platform supports OAuth 2.0 and OpenID Connect to authorize apps to
access data within Anypoint Platform. OAuth (Open Authorization) is an open
protocol that provides secure API authorization from applications in a simple
and standardized way. OAuth can authorize access to resources without
revealing user credentials to apps. OpenID Connect identifies the end user and
obtains information to pass to OAuth 2.0 connected apps.

For more information, see [OAuth 2.0](https://oauth.net/2/) and [OpenID
Connect](https://openid.net/connect/).

## Access and Authorization

Use connected apps to create a seamless authentication experience for end
users. Connected apps address use cases for these types of users:

  * An [organization administrator](connected-apps-org-admin) can control how their organization’s data is used by allowlisting apps, revoking access, and disabling this feature for the entire organization.

  * An [organization administrator who is developing a connected app](connected-apps-developers#developers) can register new (and manage existing) apps at the root organization or business group level.

  * An [end user](connected-apps-end-users#end-users) can authorize apps to access particular information, such as viewing assets in Anypoint Exchange.

There are two types of connected apps supporting different grant types:

Type | Description | Supported grant types | Example use cases  
---|---|---|---  
App that acts on behalf of a user | Authorized by a user to act on their behalf | 

  * Authorization Code
  * Password
  * JWT Bearer

| Productizing additional third-party applications on top of Anypoint
Platform.  
App that acts on its own behalf | Acts on its own behalf without impersonating a user. The app can be used only in the organization where it’s created. | Client Credentials | Automation scenarios such as building or accessing CI/CD pipelines without user intervention.  
  
## Example

A connected app acts like a doorman for your building. You, as the owner, can
configure this doorman to:

  * Identify the external app.

You register the external application with Anypoint Platform, giving it a
unique identity (like an ID card for the doorman to recognize).

  * Define the permissions for which rooms are accessible to the visitor.

You specify exactly which APIs and data the external app has permission to
use.

  * Issue a temporary access pass (OAuth 2.0 tokens).

When the external app wants to access something, the connected app (the
doorman) verifies its identity and, if authorized, issues a temporary access
pass (an OAuth 2.0 token). This pass allows the external app to access only
the permitted resources for a limited time, without ever needing your direct
login credentials.

## See Also

  * [Connected Apps for Organization Administrators](connected-apps-org-admin)

  * [Connected Apps for Developers](connected-apps-developers)

  * [Connected Apps for End Users](connected-apps-end-users)

