# Build an Application from an API Specification

During your app development lifecycle, you can build Mule REST or SOAP APIs
from an API specification using APIkit. You develop APIs based on the
following modeling languages:

  * RAML (RESTful API Modeling Language)

  * WSDL (Web Service Description Language)

  * OData (OData-Enabled APIs using APIkit OData Extension)

  * OAS (Open API Specification)

By using APIkit in Anypoint Studio, you can simplify the design and
implementation of APIs by automating Mule flow creation based on importing
either a RAML or a WSDL specification file. After generating the API, you can
perform calls to test the API and then finalize its implementation.  

Additionally, APIkit helps you build applications using Apache Maven, and also
provides a CLI tool to generate flows for an already existing application.
However, before you perform any of these tasks, you must learn the basic
APIkit anatomy and understand the scaffolding technique that generates Mule
flows when you start APIkit projects.

## APIkit Anatomy

A REST or SOAP Studio project that uses APIkit has the following parts:

  * A REST or SOAP interface

  * A main flow

  * Backend flows

![A REST Studio project showing components including APIkit Router and API
console](_images/mruntime-rest-studio-project.png)

Figure 1. REST Studio Project.

![A SOAP Studio project showing components including SOAP Router and Transform
Message](_images/mruntime-soap-studio-project.png)

Figure 2. SOAP Studio Project.

### REST Interface

The relationship between REST resources and actions is called _resource-
action_ pairing. The interface exposes internal data assets requested by the
REST service. Also, the interface defines the API, designating resources that
contain or access data and specify actions, such as GET and PUT, on the
example data.

### SOAP Interface

The interface defined by a WSDL file exposes a number of services. Each
service has a set of operations. The underlying type of data is XML defined by
schemas within the WSDL file or by an imported XSD file.

### Main Flow

The main flow for the API manages these functions:

  * Exposes the API using Anypoint Connector for HTTP (HTTP Connector).

  * Routes requests between the interface and the backend flows based on the HTTP request.

  * Accepts requests, sends responses, and facilitates communication between the interface and API processes.

The main flow consists of HTTP Listener and APIkit (REST or SOAP) Router
components. The APIkit Router is a key message processor that validates
requests against the provided definition, enriches messages (for example by
adding default values to the messages) and routes requests to a particular
flow. Also, the Router raises errors messages if errors occurs while routing,
validating or processing the user request.

![A REST API main flow with components including Listener and APIkit
Router](_images/mruntime-rest-main-flow.png)

Figure 3. REST API Main Flow.

![A SOAP API main flow with components including Listener and SOAP
Router](_images/mruntime-soap-main-flow.png)

Figure 4. SOAP API Main Flow.

### Backend Flows

APIkit for REST generates a backend flow for each resource-action pairing in a
RAML file.  
APIkit for SOAP generates a backend flow for each operation in a WSDL.  
In the following example, the RAML interface receives the GET request users.
The backend flow accesses a database to look up users by ID.

![REST API backend flows](_images/mruntime-rest-backend-flows.png)

Figure 5. REST API Backend Flows.

### Perform Calls

For REST APIs, use API Console to perform calls to the API.  
For SOAP APIs, use a SOAP testing tool such as SoapUI to perform calls to the
API.

## Start APIkit Project and Generate Mule Flows

When you start a new APIkit project in Studio, you have the option to import
an API definition file. When you import the file, the APIkit scaffolding
mechanism generates different flows for the API. There are three ways to start
an APIkit project in Anypoint Studio:

### Start a New APIkit Project Using an API Definition File

Use this method if you want to start a project by either importing an existing
RAML or WSDL file or by referencing the file URL:

  1. Select **File > New > Mule Project**.

  2. In **Project Name** , enter a name for the project, for example **myproject**.

  3. Select or accept the default EE Runtime, for example **Mule Server 4.2.0 EE**.

  4. In **API Implementation** , select **Specify API Definition File Location or URL**.

  5. In **Location** , do one of the following:

     * If you created an `api.raml` file in Design Center, select **Design Center** . Login to Anypoint Platform if necessary, and select `api.raml`.

     * If you didn’t create a RAML file in Design Center, select **Browse Files** and select the RAML or WSDL file that you created in a text editor. For a WSDL file, select a service and port from the drop-down menus or accept the defaults.

  6. Accept the Location default options, and click **Finish**.

![A new Mule project with an API specification selected](_images/mruntime-
start-apikit-project-1.png)

Figure 6. New Mule Project window selecting API specification .

Using this method the APIkit scaffolding technique generates:

  * An archetype that contains basic configuration files plus a Mule XML configuration file

  * An implementation of the API

For RAML-based APIs, the RAML file appears under the `src/main/resources/api`
folder. The implementation of the API contains:

  * A main flow with an HTTP Listener

  * APIkit Router component

  * Error handlers

  * RAML dependencies (push or pull changes from one location, such as Studio, to the other, such as Design Center)

  * Backend flows containing REST resource-action mappings

For WSDL-based APIs, the WSDL file appears under the `src/main/resources/api`
folder. The implementation of the API contains:

  * A SOAP Router

  * A SOAP fault response template

  * Backend flows containing SOAP message templates

