# Mule 3 to Mule 4 Cheat Sheet

To help you move from Mule 3 to Mule 4, we built this index to help you find
the Mule 4 equivalent of the most common Mule 3 use cases.

**IMPORTANT:** Keep in mind that this index is only intended to act as a quick
entry to the most common migration scenarios. It doesn’t contain the entire
migration guide. For the full set of migration articles, please visit our Mule
[Mule 4 for Mule 3 Users](index-migration) page.

  * [Configuration Properties](configuring-properties): There’s a new way of handling configuration properties in Mule 4

  * [Using Secure Properties](migration-secure-properties-placeholder): Secure placeholders are now a Runtime feature and no longer part of the Security Module

  * [Using the HTTP Connector](migration-connectors-http): The new HTTP connector has some differences with Mule 3, especially when it comes to handling multipart and form requests.

  * [From MEL to DataWeave](migration-mel): DataWeave 2.0 is now the expression language. Here’s how to adapt your MEL expressions to DataWeave.

  * [From DataWeave 1.0 to DataWeave 2.0](migration-dataweave): A new version of DataWeave is available in Mule 4

  * Where are the explicit transformers?: Transformers like `<object-to-string />` or `<object-to-json>` are no longer necessary. Mule handles this automatically under the covers

  * [Define a custom Object Store](../../object-store-connector/latest/object-store-to-define-a-new-os): Custom Object Stores are now defined through the new connector

  * [Use watermarks](migration-patterns-watermark): Watermarks have been simplified. You can also do it manually now allowing for more complex use cases.

  * [Accessing the Mule Message](migration-message-properties): The Mule Message has a new structure and it’s accessed differently. Here’s a quick overview.

  * Using Java: Interoperability with Java is now done through the [Java module](../../java-module/latest/). Optionally you can also try the [Scripting module](migration-module-scripting) or the [Mule SDK](../../mule-sdk/latest/)

  * [Using Spring](migration-module-spring): Instead of defining Spring beans directly in your application, you can now use the [Spring Module](../../spring-module/latest/).

  * [Using reconnection strategies](migration-patterns-reconnection-strategies): There are some small but important differences around reconnection in Mule 4.

  * [Classloading isolation](about-classloading-isolation): Classloading isolation changes the way resources and classes are shared. Read this article to learn more.

  * [Core Components Migration](migration-core): A comprehensive list of the changes that were made to the core language elements

  * [Using the new connectors](migration-connectors): A comprehensive list of the changes that were made to the main connectors.

  * [Using the Security Module (AES)](migration-aes): Anypoint Enterprise Security module was split into different modules explained here.

  * [Migrating Gateways](migration-api-gateways): This section covers the migration of API Gateway related features.

  * [Migrating ApiKit apps](migration-example-complex): Covers the necessary steps to successfully migrate APIkit-based applications.

  * Migrating custom components: You can use the [Mule SDK](../../mule-sdk/latest/) to create your own reusable components

  * Migrating DevKit based components: There’s a [DevKit Migration Tool](../../mule-sdk/latest/dmt) that helps to migrate DevKit projects for Mule 3 into Mule SDK ones.

  * [Transport service overrides](migration-transports): Covers how to migrate from generic transports.

  * [mule-high-availability-ha-clusters.adoc#configure-the-performance-profile](mule-high-availability-ha-clusters#configure-the-performance-profile): At a container level, change the property from `mule.clusterPartitioningMode=OPTIMIZE_PERFORMANCE` to `mule.cluster.storeprofile=performance`. At an individual application level, you can configure the store profile for a specific Mule application.

