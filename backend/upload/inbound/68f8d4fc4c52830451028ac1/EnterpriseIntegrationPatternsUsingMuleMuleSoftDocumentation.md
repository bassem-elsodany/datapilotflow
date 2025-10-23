# Enterprise Integration Patterns Using Mule

Enterprise Integration Patterns are accepted solutions to recurring problems
within a given context. The patterns provide a framework for designing,
building messaging and integration systems, as well as a common language for
teams to use when architecting solutions.

Mule supports most of the patterns shown in the Enterprise Integration
Patterns book written by Gregor Hohpe and Bobby Woolf.

Mule reduces the effort required when building integrations by implementing
the patterns that you use to design solutions. You can then simply configure
and use these same patterns in Mule.

## Mapping Enterprise Integration Patterns into Mule Objects

Review the following list of Enterprise Integration Patterns that can be
mapped directly to Mule objects:

### Integration Styles

Pattern | Mapping to a Mule Object  
---|---  
File Transfer | [File Connector](../../file-connector/latest/)  
Shared Database | [DataBase Connector](../../db-connector/latest/)  
Remote Procedure Invocation | Mule APIs are meant to work like this procedure or even doing requests to external APIs.  
Messaging | Mule is all about Messaging.  
  
### Messaging Systems

Pattern | Mapping to a Mule Object  
---|---  
Message Channel | Mule provides a message channel that connects the message processors in a flow.  
Pipes and Filters | A flow implements a pipe and filter architecture.  
Message Router | [Message Routers](about-components#flow-control-routers).  
Message Translator | [Message Transformer](transform-component-about).  
Message Endpoint | [Creating Message Sources with the Mule SDK](../../mule-sdk/latest/sources) and [Operations](../../mule-sdk/latest/operations).  
  
### Messaging Channels

Pattern | Mapping to a Mule Object  
---|---  
Point-to-Point Channel | The default channel within a flow.  
Message Bus | Mule is a message bus.  
Guaranteed Delivery | Using [Reliability Patterns](reliability-patterns).  
  
### Message Construction

Pattern | Mapping to a Mule Object  
---|---  
Event Message | Mule transmits events from different Application or Processors.  
Request Reply | Mule uses connectors that facilitate request-reply wise operations, or using [Reliability Patterns](reliability-patterns).  
  
### Message Routing

Pattern | Mapping to a Mule Object  
---|---  
Content-Based Router | [Choice Router](choice-router-concept).  
Message Filter | [Validation Module](../../validation-connector/latest/).  
Dynamic Routing | [Message Routers](about-components#flow-control-routers).  
Scatter Gather | [Scatter Gather Router](scatter-gather-concept).  
Splitter | [Foreach Scope](for-each-scope-concept), [Parape](parallel-foreach-scope) and [Batch](batch-processing-concept).  
Aggregator | [Aggregator Module](../../aggregators-module/latest/).  
  
### Message Transformation

Pattern | Mapping to a Mule Object  
---|---  
Content Enricher | [Target Variables](target-variables).  
  
### Messaging Endpoints

Pattern | Mapping to a Mule Object  
---|---  
Polling Consumer | [Creating Message Sources with the Mule SDK](../../mule-sdk/latest/sources).  
Transactional Client | [Transaction Management](transaction-management).  
Idempotent Receiver | [Redelivery Policy](redelivery-policy).

