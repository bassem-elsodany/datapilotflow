# Migrating an APIkit-based Application

This example covers the necessary steps for successfully migrate an APIkit-
based application from Mule 3 to Mule 4. The following REST API performs CRUD
(create, read, update and delete) operations over a MySQL database.

![A flow showing a main API flow with components including HTTP, APIkit
Router, and Error handling](_images/m3-apikit-based-example-main.png)

![A flow including an HTTP, APIkit Console, and Error
handling](_images/m3-apikit-based-example-console.png)

![A flow showing a GET request to retrieve products in an API-
config](_images/m3-apikit-based-example-get-products.png)

![A flowshowing the process for retrieving a product by ID using API
configuration and error handling](_images/m3-apikit-based-example-get-product-
id.png)

![A flow for posting a new product with error handling
steps](_images/m3-apikit-based-example-post-product.png)

![A flow showing the process for deleting a product by ID including error
handling](_images/m3-apikit-based-example-delete-product.png)

![An API configuration for a PUT request to update a product with JSON format
in an API-config](_images/m3-apikit-based-example-put-product.png)

![A flow showing API global exception handling with components including HTTP
status codes and payload settings](_images/m3-apikit-based-example-
globalexceptionmapping.png)

## Migrating Property Placeholders

Mule 4 supports property placeholders either as `.yaml` or `.properties`
configuration files.

  1. Create a folder with the name `config` under `/src/main/resources` project directory.

  2. Create a configuration file with the name `configuration.yaml` inside the newly created config folder.

  3. Migrate property placeholders from `.properties` to `.yaml` format.

configuration.properties

         
         http.host=0.0.0.0
         http.port=8081
         
         mysql.password=pa$$w0rd
         mysql.port=3306
         mysql.user=admin
         mysql.database=products
         mysql.host=corp.services.com
         
         autodiscovery.api.version=1.0.0:1762946
         autodiscovery.api.name=groupId:com.mulesoft.retailer.manufacturingit.apis:assetId:product-api-database
         
         anypoint.platform.client_id=1f702j71hu9z2x88v9vd19v7h248s589
         anypoint.platform.client_secret=87v8V47668701Dd574B0531255d6287d

configuration.yaml

         
         http:
           host: "0.0.0.0"
           port: "8081"
         
         mysql:
           password: "pa$$w0rd"
           port: "3306"
           user: "admin"
           database: "products"
           host: "corp.services.com"
         
         autodiscovery:
           api:
             name: "groupId:com.mulesoft.retailer.manufacturingit.apis:assetId:product-api-database"
             version: "1.0.0:1762946"
         
         anypoint:
           platform:
             client_id: "1f702j71hu9z2x88v9vd19v7h248s589"
             client_secret: "87v8V47668701Dd574B0531255d6287d"

  4. Replace the standard Spring element `<context:property-placeholder>` with the new Global Element `configuration-properties`.

Configuration XML for Property Placeholders in Studio 6.

         
         <context:property-placeholder location="configuration.properties" />

The `file` attribute points to the new configuration file in YAML format
located under `/src/main/resources/config` folder.

Configuration XML for Property Placeholders in Studio 7.

         
         <configuration-properties file="config/configuration.yaml" doc:name="Configuration properties" />

## Migrating Global HTTP Listener Configuration

Configuration XML for Global HTTP Listener Configuration in Studio 6.

    
    
    <http:listener-config name="HTTP_Listener_Configuration" host="${http.host}" port="${http.port}" doc:name="HTTP Listener Configuration"/>

The minimal configuration requires specifying `host` and `port` in the inner
`http:listener-connection` element. We use the placeholders defined in the
previous step.

Configuration XML for Global HTTP Listener Configuration in Studio 7.

    
    
    <http:listener-config name="httpListenerConfig">
      <http:listener-connection host="${http.host}" port="${http.port}" />
    </http:listener-config>

## Migrating MySQL Global Configuration

The database connector facilitates setting up _Derby_ , _MySQL_ and _Oracle_
databases for use in a Mule app.

  1. In the Mule Palette, click `Add Module` and select `Database Connector` among the available modules.

  2. Add a `Database Config` Global Configuration Element.

  3. In Database Config > Connection, select MySQL Connection.

  4. In MySQL JDBC Driver, click Add Dependency and configure the Maven information for the driver.
         
         <dependency>
           <groupId>mysql</groupId>
           <artifactId>mysql-connector-java</artifactId>
           <version>5.1.6</version>
         </dependency>

  5. Complete MySQL Global Configuration with `host`, `port`, `user`, `password` and `database` using previously defined placeholders.

Configuration XML for MySQL Global Configuration in Studio 6.

         
         <db:mysql-config name="MySQL_Configuration" host="${mysql.host}" port="${mysql.port}" user="${mysql.user}" password="${mysql.password}" database="${mysql.database}" doc:name="MySQL Configuration" />

Configuration XML for MySQL Global Configuration in Studio 7.

         
         <db:config name="MySQL_Configuration" doc:name="Database Config">
           <db:my-sql-connection host="${mysql.host}" port="${mysql.port}" user="${mysql.user}" password="${mysql.password}" database="${mysql.database}" />
         </db:config>

## Migrating API Autodiscovery Configuration

The `api-platform-gw` global element is required for registering an API in
Anypoint Platform.

Configuration XML for API Autodiscovery Configuration in Studio 6.

    
    
    <api-platform-gw:api apiName="${autodiscovery.api.name}" version="${autodiscovery.api.version}" flowRef="api-main" create="true" doc:name="API Autodiscovery"/>

In Mule Runtime 4.x, the `apiName`, `version`, and `create` attributes were
removed. Just the `apiId` and `flowRef` attributes are required. `apiId` is
generated by API Manager and visible on the API instance dashboard.

For API Autodiscovery Configuration in Mule Runtime 4.x:

  1. Add the following Namespace, Schema `global.xml` Configuration file.
         
         xmlns:api-gateway="http://www.mulesoft.org/schema/mule/api-gateway"
         http://www.mulesoft.org/schema/mule/api-gateway http://www.mulesoft.org/schema/mule/api-gateway/current/mule-api-gateway.xsd

  2. Add the required Autodiscovery Dependency Information to project `pom.xml` file.
         
         <dependency>
           <groupId>com.mulesoft.anypoint</groupId>
           <artifactId>mule-module-autodiscovery</artifactId>
           <version>4.0.0</version>
         </dependency>

Configuration XML for API Autodiscovery Configuration in Studio 7.

         
         <api-gateway:autodiscovery apiId="${autodiscovery.api.id}" flowRef="api-product-main" doc:name="API Autodiscovery"/>

## Migrating Global Validation Configuration

Configuration XML for Global Validation Configuration in Studio 6.

    
    
    <validation:config name="Validation_Configuration" doc:name="Validation Configuration"/>

