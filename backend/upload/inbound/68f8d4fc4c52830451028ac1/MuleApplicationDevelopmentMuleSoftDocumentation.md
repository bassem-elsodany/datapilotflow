# Mule Application Development

You create Mule applications to perform system integrations. Typically, the
application reads data from internal and external sources, processes and
transforms data to the required formats or structures, and writes that output
to the systems and servers where you store or use the transformed data.

Mule applications are configured to run in Mule runtime engine (Mule). A
request to a Mule application triggers Mule to encode the request and data in
a Mule event and to pass it to either single or multiple threads.

## Getting Started with Mule Application Development

To get started with Mule application development, you can follow the steps in
these tutorials:

  * [Create a "Hello World" Mule app](mule-app-dev-hellomule)

Build a Mule application that interacts with a user in a simple HTTP request-
response flow.

  * [Create a Mule app that uses the Database Connector and DataWeave](mule-app-tutorial)

Build a Mule application that retrieves data from a database and transforms it
to a new structure.

## Building Blocks of a Mule Application

Mule applications use connectors, modules, and components to read, write, and
process data.

  * [Connectors and Modules](../../connectors/)

Anypoint connectors provide components, such as listeners, that interact with
external API endpoints and act on data in the Mule application. Modules, such
as the Validation, Java, Spring, and OAuth, provide modules that act on data
in a Mule application without providing a direct connection to an endpoint.

  * [Core Components](about-components)

Core components support flow control, error handling, logging, batch, and
other programmatic operations on data that flows through your application.

## DataWeave Language

DataWeave is the primary language used for formulating expressions in Mule.
Connectors, modules, and components support the use of DataWeave to access,
manipulate, and transform data structures and output formats, and to extract
data that is processed within the Mule application.

At runtime, Mule evaluates DataWeave expressions while executing a flow to:

  * Extract data needed to process the current message

  * Set or manipulate a value in the message

## Mule Flows

Understanding basic flow architecture is key to understanding a Mule
application. Essentially, every Mule flow contains a series of Mule components
that receive or process messages:

![A flow including an HTTP Listener, data transformation, database connection,
and logging process](_images/flow-example.png)

Figure 1. Simple Flow in Design Center

At the simplest level, flows are sequences of processors. A message that
enters a flow can pass through a variety of processors. In a typical flow, a
Mule application receives a message through a source (such as an HTTP Listener
component), transforms that message into a new format, and processes any
business logic before writing the processed message to an external system in a
format that the system can read.

To separate processing into more manageable units, Mule applications often
contain multiple, interrelated flows instead of just a single flow. One flow
can call another flow as a direct reference.

For more information about this topic, see [Flows and Subflows](about-flows)
and [Mule Components](mule-components).

### Sources

A source component (or trigger) is the first component in a flow. It receives
a triggering event, creates a corresponding Mule event, and forwards that
event for processing by the next component in the flow.

External clients can trigger processing in a Mule flow through several
communication protocols and methods, such as JMS, HTTP, FTP, JDBC, or File.
Mule translates these communication protocols and methods into a standard
message format, which passes through the flow’s processors.

Sources in Mule can connect to specific external sources, either through a
standard protocol or a third-party API. It is also possible to set a Scheduler
component. Some schedulers can poll for specific changes to external
resources, such as new files or table rows in an external resource. Examples
of listeners and connector operations that can trigger a flow include:

  * HTTP, JMS, and VM listeners in their associated connectors

  * On Table Row operation in the Database connector

  * On New or Updated File operation in the File and FTP connectors

  * Scheduler

Note that you can also create your own source using the [Mule SDK](../../mule-
sdk/latest/).

### Processors

After a flow is triggered through the source component, subsequent components
process the data as it travels through the flow. By default, each processor
that receives a Mule event returns a new Mule message, typically with a set of
attributes and the message payload that the processor returns. The processor
forwards the new message as output to the next processor in the flow.

Processors available to Mule applications include:

  * Components from modules and connectors

Examples include operations that read from and write to an external resource
and that validate data in the Mule application. Some operations can make
client requests to external resources and services (including external
databases and systems, such as Salesforce, Workday, ServiceNow, and many
others) and to other Mule applications. Others can run your custom code,
support OAuth configurations, and manage communication through asynchronous
queues, for example. Many other operations are available.

  * Core components

Core components can route data, perform data transformations, handle errors
that might occur when processing the event, and perform other tasks in a Mule
application.

Transformers (such as the Transform Message, Set Variable, and others) are key
to exchanging data between nodes. Transformers enable Mule to convert message
data in the Mule event to a format that another application or service can
read.

Mule also enables content enrichment of messages (through [Target
Variables](target-variables)) so that you can retrieve additional data and
attach it to the message.

Note that you can also create your own event processors using the [Mule
SDK](../../mule-sdk/latest/).

## Security

You can provide security to your Mule applications by encrypting properties,
configuring secure communications over TLS, setting up authentication over
OAuth 2.0, and providing cryptographic and other capabilities, such as FIPS
compliance.

  * [Security](securing)

## Development Environments

You can develop a Mule application using [Anypoint
Studio](../../studio/latest/) (an Eclipse-based IDE), or, if you are an
advanced developer, in your own IDE.

For example, in Studio, you build and design a Mule application in a project
that contains one or more XML-based files. A Mule project supports all the
dependencies required for development. The [Package
Explorer](../../studio/latest/#package-explorer) view in Studio provides
access to the project folders and files that make up a Mule project. Studio
provides a design-time environment in which you can also build, run, and test
your Mule application.

## Mule Versioning

The Mule version you use determines what your Mule application, domain, or
policy can do and what features and products are compatible with Mule. For
example, [Core components](about-components), which process the Mule event as
it travels through flows in a Mule application, are part of a Core module that
is bundled with and shares the same version as Mule. [Modules,
connectors](../../connectors/), the DataWeave language, and several MuleSoft
products have their own versioning system but are compatible with specific
versions of Mule. For example, DataWeave 2.0 and Studio 7.x are compatible
Mule 4.x runtime engines, while DataWeave 1.0 and Studio 6.x are compatible
with Mule 3.x runtime engines. You need to make sure the connector or module
you use in a Mule application is compatible with your Mule version.

## See Also

  * [Mule Message](about-mule-message)

  * [Variables in Mule Applications](about-mule-variables)

  * [Mule Configuration](about-mule-configuration)

  * [APIKit](../../apikit/latest/)