The following graphics illustrate the APIkit scaffolding:

![XML configuration for RAML scaffolding including Listener, APIkit Router,
and Error handling components.](_images/mruntime-raml-scaffolding.png)

Figure 7. RAML Scaffolding.

![XML configuration for WSDL scaffolding including Listener, SOAP Router, and
Error handling components](_images/mruntime-wsdl-scaffolding.png)

Figure 8. WSDL Scaffolding.

In Studio, the REST API APIkit project looks like this:

![An APIkit project with files and configurations for handling REST API
requests.](_images/mruntime-rest-api-studio-apikit.png)

Figure 9. REST API in Anypoint Studio UI with the Package Explorer and Canvas
sections.

The five items illustrated here show:

  1. The project files in the Package Explorer of Studio with the `api.raml` file under `src/main/resources/api` folder.

  2. The main flow, with the APIkit Router.

  3. APIkit Console

  4. Error Handling

  5. Generated flows for each resource method.  
The generated minimal flows meets the communication operations required by a
REST contract.

In Studio, the SOAP API APIkit project looks like this:

![A REST API APIkit project setup showing the Package Explorer and canvas in
Anypoint Studio](_images/mruntime-soap-api-studio-apikit.png)

Figure 10. SOAP API in Anypoint Studio UI with the Package Explorer and Canvas
sections.

The four items illustrated here show:

  1. The project files in the Package Explorer of Studio with the `example.wsdl` file under `src/main/resources/api` folder.

  2. The main flow, with the SOAP Router.

  3. SOAP fault response template

  4. Generated backend flows containing SOAP message templates.

After you create your APIkit project, you can continue building the
application by performing calls to test the API and finalize its
implementation. See Build Applications Workflows for details.

### Start a New APIkit Project

Use this method if you start an APIkit project without an API specification
file and you can later add it into the project. APIkit generates a skeletal
RAML file and XML configuration file.

  1. Select **File > New > Mule Project**.

  2. In **Project Name** , enter a name for the project, for example **myproject**.

  3. Select or accept the default EE . Runtime, for example **Mule Server 4.2.0 EE**.

  4. In **API Implementation** , do _not_ select **Specify API Definition File Location or URL**.  
This creates the backend-first APIkit design.

  5. Accept the other default options, and click **Finish**.

![A new Mule project without an API specification](_images/mruntime-start-
apikit-project-2.png)

Figure 11. New Mule Project window.

Using this method the APIkit scaffolding generates a skeletal RAML file and
XML configuration file that includes the following components:

  * A main flow `<flow name="main-api"></flow>`

  * HTTP Listener configuration in the main flow

  * APIkit Router component

  * Error handlers

You can later add an API specification to the backend-first APIkit design and
generate backend flows to continue building the application. See Build
Applications Workflows for details.

### Start a New APIkit Project by Generating Backend Flows

To perform this task, you must have met the following prerequisites:

  * Created a RAML file in Studio (RAML editor)

  * Created a main flow with an HTTP Listener and APIkit Router components

When you create a RAML file in Studio, generating backend flows is optional.
Error handling is generated automatically for a RAML-based API. To start the
APIkit project, you need to generate the backend flows from the main flow.
Follow the next steps:

  1. In Package Explorer, right-click the project name.

  2. Select **Mule > Generate Flows From REST API**.

![A Package Explorer view showing options for generating backend flows from
Mule project](_images/mruntime-start-apikit-project-3.png)

Figure 12. Generating backend flows from Mule Project.

The APIkit scaffolding technique generates the backend flows following the
main flow. You can then continue building the application by performing calls
to test the API and finalize its implementation. See Build Applications
Workflows for details.

## Build Applications Workflows

After you are familiar with the basic APIkit anatomy and the scaffolding
technique, examine the following workflows to help you build your desired
application by creating the APIkit project, generating Mule flows, performing
calls to the API, and finalizing its implementation:

  * [Build a REST API using APIKit for REST](../../apikit/latest/apikit-4-for-rest)

  * [Build a SOAP API using APKit for SOAP](../../apikit/latest/apikit-4-for-soap)

Additionally, you can:

  * [Convert an Existing Mule Project to an APIkit Project](../../apikit/latest/apikit-workflow-convert-existing)  
Add an API specification to an existing APIkit backend-first design, define
API definition files, create main flow, generate backend REST API flows, map
RAML resources to actions.

  * [Perform APIkit 4.x Tasks](../../apikit/latest/key-configurations)  
Change APIkit project, customize API console, configure headers, retrieve RAML
files, execute nonfunctional requirements, configure load balancers.

  * [Create an Enable O-Data API using the APIkit OData Extension](../../apikit/latest/creating-an-odatav4-api-with-apikit)  
Generate Mule flows to handle OData requests.

  * [Create an APIkit project with Maven](../../apikit/latest/apikit-4-scaffolding-reference)  
Add APIkit components to an existing Apache Maven project.

## Consume Data from an API

After you build your application, you can start consuming data from the API.
Review the [Consume Data from an API documentation](consume-data-from-an-api)
for guidelines.

## See Also

  * [APIkit](../../apikit/latest/)

  * [APIKit Handling Errors](../../apikit/latest/apikit-error-handling-reference)