Opposite to Mule Runtime 3.x, adding the Validation Module to the Mule Palette
is required to proceed with the configuration.

  1. In the Mule Palette, click `Add Module` and select `Validation Module` among the available modules.

  2. Add a `Validation Config` Global Configuration Element.

Configuration XML for Global Validation Configuration in Studio 7.

    
    
    <validation:config name="Validation_Config" doc:name="Validation Config" />

## Migrating _get-products-flow_

`get-products-flow` returns products from the database filtering by `Product
Category` and/or `Product Name` also supporting paginated queries with
`offset` and `maxResults` parameters.

![A flow showing a GET request to retrieve products with components including
Source, Transform Message, and Error handling](_images/m3-apikit-based-
example-get-products-flow.png)

Figure 1. get-products-flow in Studio 6

Configuration XML for get-products-flow in Studio 6.

    
    
    <flow name="get-products-flow">
      <message-properties-transformer doc:name="Get Query Params" scope="invocation">
        <add-message-property key="queryOffset" value="#[Integer.valueOf(message.inboundProperties.'http.query.params'.offset)]" />
        <add-message-property key="queryLimit" value="#[Integer.valueOf(message.inboundProperties.'http.query.params'.maxResults)]" />
        <add-message-property key="queryName" value="#[ (message.inboundProperties.'http.query.params'.name != null) ? ('%'+message.inboundProperties.'http.query.params'.name+'%') : '%%']" />
        <add-message-property key="queryCategory" value="#[ (message.inboundProperties.'http.query.params'.category != null) ? ('%'+message.inboundProperties.'http.query.params'.category+'%') : '%%']" />
      </message-properties-transformer>
      <db:select config-ref="MySQL_Configuration" doc:name="Query Products">
        <db:parameterized-query><![CDATA[SELECT  p.id, p.name, p.description, p.product_number, p.manufactured, p.colors, p.categories, p.stock, p.safety_stock_level, p.standard_cost, p.list_price, p.size, p.size_unit_measure_code, p.weight, p.weight_unit_measure_code, p.days_to_manufacture, p.images,  p.modified_date, p.created_date
    FROM product p
    WHERE LOWER(p.name) like #[flowVars.queryName.toLowerCase()] AND LOWER(p.categories) like #[flowVars.queryCategory.toLowerCase()]
    LIMIT #[flowVars.queryLimit]
    OFFSET #[flowVars.queryOffset]]]>
        </db:parameterized-query>
      </db:select>
      <dw:transform-message doc:name="Products to JSON">
        <dw:set-payload resource="classpath:mappings/get-products-response.dwl"/>
      </dw:transform-message>
    </flow>

  1. There are no changes regarding `get-products-flow` definition.
         
         <flow name="get-products-flow">

  2. Create a package with the name `variables` under `src/main/resources` folder.

  3. Create the file `set-queryCategory-variable.dwl` under `src/main/resources/variables` folder and write a DW script for setting `queryCategory` flow variable.
         
         %dw 2.0
         output application/java
         var queryCategory = attributes.queryParams.category
         ---
         if (queryCategory != null)
         	queryCategory
         else
         	'%%'

  4. Create the file `set-queryLimit-variable.dwl` under `src/main/resources/variables` folder and write a DW script for setting `queryLimit` flow variable.
         
         %dw 2.0
         output application/java
         ---
         attributes.queryParams.maxResults as Number

  5. Create the file `set-queryName-variable.dwl` under `src/main/resources/variables` folder and write a DW script for setting `queryName` flow variable.
         
         %dw 2.0
         output application/java
         var queryName = attributes.queryParams.name
         ---
         if (queryName != null)
         	queryName
         else
         	'%%'

  6. Create the file `set-queryOffset-variable.dwl` under `src/main/resources/variables` folder and write a DW script for setting `queryOffset` flow variable.
         
         %dw 2.0
         output application/java
         ---
         attributes.queryParams.offset as Number

  7. Add a `Transform component` to replace the logic inside `message-properties-transformer` and set the variables `queryOffset`, `queryLimit`, `queryName` and `queryCategory` referencing to its DW script.
         
         <flow name="get-products-flow">
           <ee:transform doc:name="Get Query Params" doc:id="ab756164-e1df-4fc5-8fbe-8f4f8cafc2f6">
             <ee:message />
             <ee:variables>
              <ee:set-variable variableName="queryOffset" resource="variables/set-queryOffset-variable.dwl" />
              <ee:set-variable variableName="queryLimit" resource="variables/set-queryLimit-variable.dwl" />
              <ee:set-variable variableName="queryName" resource="variables/set-queryName-variable.dwl" />
              <ee:set-variable variableName="queryCategory" resource="variables/set-queryCategory-variable.dwl" />
            </ee:variables>
          </ee:transform>
         </flow>

  8. Add a `db:select` element, referencing the MySQL Global Configuration. Use the colon (:) syntax in parametrized queries. Parameters must be supplied as key-value pairs into the `db:input-parameters` element.
         
         <db:select config-ref="MySQL_Configuration" doc:name="Query Products">
           <db:sql >SELECT  p.id, p.name, p.description, p.product_number, p.manufactured, p.colors, p.categories, p.stock, p.safety_stock_level, p.standard_cost, p.list_price, p.size, p.size_unit_measure_code, p.weight, p.weight_unit_measure_code, p.days_to_manufacture, p.images,  p.modified_date, p.created_date
         FROM product p
         WHERE LOWER(p.name) like :name AND LOWER(p.categories) like :category
         LIMIT :limit
         OFFSET :offset</db:sql>
           <db:input-parameters ><![CDATA[#[{'name' : lower(vars.queryName), 'category': lower(vars.queryCategory), 'limit': vars.queryLimit, 'offset': vars.queryOffset}]]]></db:input-parameters>
         </db:select>

  9. Create a package with the name `mappings` under `src/main/resources` folder.

  10. Create the file `get-products-response.dwl` under `src/main/resources/mappings` folder.

  11. Migrate `get-products-response.dwl` DW 1.0 script to DW 2.0.

Transformation for get-products-response in DW 1.0.

         
         %dw 1.0
         %output application/json
         ---
         payload map {
         	id: $.id,
         	categories: ($.categories default "") splitBy ",",
         	colors: ($.colors default "") splitBy ",",
         	images: ($.images default "") splitBy ",",
         	createdDate: $.created_date as :string {format: "yyyy-MM-dd"},
         	modifiedDate: $.modified_date as :string {format: "yyyy-MM-dd"},
         	safetyStockLevel: $.safety_stock_level as :number,
         	stock: $.stock as :number,
         	daysToManufacture: $.days_to_manufacture,
         	name: $.name,
         	description: $.description,
         	listPrice: $.list_price,
         	manufactured: $.manufactured,
         	productNumber: $.product_number,
         	size: $.size,
         	sizeUnitMeasureCode: $.size_unit_measure_code,
         	standardCost: $.standard_cost,
         	weightUnitMeasureCode: $.weight_unit_measure_code,
         	weight: $.weight
         }

Transformation for get-products-response in DW 2.0.

         
         %dw 2.0
         output application/json
         ---
         payload map {
         	id: $.id,
         	categories: ($.categories default "") splitBy ",",
         	colors: ($.colors default "") splitBy ",",
         	images: ($.images default "") splitBy ",",
         	createdDate: $.created_date as String {format: "yyyy-MM-dd"},
         	modifiedDate: $.modified_date as String {format: "yyyy-MM-dd"},
         	safetyStockLevel: $.safety_stock_level as Number,
         	stock: $.stock as Number,
         	daysToManufacture: $.days_to_manufacture,
         	name: $.name,
         	description: $.description,
         	listPrice: $.list_price,
         	manufactured: $.manufactured,
         	productNumber: $.product_number,
         	size: $.size,
         	sizeUnitMeasureCode: $.size_unit_measure_code,
         	standardCost: $.standard_cost,
         	weightUnitMeasureCode: $.weight_unit_measure_code,
         	weight: $.weight
         }

  12. Finally, add a `Transform component` that sets the payload using the DW 2.0 transformation.
         
         <flow name="get-products-flow">
         	<!-- more logic here -->
         	<ee:transform doc:name="Products to JSON">
         		<ee:message>
         			<ee:set-payload resource="mappings/get-products-response.dwl" />
         		</ee:message>
         	</ee:transform>
         </flow>

Configuration XML for get-products-flow in Studio 7.

    
    
    <flow name="get-products-flow">
      <ee:transform doc:name="Get Query Params" doc:id="ab756164-e1df-4fc5-8fbe-8f4f8cafc2f6">
        <ee:message />
        <ee:variables>
          <ee:set-variable variableName="queryOffset" resource="variables/set-queryOffset-variable.dwl" />
          <ee:set-variable variableName="queryLimit" resource="variables/set-queryLimit-variable.dwl" />
          <ee:set-variable variableName="queryName" resource="variables/set-queryName-variable.dwl" />
          <ee:set-variable variableName="queryCategory" resource="variables/set-queryCategory-variable.dwl" />
        </ee:variables>
      </ee:transform>
      <db:select config-ref="MySQL_Configuration" doc:name="Query Products">
        <db:sql>SELECT p.id, p.name, p.description, p.product_number,
    				p.manufactured, p.colors, p.categories, p.stock,
    				p.safety_stock_level, p.standard_cost, p.list_price, p.size,
    				p.size_unit_measure_code, p.weight, p.weight_unit_measure_code,
    				p.days_to_manufacture, p.images, p.modified_date, p.created_date
    				FROM product p
    				WHERE LOWER(p.name) like :name AND LOWER(p.categories) like :category
    				LIMIT :limit
    				OFFSET :offset</db:sql>
        <db:input-parameters><![CDATA[#[{'name' : lower(vars.queryName), 'category': lower(vars.queryCategory), 'limit': vars.queryLimit, 'offset': vars.queryOffset}]]]></db:input-parameters>
      </db:select>
      <ee:transform doc:name="Products to JSON">
        <ee:message>
          <ee:set-payload resource="mappings/get-products-response.dwl" />
        </ee:message>
      </ee:transform>
    </flow>

![A flow showing the process for getting products with components including
Source, Transform Message, and Error handling](_images/m4-apikit-based-
example-get-products-flow.png)

Figure 2. get-products-flow in Studio 7

## Migrating _get-product-by-id-flow_

`get-product-by-id-flow` returns a product from the database filtering by
`id`. If there isn’t a product with the required id, an `HTTP 404 Not Found`
error is returned.

![A flow showing the process to retrieve a product by ID, including validation
and JSON transformation](_images/m3-apikit-based-example-get-product-by-id-
flow.png)

Figure 3. get-product-by-id-flow in Studio 6

Configuration XML for get-product-by-id-flow in Studio 6.

    
    
    <flow name="get-product-by-id-flow">
      <db:select config-ref="MySQL_Configuration" doc:name="Get by Id">
        <db:parameterized-query><![CDATA[SELECT p.id, p.name, p.description, p.product_number, p.manufactured, p.colors, p.categories, p.stock, p.safety_stock_level, p.standard_cost, p.list_price, p.size, p.size_unit_measure_code, p.weight, p.weight_unit_measure_code, p.days_to_manufacture, p.images,  p.modified_date, p.created_date FROM product p where p.id = #[id]]]></db:parameterized-query>
      </db:select>
      <validation:is-true config-ref="Validation_Configuration" doc:name="Is Not Empty" exceptionClass="org.mule.module.apikit.exception.NotFoundException" expression="#[payload.size() &gt; 0]"/>
      <dw:transform-message doc:name="Product to JSON">
        <dw:set-payload resource="classpath:mappings/get-product-by-id-response.dwl"/>
      </dw:transform-message>
    </flow>

  1. There are no changes regarding `get-product-by-id-flow` definition.
         
         <flow name="get-product-by-id-flow" />

  2. Create `set-productId-variable.dwl` under `src/main/resources/variables` folder. Add the following logic for getting the `id` from `uriParams`.
         
         %dw 2.0
         output application/java
         ---
         attributes.uriParams.id

  3. Add a `Transform component` that references the DW script that sets a variable with the `productId` value received as a `URI parameter`.
         
         <flow name="get-product-by-id-flow">
           <ee:transform doc:name="Get Uri Params">
             <ee:message />
             <ee:variables>
               <ee:set-variable variableName="id" resource="variables/set-productId-variable.dwl" />
             </ee:variables>
           </ee:transform>
         </flow>

  4. Add a `db:select` element, referencing the MySQL Global Configuration. Use the colon (:) syntax in parametrized queries. Parameters must be supplied as key-value pairs into the `db:input-parameters` element.
         
         <db:select config-ref="MySQL_Configuration" doc:name="Get by Id">
           <db:sql>SELECT p.id, p.name, p.description, p.product_number, p.manufactured, p.colors, p.categories, p.stock, p.safety_stock_level, p.standard_cost, p.list_price, p.size, p.size_unit_measure_code, p.weight, p.weight_unit_measure_code, p.days_to_manufacture, p.images,  p.modified_date, p.created_date
         FROM product p
         where p.id = :id</db:sql>
           <db:input-parameters><![CDATA[#[{'id' : vars.id}]]]></db:input-parameters>
         </db:select>

  5. Add a `validation:is-true` element after the `db:select` that checks if the query has returned results. If not, throw an `APP:NOT_FOUND` error. Notice that as `MEL` has been replaced by `DataWeave` as the default expression language, `[payload.size() > 0]` is rewritten as `[sizeOf(payload) > 0]`.
         
         <validation:is-true doc:name="Is Not Empty" config-ref="Validation_Config" expression="#[sizeOf(payload) &gt; 0]">
           <error-mapping sourceType="VALIDATION:INVALID_BOOLEAN" targetType="APP:NOT_FOUND" />
         </validation:is-true>

  6. Create `get-product-by-id-response.dwl` file under `src/main/resources/mappings` folder and migrate DataWeave script for building JSON response from 1.0 to 2.0.

Transformation for get-product-by-id-response in DW 1.0.

         
         %dw 1.0
         %output application/json
         %var product = payload[0]
         ---
         {
         	id: product.id,
         	name: product.name,
         	description: product.description,
         	manufactured: product.manufactured,
         	productNumber: product.product_number,
         	colors: (product.colors default "") splitBy "," ,
         	categories:(product.categories default "") splitBy "," ,
         	safetyStockLevel: product.safety_socket_level,
         	standardCost: (product.standard_cost default "0.0") as :string {format: "##.##"} as :number,
         	listPrice: (product.list_price default "0.0") as :string {format: "##.##"} as :number,
         	stock: product.stock,
         	safetyStockLevel: product.safety_stock_level,
         	daysToManufacture: product.days_to_manufacture,
         	size: product.size,
         	sizeUnitMeasureCode: product.size_unit_measure_code,
         	weight: product.weight,
         	weightUnitMeasureCode: product.weight_unit_measure_code,
         	daysToManufacture: product.days_to_manufacture,
         	images: (product.images splitBy "," default null),
         	modifiedDate: (product.modified_date default "") as :date {format: "yyyy-MM-dd"},
         	createdDate: (product.created_date default "") as :date {format: "yyyy-MM-dd"}
         
         }

Transformation for get-product-by-id-response.dwl in DW 2.0.

         
         %dw 2.0
         output application/json
         var product = payload[0]
         ---
         {
         	id: product.id,
         	name: product.name,
         	description: product.description,
         	manufactured: product.manufactured,
         	productNumber: product.product_number,
         	colors: (product.colors default "") splitBy "," ,
         	categories:(product.categories default "") splitBy "," ,
         	safetyStockLevel: product.safety_socket_level,
         	standardCost: (product.standard_cost default "0.0") as String {format: "##.##"} as Number,
         	listPrice: (product.list_price default "0.0") as String {format: "##.##"} as Number,
         	stock: product.stock,
         	safetyStockLevel: product.safety_stock_level,
         	daysToManufacture: product.days_to_manufacture,
         	size: product.size,
         	sizeUnitMeasureCode: product.size_unit_measure_code,
         	weight: product.weight,
         	weightUnitMeasureCode: product.weight_unit_measure_code,
         	daysToManufacture: product.days_to_manufacture,
         	images: (product.images splitBy "," default null),
         	modifiedDate: (product.modified_date default "") as Date {format: "yyyy-MM-dd"},
         	createdDate: (product.created_date default "") as Date {format: "yyyy-MM-dd"}
         }

  7. Finally, add a `Transform component` that sets the payload using the DW 2.0 transformation.
         
         <ee:transform doc:name="Product to JSON">
           <ee:message>
             <ee:set-payload resource="mappings/get-product-by-id-response.dwl" />
           </ee:message>
         </ee:transform>

Configuration XML for get-product-by-id-flow in Studio 7.

    
    
    <flow name="get-product-by-id-flow">
      <ee:transform doc:name="Get Uri Params">
        <ee:message />
        <ee:variables>
          <ee:set-variable variableName="id" resource="variables/set-productId-variable.dwl" />
        </ee:variables>
      </ee:transform>
      <db:select config-ref="MySQL_Configuration" doc:name="Get by Id">
        <db:sql>SELECT p.id, p.name, p.description, p.product_number, p.manufactured, p.colors, p.categories, p.stock, p.safety_stock_level, p.standard_cost, p.list_price, p.size, p.size_unit_measure_code, p.weight, p.weight_unit_measure_code, p.days_to_manufacture, p.images,  p.modified_date, p.created_date
    FROM product p
    where p.id = :id</db:sql>
        <db:input-parameters><![CDATA[#[{'id' : vars.id}]]]></db:input-parameters>
      </db:select>
      <validation:is-true doc:name="Is Not Empty" config-ref="Validation_Config" expression="#[sizeOf(payload) &gt; 0]">
        <error-mapping sourceType="VALIDATION:INVALID_BOOLEAN" targetType="APP:NOT_FOUND" />
      </validation:is-true>
      <ee:transform doc:name="Product to JSON">
        <ee:message>
          <ee:set-payload resource="mappings/get-product-by-id-response.dwl" />
        </ee:message>
      </ee:transform>
    </flow>

![A flow showing a GET request by ID with components including Source,
Transform Message, and Error handling](_images/m4-apikit-based-example-get-
product-by-id-flow.png)

Figure 4. get-product-by-id-flow in Studio 7

## Migrating _post-product-flow_

`post-product-flow` inserts a product in the database.

![A flow showing the process for posting a product with components including
Source, Transactional, and Error handling](_images/m3-apikit-based-example-
post-product-flow.png)

Figure 5. post-product-flow in Studio 6

Configuration XML for post-product-flow in Studio 6.

    
    
    <flow name="post-product-flow">
      <set-variable variableName="originalPayload" value="#[payload:java.lang.String]" doc:name="Set Original Payload" />
      <dw:transform-message doc:name="Json to Map">
        <dw:set-payload resource="classpath:mappings/json-product-to-java.dwl"/>
      </dw:transform-message>
      <transactional action="ALWAYS_BEGIN" doc:name="Transactional">
        <db:insert config-ref="MySQL_Configuration" doc:name="Insert Product" autoGeneratedKeys="true" autoGeneratedKeysColumnNames="id" target="#[payload]">
          <db:parameterized-query><![CDATA[insert into product(name, description, product_number, manufactured, colors, categories, stock, safety_stock_level, standard_cost, list_price, size, size_unit_measure_code, weight, weight_unit_measure_code, days_to_manufacture, images, modified_date, created_date) values(#[payload.name],#[payload.description], #[payload.productNumber], #[payload.manufactured], #[payload.colors],  #[payload.categories], #[payload.stock], #[payload.safetyStockLevel], #[payload.standardCost], #[payload.listPrice], #[payload.size], #[payload.sizeUnitMeasureCode], #[payload.weight], #[payload.weightUnitMeasureCode], #[payload.daysToManufacture], #[payload.images], CURDATE(), CURDATE() );]]></db:parameterized-query>
        </db:insert>
      </transactional>
      <dw:transform-message doc:name="Database to Json">
        <dw:input-variable doc:sample="json.json" mimeType="application/json" variableName="originalPayload" />
        <dw:set-payload resource="classpath:mappings/post-product-response.dwl"/>
      </dw:transform-message>
    </flow>

  1. There are no changes regarding `post-product-flow` definition.
         
         <flow name="post-product-flow" />

  2. Create a `json-to-java.dwl` file into `src/main/resources/mappings` folder to transform the JSON request into a JAVA map.
         
         %dw 2.0
         output application/java
         ---
         payload

  3. Create a `json-product-to-java.dwl` file into `src/main/resources/mappings` and migrate the original script from DW 1.0 to 2.0.

Transformation for json-product-to-java.dwl in DW 1.0.

         
         %dw 1.0
         %output application/java
         ---
         {
         	categories: payload.categories joinBy ",",
         	colors: payload.colors joinBy ",",
         	daysToManufacture: payload.daysToManufacture,
         	description: payload.description,
         	images: payload.images joinBy ",",
         	listPrice: payload.listPrice,
         	(manufactured: 1) when payload.manufactured == true,
         	(manufactured: 0) when payload.manufactured == false,
         	name: payload.name,
         	productNumber: payload.productNumber,
         	safetyStockLevel: payload.safetyStockLevel,
         	size: payload.size,
         	sizeUnitMeasureCode: payload.sizeUnitMeasureCode,
         	standardCost: payload.standardCost,
         	stock: payload.stock,
         	weight: payload.weight,
         	weightUnitMeasureCode: payload.weightUnitMeasureCode
         }

Transformation for json-product-to-java.dwl in DW 2.0.

         
         %dw 2.0
         output application/java
         fun getManufacturedCode(value) =
         	if (value == true) 1
         	else 0
         ---
         {
         	categories: payload.categories joinBy ",",
         	colors: payload.colors joinBy ",",
         	daysToManufacture: payload.daysToManufacture,
         	description: payload.description,
         	images: payload.images joinBy ",",
         	listPrice: payload.listPrice,
         	manufactured: getManufacturedCode(payload.manufactured),
         	name: payload.name,
         	productNumber: payload.productNumber,
         	safetyStockLevel: payload.safetyStockLevel,
         	size: payload.size,
         	sizeUnitMeasureCode: payload.sizeUnitMeasureCode,
         	standardCost: payload.standardCost,
         	stock: payload.stock,
         	weight: payload.weight,
         	weightUnitMeasureCode: payload.weightUnitMeasureCode
         }

  4. Add a `Transform component` that sets `originalPayload` and `newPayload` using the previously created DataWeave transformations.
         
         <flow name="post-product-flow">
           <ee:transform doc:name="Json to Map">
             <ee:message />
             <ee:variables>
               <ee:set-variable variableName="originalPayload" resource="mappings/json-to-java.dwl" />
               <ee:set-variable variableName="newPayload" resource="mappings/json-product-to-java.dwl" />
             </ee:variables>
           </ee:transform>
         </flow>

  5. For configuring the details of the transaction, replace the Mule 3.x `transactional` scope with the new `try` scope and set the `transactionalAction` attribute to `ALWAYS_BEGIN`.
         
         <try doc:name="Try" transactionalAction="ALWAYS_BEGIN">
         </try>

  6. Add a `db:insert` element into the `Try scope`, referencing the MySQL Global Configuration. Parameters must be supplied as key-value pairs into the `db:input-parameters` element. Notice also the inclusion of `db:auto-generated-keys-column-name` tag for setting the payload with the `ID` that was auto-generated by the Database engine.
         
         <try transactionalAction="ALWAYS_BEGIN" doc:name="Try">
           <db:insert config-ref="MySQL_Configuration" doc:name="Insert Product" autoGenerateKeys="true">
             <db:sql>insert into product(name, description, product_number,
         					manufactured, colors, categories, stock, safety_stock_level,
         					standard_cost, list_price, size, size_unit_measure_code, weight,
         					weight_unit_measure_code, days_to_manufacture, images,
         					modified_date, created_date)
         					values(:name, :description,
         					:product_number, :manufactured, :colors,
         					:categories, :stock,
         					:safety_stock_level, :standard_cost,
         					:list_price, :size,
         					:size_unit_measure_code, :weight,
         					:weight_unit_measure_code,
         					:days_to_manufacture, :images,
         					CURDATE(), CURDATE());
         				</db:sql>
             <db:input-parameters><![CDATA[#[{'name': vars.newPayload.name, 'description': vars.newPayload.description, 'product_number': vars.newPayload.productNumber, 'manufactured': vars.newPayload.manufactured, 'colors': vars.newPayload.colors, 'categories': vars.newPayload.categories, 'stock': vars.newPayload.stock, 'safety_stock_level': vars.newPayload.safetyStockLevel, 'standard_cost': vars.newPayload.standardCost, 'list_price': vars.newPayload.listPrice, 'size': vars.newPayload.size, 'size_unit_measure_code': vars.newPayload.sizeUnitMeasureCode, 'weight': vars.newPayload.weight, 'weight_unit_measure_code': vars.newPayload.weightUnitMeasureCode, 'days_to_manufacture': vars.newPayload.daysToManufacture, 'images': vars.newPayload.images}]]]></db:input-parameters>
             <db:auto-generated-keys-column-names>
               <db:auto-generated-keys-column-name value="id" />
             </db:auto-generated-keys-column-names>
           </db:insert>
         </try>

  7. Create a `post-product-response.dwl` file under `src/main/resources/mappings` and migrate the response transformation from DataWeave 1.0 to 2.0. Notice the difference getting the generated `id` from the payload with the expression `payload.generatedKeys.GENERATED_KEY`.

Transformation for post-product-response.dwl in DW 1.0.

         
         %dw 1.0
         %output application/json
         ---
         flowVars.originalPayload ++
         id: payload[0].GENERATED_KEY

Transformation for post-product-response.dwl in DW 2.0.

         
         %dw 2.0
         output application/json
         ---
         vars.originalPayload ++
         id: payload.generatedKeys.GENERATED_KEY

  8. Add a `Transform component` and set the payload with the DataWeave script.
         
         <ee:transform doc:name="Database to Json">
           <ee:message>
             <ee:set-payload resource="mappings/post-product-response.dwl" />
           </ee:message>
         </ee:transform>

Configuration XML for post-product-flow in Studio 7.

    
    
    <flow name="post-product-flow">
      <ee:transform doc:name="Json to Map">
        <ee:message />
        <ee:variables>
          <ee:set-variable variableName="originalPayload" resource="mappings/json-to-java.dwl" />
          <ee:set-variable variableName="newPayload" resource="mappings/json-product-to-java.dwl" />
        </ee:variables>
      </ee:transform>
      <try transactionalAction="ALWAYS_BEGIN" doc:name="Try">
        <db:insert config-ref="MySQL_Configuration" doc:name="Insert Product" autoGenerateKeys="true">
          <db:sql>insert into product(name, description, product_number,
    					manufactured, colors, categories, stock, safety_stock_level,
    					standard_cost, list_price, size, size_unit_measure_code, weight,
    					weight_unit_measure_code, days_to_manufacture, images,
    					modified_date, created_date)
    					values(:name, :description,
    					:product_number, :manufactured, :colors,
    					:categories, :stock,
    					:safety_stock_level, :standard_cost,
    					:list_price, :size,
    					:size_unit_measure_code, :weight,
    					:weight_unit_measure_code,
    					:days_to_manufacture, :images,
    					CURDATE(), CURDATE());
    				</db:sql>
          <db:input-parameters><![CDATA[#[{'name': vars.newPayload.name, 'description': vars.newPayload.description, 'product_number': vars.newPayload.productNumber, 'manufactured': vars.newPayload.manufactured, 'colors': vars.newPayload.colors, 'categories': vars.newPayload.categories, 'stock': vars.newPayload.stock, 'safety_stock_level': vars.newPayload.safetyStockLevel, 'standard_cost': vars.newPayload.standardCost, 'list_price': vars.newPayload.listPrice, 'size': vars.newPayload.size, 'size_unit_measure_code': vars.newPayload.sizeUnitMeasureCode, 'weight': vars.newPayload.weight, 'weight_unit_measure_code': vars.newPayload.weightUnitMeasureCode, 'days_to_manufacture': vars.newPayload.daysToManufacture, 'images': vars.newPayload.images}]]]></db:input-parameters>
          <db:auto-generated-keys-column-names>
            <db:auto-generated-keys-column-name value="id" />
          </db:auto-generated-keys-column-names>
        </db:insert>
      </try>
      <ee:transform doc:name="Database to Json">
        <ee:message>
          <ee:set-payload resource="mappings/post-product-response.dwl" />
        </ee:message>
      </ee:transform>
    </flow>

![A flow showing the process to post a new product, including JSON
transformation and database interaction](_images/m4-apikit-based-example-post-
product-flow.png)

Figure 6. post-product-flow in Studio 7

## Migrating _put-product-flow_

`put-product-flow` updates a product in the database based on the specified
`id`.

![A flow for updating a product with transactional error handling and status
updates](_images/m3-apikit-based-example-put-product-flow.png)

Figure 7. put-product-flow in Studio 6

Configuration XML for put-product-flow in Studio 6.

    
    
    <flow name="put-product-flow">
      <dw:transform-message doc:name="JSon to Product">
        <dw:set-payload resource="classpath:mappings/put-json-product-to-java.dwl"/>
      </dw:transform-message>
      <transactional action="ALWAYS_BEGIN" doc:name="Transactional">
        <db:update config-ref="MySQL_Configuration" doc:name="Update Product">
          <db:parameterized-query><![CDATA[update product set name = #[payload.name], description = #[payload.description], product_number = #[payload.productNumber], manufactured = #[payload.manufactured], colors = #[payload.colors], categories= #[payload.categories], stock = #[payload.stock], safety_stock_level = #[payload.safetyStockLevel], standard_cost = #[payload.standardCost], list_price = #[payload.listPrice], size = #[payload.size], size_unit_measure_code = #[payload.sizeUnitMeasureCode], weight = #[payload.weight], weight_unit_measure_code = #[payload.weightUnitMeasureCode], days_to_manufacture = #[payload.daysToManufacture], images = #[payload.images],  modified_date = CURDATE() where id = #[id]]]></db:parameterized-query>
        </db:update>
      </transactional>
      <set-payload value="#[NullPayload.getInstance()]" doc:name="Set Payload" />
      <set-property propertyName="http.status" value="204" doc:name="Set Status" />
    </flow>

  1. There are no changes regarding `put-product-flow` definition.
         
         <flow name="put-product-flow" />

  2. Create a `put-json-product-to-java.dwl` file under `src/main/resources/mappings` folder and migrate the original script from DW 1.0 to 2.0.

Transformation for put-json-product-to-java.dwl in DW 1.0.

         
         %dw 1.0
         %output application/java
         ---
         {
         	categories: payload.categories joinBy ",",
         	colors: payload.colors joinBy ",",
         	daysToManufacture: payload.daysToManufacture,
         	description: payload.description,
         	images: payload.images joinBy ",",
         	listPrice: payload.listPrice,
         	manufactured: payload.manufactured,
         	name: payload.name,
         	productNumber: payload.productNumber,
         	safetyStockLevel: payload.safetyStockLevel,
         	size: payload.size,
         	sizeUnitMeasureCode: payload.sizeUnitMeasureCode,
         	standardCost: payload.standardCost,
         	stock: payload.stock,
         	weight: payload.weight,
         	weightUnitMeasureCode: payload.weightUnitMeasureCode
         }

Transformation for put-json-product-to-java.dwl in DW 2.0.

         
         %dw 2.0
         output application/java
         ---
         {
         	categories: payload.categories joinBy ",",
         	colors: payload.colors joinBy ",",
         	daysToManufacture: payload.daysToManufacture,
         	description: payload.description,
         	images: payload.images joinBy ",",
         	listPrice: payload.listPrice,
         	manufactured: payload.manufactured,
         	name: payload.name,
         	productNumber: payload.productNumber,
         	safetyStockLevel: payload.safetyStockLevel,
         	size: payload.size,
         	sizeUnitMeasureCode: payload.sizeUnitMeasureCode,
         	standardCost: payload.standardCost,
         	stock: payload.stock,
         	weight: payload.weight,
         	weightUnitMeasureCode: payload.weightUnitMeasureCode
         }

  3. Add a `Transform component` that sets `updatePayload` using the previously created DataWeave transformation and `id` with `variables/set-productId-variable.dwl` script.
         
         <flow name="put-product-flow">
           <ee:transform doc:name="JSon to Product">
             <ee:message />
             <ee:variables >
               <ee:set-variable variableName="updatePayload" resource="mappings/put-json-product-to-java.dwl" />
               <ee:set-variable variableName="id" resource="variables/set-productId-variable.dwl" />
             </ee:variables>
           </ee:transform>
         </flow>

  4. For configuring the details of the transaction, replace the Mule 3.x `transactional` scope with the new `try` scope and set the `transactionalAction` attribute to `ALWAYS_BEGIN`.
         
         <try doc:name="Try" transactionalAction="ALWAYS_BEGIN">
         </try>

  5. Add a `db:update` element into the `Try scope`, referencing the MySQL Global Configuration. Parameters must be supplied as key-value pairs into the `db:input-parameters` element.
         
         <try doc:name="Try" transactionalAction="ALWAYS_BEGIN">
           <db:update config-ref="MySQL_Configuration" doc:name="Update Product">
             <db:sql >update product
         set name = :name, description = :description, product_number = :product_number, manufactured = :manufactured, colors = :colors, categories= :categories, stock = :stock, safety_stock_level = :safety_stock_level, standard_cost = :standard_cost, list_price = :list_price, size = :size, size_unit_measure_code = :size_unit_measure_code, weight = :weight, weight_unit_measure_code = :weight_unit_measure_code, days_to_manufacture = :days_to_manufacture, images = :images,  modified_date = CURDATE()
         where id = :id</db:sql>
             <db:input-parameters ><![CDATA[#[{'name': vars.updatePayload.name, 'description': vars.updatePayload.description, 'product_number': vars.updatePayload.productNumber, 'manufactured': vars.updatePayload.manufactured, 'colors': vars.updatePayload.colors, 'categories': vars.updatePayload.categories, 'stock': vars.updatePayload.stock, 'safety_stock_level': vars.updatePayload.safetyStockLevel, 'standard_cost': vars.updatePayload.standardCost, 'list_price': vars.updatePayload.listPrice, 'size': vars.updatePayload.size, 'size_unit_measure_code': vars.updatePayload.sizeUnitMeasureCode, 'weight': vars.updatePayload.weight, 'weight_unit_measure_code': vars.updatePayload.weightUnitMeasureCode, 'days_to_manufacture': vars.updatePayload.daysToManufacture, 'images': vars.updatePayload.images, 'id': vars.id}]]]></db:input-parameters>
           </db:update>
         </try>

  6. Add a `Transform component` and set the `httpStatus` variable with `204` using `set-httpStatus-with-204.dwl` file into `src/main/resources/variables`.
         
         <ee:transform doc:name="Set Status">
           <ee:message />
           <ee:variables >
             <ee:set-variable variableName="httpStatus" resource="variables/set-httpStatus-with-204.dwl" />
           </ee:variables>
         </ee:transform>

Configuration XML for put-product-flow in Studio 7.

    
    
    <flow name="put-product-flow">
      <ee:transform doc:name="JSon to Product">
        <ee:message />
        <ee:variables >
          <ee:set-variable variableName="updatePayload" resource="mappings/put-json-product-to-java.dwl" />
          <ee:set-variable variableName="id" resource="variables/set-productId-variable.dwl" />
        </ee:variables>
      </ee:transform>
      <try doc:name="Try" transactionalAction="ALWAYS_BEGIN">
        <db:update config-ref="MySQL_Configuration" doc:name="Update Product">
          <db:sql >update product
    set name = :name, description = :description, product_number = :product_number, manufactured = :manufactured, colors = :colors, categories= :categories, stock = :stock, safety_stock_level = :safety_stock_level, standard_cost = :standard_cost, list_price = :list_price, size = :size, size_unit_measure_code = :size_unit_measure_code, weight = :weight, weight_unit_measure_code = :weight_unit_measure_code, days_to_manufacture = :days_to_manufacture, images = :images,  modified_date = CURDATE()
    where id = :id</db:sql>
          <db:input-parameters ><![CDATA[#[{'name': vars.updatePayload.name, 'description': vars.updatePayload.description, 'product_number': vars.updatePayload.productNumber, 'manufactured': vars.updatePayload.manufactured, 'colors': vars.updatePayload.colors, 'categories': vars.updatePayload.categories, 'stock': vars.updatePayload.stock, 'safety_stock_level': vars.updatePayload.safetyStockLevel, 'standard_cost': vars.updatePayload.standardCost, 'list_price': vars.updatePayload.listPrice, 'size': vars.updatePayload.size, 'size_unit_measure_code': vars.updatePayload.sizeUnitMeasureCode, 'weight': vars.updatePayload.weight, 'weight_unit_measure_code': vars.updatePayload.weightUnitMeasureCode, 'days_to_manufacture': vars.updatePayload.daysToManufacture, 'images': vars.updatePayload.images, 'id': vars.id}]]]></db:input-parameters>
        </db:update>
      </try>
      <ee:transform doc:name="Set Status">
        <ee:message />
        <ee:variables >
          <ee:set-variable variableName="httpStatus" resource="variables/set-httpStatus-with-204.dwl" />
        </ee:variables>
      </ee:transform>
    </flow>

![A flow showing the process to update a product, including JSON
transformation and status setting](_images/m4-apikit-based-example-put-
product-flow.png)

Figure 8. put-product-flow in Studio 7

## Migrating _delete-product-flow_

`delete-product-flow` deletes the product record from the MySQL database with
the `id` specified as a `URI parameter` returning an HTTP 204 status code.

![A flow showing the process for deleting a product with components including
Source, Transactional, and Error handling](_images/m3-apikit-based-example-
delete-product-flow.png)

Figure 9. delete-product-flow in Studio 6

Configuration XML for delete-product-flow in Studio 6.

    
    
    <flow name="delete-product-flow">
      <transactional action="ALWAYS_BEGIN" doc:name="Transactional">
        <db:delete config-ref="MySQL_Configuration" doc:name="Delete Product">
          <db:parameterized-query><![CDATA[delete from product where id=#[id]]]></db:parameterized-query>
        </db:delete>
      </transactional>
      <set-payload value="#[NullPayload.getInstance()]" doc:name="Set Payload"/>
      <set-property propertyName="http.status" value="204" doc:name="Set Status"/>
    </flow>

  1. There are no changes regarding `delete-product-flow` definition.
         
         <flow name="delete-product-flow" />

  2. Add a `Transform component` that references the DW script that sets a variable with the `productId` value received as a `URI parameter`.
         
         <flow name="delete-product-flow">
           <ee:transform doc:name="Set productId variable">
             <ee:message />
             <ee:variables>
               <ee:set-variable variableName="productId" resource="variables/set-productId-variable.dwl" />
             </ee:variables>
           </ee:transform>
         </flow>

  3. For configuring the details of the transaction, replace the Mule 3.x `transactional` scope with the new `try` scope and set the `transactionalAction` attribute to `ALWAYS_BEGIN`.
         
         <try doc:name="Try" transactionalAction="ALWAYS_BEGIN">
         </try>

  4. Add a `db:delete` element into the `Try scope`, referencing the MySQL Global Configuration. Parameters must be supplied as key-value pairs into the `db:input-parameters` element. Opposite to Mule 3.x, the previously defined `productId` flow variable must be accessed as `vars.productId` instead of `flowVars.productId`.
         
         <try doc:name="Try" transactionalAction="ALWAYS_BEGIN">
           <db:delete config-ref="MySQL_Configuration" doc:name="Delete Product">
             <db:sql>delete from product where id=:productId</db:sql>
             <db:input-parameters><![CDATA[#[{'productId' : vars.productId}]]]></db:input-parameters>
           </db:delete>
         </try>

  5. Create a `set-httpStatus-with-204.dwl` file under `src/main/resources/variables` as follows.
         
         %dw 2.0
         output application/java
         ---
         204

  6. Set `httpStatus` variable with the value `204` using a `Transform Component` for defining a `NO CONTENT` response code.
         
         <ee:transform doc:name="Set 204 HTTP Status code">
           <ee:message />
           <ee:variables>
             <ee:set-variable variableName="httpStatus" resource="variables/set-httpStatus-with-204.dwl" />
           </ee:variables>
         </ee:transform>

To return a specific HTTP Status code, instead of setting a `http.status`
property, APIkit in Mule 4 requires setting a variable with the name
`httpStatus`.

Configuration XML for delete-product-flow in Studio 7.

    
    
    <flow name="delete-product-flow">
      <ee:transform doc:name="Set productId variable">
        <ee:message />
        <ee:variables>
          <ee:set-variable variableName="productId" resource="variables/set-productId-variable.dwl" />
        </ee:variables>
      </ee:transform>
      <try doc:name="Try" transactionalAction="ALWAYS_BEGIN">
        <db:delete config-ref="MySQL_Configuration" doc:name="Delete Product">
          <db:sql>delete from product where id=:productId</db:sql>
          <db:input-parameters><![CDATA[#[{'productId' : vars.productId}]]]></db:input-parameters>
        </db:delete>
      </try>
      <ee:transform doc:name="Set 204 HTTP Status code">
        <ee:message />
        <ee:variables>
          <ee:set-variable variableName="httpStatus" resource="variables/set-httpStatus-with-204.dwl" />
        </ee:variables>
      </ee:transform>
    </flow>

![A flow showing the process for deleting a product, including error handling
and HTTP status setting](_images/m4-apikit-based-example-delete-product-
flow.png)

Figure 10. delete-product-flow in Studio 7

## Migrating Backend Flows

To migrate backend flows:

For each Backend Flow generated by APIkit, add a `flow-ref` to its
implementation.

\+ .Configuration XML for Backend Flows in Studio 6.

    
    
    <flow name="get:/product:api-config">
      <flow-ref name="get-products-flow" doc:name="get-products-flow" />
    </flow>
    <flow name="get:/product/{id}:api-config">
      <flow-ref name="get-product-by-id-flow" doc:name="get-product-by-id-flow" />
    </flow>
    <flow name="post:/product:application/json:api-config">
      <flow-ref name="post-product-flow" doc:name="post-product-flow" />
    </flow>
    <flow name="delete:/product/{id}:api-config">
      <flow-ref name="delete-product-flow" doc:name="delete-product-flow" />
    </flow>
    <flow name="put:/product/{id}:application/json:api-config">
      <flow-ref name="put-product-flow" doc:name="put-product-flow" />
    </flow>

+

\+ .Configuration XML for Backend Flows in Studio 7.

    
    
    <flow name="get:\product:api-product-config">
      <flow-ref name="get-products-flow" doc:name="get-products-flow" />
    </flow>
    <flow name="get:\product\(id):api-product-config">
      <flow-ref doc:name="get-product-by-id-flow" name="get-product-by-id-flow"/>
    </flow>
    <flow name="post:\product:application\json:api-product-config">
      <flow-ref name="post-product-flow" doc:name="post-product-flow" />
    </flow>
    <flow name="delete:\product\(id):application\json:api-product-config">
      <flow-ref doc:name="delete-product-flow" doc:id="38894873-9a01-4e59-8362-5eefce5ea043" name="delete-product-flow"/>
    </flow>
    <flow name="put:\product\(id):application\json:api-product-config">
      <flow-ref doc:name="put-product-flow" doc:id="e64cf378-26a2-4435-8d0d-269c50282b3c" name="put-product-flow"/>
    </flow>

## Extending default APIkit Global Exception Strategies

  1. Add `APP:NOT_FOUND` exception type to the ApiKit-generated 404 mapping to handle the exception thrown by the `validation:is-true` element in `get-product-by-id-flow`. You can repeat this process for any other errors you want to map to a specific status code.

Configuration XML for ApiKit Mapping 404 in Studio 6.

         
         <apikit:mapping statusCode="404">
           <apikit:exception value="org.mule.module.apikit.exception.NotFoundException" />
           <set-property propertyName="Content-Type" value="application/json" doc:name="Property" />
           <set-payload value="{ &quot;message&quot;: &quot;Resource not found&quot; }" doc:name="Set Payload" />
         </apikit:mapping>

Configuration XML for ApiKit Mapping 404 in Studio 7.

         
         <on-error-propagate type="APIKIT:NOT_FOUND, APP:NOT_FOUND" doc:name="On Error Propagate" enableNotifications="true" logException="true">
           <ee:transform xmlns:ee="http://www.mulesoft.org/schema/mule/ee/core" xsi:schemaLocation="http://www.mulesoft.org/schema/mule/ee/core http://www.mulesoft.org/schema/mule/ee/core/current/mule-ee.xsd" doc:id="70f893cb-6106-42d9-9a95-e201e9349159">
             <ee:message>
               <ee:set-payload><![CDATA[%dw 2.0
         output application/json
         ---
         {message: "Resource not found"}]]></ee:set-payload>
             </ee:message>
             <ee:variables>
               <ee:set-variable variableName="httpStatus"><![CDATA[404]]></ee:set-variable>
             </ee:variables>
           </ee:transform>
         </on-error-propagate>

  2. Add a Generic ApiKit Mapping 500 for all the non previously managed exceptions.

Configuration XML for Generic ApiKit Mapping 500 in Studio 6.

         
         <apikit:mapping-exception-strategy name="api-apiKitGlobalExceptionMapping">
           <!-- other exception strategies here -->
           <apikit:mapping statusCode="500">
             <apikit:exception value="java.lang.Exception" />
             <set-property propertyName="Content-Type" value="application/json" doc:name="Property" />
             <set-payload value="{ &quot;message&quot;: &quot;Internal Server Error&quot; }" doc:name="Set Payload" />
           </apikit:mapping>
         </apikit:mapping-exception-strategy>

Configuration XML for Generic ApiKit Mapping 500 in Studio 7.

         
         <error-handler>
           <!-- other exception strategies here -->
           <on-error-propagate doc:name="On Error Propagate" enableNotifications="true" logException="true">
             <ee:transform xmlns:ee="http://www.mulesoft.org/schema/mule/ee/core" xsi:schemaLocation="http://www.mulesoft.org/schema/mule/ee/core http://www.mulesoft.org/schema/mule/ee/core/current/mule-ee.xsd" doc:id="7e8049ff-cae6-4937-8569-c36bb7f06dad">
               <ee:message>
                 <ee:set-payload><![CDATA[%dw 2.0
         output application/json
         ---
         {message: "Internal Server Error"}]]></ee:set-payload>
               </ee:message>
               <ee:variables>
                 <ee:set-variable variableName="httpStatus"><![CDATA[500]]></ee:set-variable>
               </ee:variables>
             </ee:transform>
           </on-error-propagate>
         </error-handler>

