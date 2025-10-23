# Migrating Core Components

The table below maps Mule 3.x components to their Mule 4 equivalents.

Mule 3.x Component | Mule 4.0 Replacement  
---|---  
All router | Use [Scatter Gather](scatter-gather-concept) instead or execute the operations one after the other with different target attributes and then use DW to merge results.  
async[`processingStrategy`] | Async processing strategies are no longer needed with the non-blocking execution engine; remove all processing strategies from your scope when you migrate to Mule 4. Use an [Async](async-scope-reference) scope wrapping all the components that you want to execute asynchronously.  
asynchronous-processing-strategy | Async processing strategies are no longer needed with the non-blocking execution engine; remove all processing strategies from your scope when you migrate to Mule 4. Use an [Async](async-scope-reference) scope wrapping all the components that you want to execute asynchronously.  
bridge | Build an equivalent flow  
catch-exception-strategy | Use [error-handler](on-error-scope-concept) with an `on-error-continue` strategy.  
choice-exception-strategy | Use [error-handler](on-error-scope-concept) with different strategies inside using error type selection or when attribute.  
combine-collections-transformer | No longer needed with the simplified message model. MuleMessageCollections are replaced with arrays of Mule Messages, which can be merged or iterated through using any Mule component, such as DataWeave or foreach.  
component | Use the [Java module](../../java-module/latest/).  
composite-source | Create one flow per each source and invoke a private flow using flow-ref for the common functionality.  
configuration[`defaultExceptionStrategy-ref`] | New name is `defaultErrorHandler-ref`  
configuration[`flowEndingWithOneWayEndpointReturnsNull`] | No longer needed with new execution engine.  
configuration[`useExtendedTransformations`] | Removed.  
configuration[`enricherPropagatesSessionVariableChanges`] | Removed.  
copy-attachments | Per the new [Message Structure](about-mule-message), attachments will now be part of the message Attributes. You can manipulate them at will using DataWeave  
copy-properties | Per the new [Message Structure](about-mule-message), properties will now be part of the message Attributes. You can manipulate them at will using DataWeave  
custom-agent | No longer supported.  
custom-aggregator | Use the [Mule SDK](../../mule-sdk/latest/) to build the custom aggregator.  
custom-connector | Use the [Mule SDK](../../mule-sdk/latest/) to build your own connector.  
custom-exception-strategy | No longer needed. Use [error-handler](on-error-scope-concept)  
custom-lifecycle-adapter-factory | No longer supported.  
custom-object-store | Use [Object Store connector](migration-connectors-objectstore) to create custom stores.  
custom-processor | Use the [Mule SDK](../../mule-sdk/latest/) or the [Scripting module](migration-module-scripting) instead  
custom-queue-store | Use the new [VM Connector](migration-module-vm).  
custom-router-resolver | Use the [Mule SDK](../../mule-sdk/latest/) to build a custom router.  
custom-router | Use the [Mule SDK](../../mule-sdk/latest/) to build a custom router.  
custom-service | Use flows.  
custom-source | Use the [Mule SDK](../../mule-sdk/latest/) to write a new event source.  
custom-splitter | Use DataWeave or the [Mule SDK](../../mule-sdk/latest/).  
custom-transaction-manager | Use the `<bti:transaction-manager/>`.  
custom-transaction | No longer supported.  
default-exception-strategy | Use [error-handler](on-error-scope-concept) with an `on-error-propagate` strategy.  
default-in-memory-queue-store | Use the new [VM Connector](migration-module-vm).  
default-persistent-queue-store | Use the new [VM Connector](migration-module-vm).  
default-service-exception-strategy | Use [error-handler](on-error-scope-concept) with an on-error-propagate strategy.  
endpoint | Use connectors.  
exception-strategy | Use [error-handler](on-error-scope-concept).  
expression-component | Depending on the nature of your expression, you can either use DataWeave (for data access expressions), [Scripting module](migration-module-scripting) or the [Mule SDK](../../mule-sdk/latest/) for algorithmic expressions, or the [Java module](../../java-module/latest/) for expressions which simply access Java.  
file-queue-store | Use the new [VM Connector](migration-module-vm).  
flow[`processingStrategy`] | Removed. Non-blocking execution engine ensures that users do not need to tune this.  
idempotent-message-filter | Replaced by [idempotent-message-validator](idempotent-message-validator).  
idempotent-redelivery-policy | New name is `redelivery-policy`.  
idempotent-secure-hash-message-filter | Replaced by [idempotent-message-validator](idempotent-message-validator).  
in-memory-store | Use [Object Store connector](migration-connectors-objectstore) to create [custom stores](../../object-store-connector/latest/object-store-to-define-a-new-os).  
inbound-endpoint | Use the event sources or triggers defined on each connector or module.  
include-entry-point | Use the [Java module](../../java-module/latest/).  
interceptor-stack | Removed. Use custom policies.  
invoke | Use the [Java module](../../java-module/latest/)  
jndi-transaction-manager | Use the `<bti:transaction-manager/>`.  
jrun-transaction-manager | Use the `<bti:transaction-manager/>`.  
legacy-abstract-exception-strategy | Use the new [error-handler](on-error-scope-concept)  
managed-store | Use [Object Store connector](migration-connectors-objectstore) to create [custom stores](../../object-store-connector/latest/object-store-to-define-a-new-os).  
message-properties-transformer | Use Transform component and DataWeave.  
model | Removed. Use flows instead.  
mule[`version`] |   
outbound-endpoint | Element moved from the core namespace to the new transports namespace.  
poll → watermark | This capability has been built inside event sources from many connectors, like Salesforce, Database, SFTP, File, etc. You can also use the object-store connector to [manually set the watermark values](migration-patterns-watermark).  
poll | Replaced with [scheduler component](migration-core-poll).  
processor | Depending on the nature of your expression, you can either use DataWeave (for data access expressions), [Scripting module](migration-module-scripting) or the [Mule SDK](../../mule-sdk/latest/) for algorithmic expressions, or the [Java module](../../java-module/latest/) for expressions which simply access Java.  
prototype-object | Use Java module or Spring module.  
queue-profile | Use the [VM Connector](migration-module-vm).  
queue-store | [VM Connector](migration-module-vm).  
recipient-list | Removed.  
reconnect-custom-notifier | Removed.  
reconnect-custom-strategy | Removed.  
reconnect-notifier | Removed.  
remove-attachment | No longer needed per the new [Message Structure](about-mule-message), attachments  
remove-property | PNo longer needed per the new [Message Structure](about-mule-message), attachments  
response | No longer needed.  
request-reply | Mule 4 will not longer support request-reply for all connectors. Connectors that had a “request-reply” behavior will provide a “request-reply” operation built in, such as the JMS `publish-consume` operation.  
resin-transaction-manager | Removed.  
rollback-exception-strategy | Use error-handler with an on-error-propagate strategy.  
scatter-gather[`threading-profile`] | No longer needed now that Mule 4 is non blocking.  
seda-model | No more SEDA queues in Mule 4. The execution engine in Mule 4 is non-blocking.  
service | Use flows.  
set-attachment | No longer needed. Attachments can be stored as variables.  
set-property | Properties no longer exist in the new message model. You can store attributes from the Mule message in a variable.  
set-session-variable | Session variables have been removed. Users must explicitly pass headers across transport boundaries.  
simple-in-memory-queue-store | Use the new VM Connector.  
simple-service | Use flows.  
simple-text-file-store | Use object store module extension to create custom stores.  
singleton-object | Use Java module or Spring module.  
spring-object | Use Java module or Spring module.  
synchronous-processing-strategy | The behavior related to flow components execution is the same as flows in 4.x but it doesn’t always execute in the same thread as in 3.x.  
transactional scope | Replaced with “try” scope.  
username-password-filter | Removed.  
validator | Removed.  
weblogic-transaction-manager | Use the `<bti:transaction-manager/>`.  
websphere-transaction-manager | Use the `<bti:transaction-manager/>`.  
all-strategy | Removed.  
entry-point-resolver | Use the [Java module](../../java-module/latest/).  
filter | Filters are replaced by the [Validation module](migration-filters).  
interceptor | Interceptors are replaced with custom policies.  
message-info-mapping | No longer needed  
point-resolver-set | Use the Use the [Java module](../../java-module/latest/).  
router | Removed.  
threading-profile | No longer needed. The Runtime now tunes itself.  
transformer | Removed. Most explicit transformations are no longer needed. Use DataWeave for the corner cases.

