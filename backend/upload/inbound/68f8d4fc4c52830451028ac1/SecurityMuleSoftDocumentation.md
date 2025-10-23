# Security

It is critical to ensure that the valuable information that a business stores
and makes available through software applications and web services is secure,
protected from unauthorized users and malicious attackers. But it is also
critical that these protected resources, such as credit card information or
Social Security numbers, be immediately accessible to authorized, legitimate
users and systems to conduct business transactions.  

To provide secure access to information, applications and services can apply a
variety of security measures. Mule runtime engine (Mule) provides several
tools and methods that enables you to protect applications:

  * Securing application configuration properties

  * Using the Cryptography module

  * Configuring a FIPS 140-2 certified environment

  * Securing flows with Spring security

  * Configuring TLS cryptographic protocol

  * Obtaining access to protected resource using Oath Authorization Grant Types

  * Configuring the Mule Secure Token Service

## Secure Configuration Properties

Encrypting configuration properties for your applications involves creating a
secure configuration properties file, defining the secure properties in the
file, and configuring the file in your project with the Mule Secure
Configuration Properties Extension module.  

See details in [Secure Configuration Properties](secure-configuration-
properties)

## Cryptography Module

The Cryptography module provides the following main cryptography capabilities
to a Mule application:

  * Symmetric and asymmetric encryption and decryption of messages

  * Message signing and signature validation of signed messages  

This module supports three different strategies to encrypt and sign your
messages:

  * [PGP](cryptography-pgp)  
Provides basic signing and encryption.

  * [XML](cryptography-xml)  
Provides signing and encryption of XML documents or elements.

  * [JCE](cryptography-jce)  
Provides the wide range of cryptography capabilities available through the
Java Cryptography Extension.  

See details in [Cryptography Module](cryptography).

## FIPS 140-2 Compliance Support

You can configure Mule 4 to run in a FIPS 140-2 certified environment if you
meet the following two requirements:

  * A certified cryptography module installed in your Java environment

  * Mule settings adjusted to run in FIPS security mode

See details in [FIPS 140-2 Compliance Support](fips-140-2-compliance-support)

## Spring Security

Spring Security provides authentication and authorization via JAAS, LDAP, CAS
(Yale Central Authentication service), and DAO. The following topics help get
you started securing your flows using Spring Security:

  * [Configure LDAP Provider for Spring Security](setting-up-ldap-provider-for-spring-security)  
Perform component authorization, or use it as a Mule security provider.

  * [Component Authorization Using Spring Security](component-authorization-using-spring-security)  
Configure authorization using Spring Security features on your Mule
components, so that users with different roles can only invoke certain
methods.

## TLS Configuration

TLS is a cryptographic protocol that provides communications security for your
Mule app. Mule 4.x supports Transport Layer Security (TLS) 1.1 and 1.2.

See details in [TLS Configuration](tls-configuration)

## OAuth Authorization Grant Types

There are four types of authorization grants that an OAuth consumer (a client
app) can use to obtain access to a protected resource from an OAuth service
provider: Authorization Code, Implicit, Resource Owner Password Credentials,
and Client Credentials.

See details in [OAuth Authorization Grant Types](authorization-grant-types)

## Mule Secure Token Service

Mule supports the OAuth 2.0 protocol. How you configure OAuth 2.0
authorization depends on your OAuth role and objective.

See details in [Mule Secure Token Service](mule-secure-token-service)

