# Connect to SFTP Servers Dynamically Example

Many integrations require connecting to different servers based on a specific
condition, such as:

  * Connecting to different invoice storage servers depending on the branch that emits an invoice

  * Connecting to different servers depending on an integration subject, such as in a multi-tenant use case

To accommodate these use cases, the Anypoint Connector for SFTP (SFTP
Connector) global configuration element supports parameter expressions that
evaluate these conditions and connect to the correct server.

The following example shows how to configure SFTP Connector to connect
dynamically to multiple servers:

  1. An HTTP **Listener** source initiates the flow by reading random content posted via HTTP.

  2. The File Connector **Read** operation loads a recipients CSV file that contains a random set of SFTP destinations, with columns such as `host`, `user`, and `port`.

  3. A DataWeave transformation maps the content and splits the CSV file.

  4. A **For Each** component and an SFTP **Write** operation write the contents into each of the SFTP destinations.

On each **For Each** iteration, the expressions set in the SFTP global
configuration element resolve to a different value and establish different
connections to each of the servers.

To test this example, create the Mule application, and run and test the
application with curl commands:

![Connect to SFTP Servers Dynamically](_images/sftp-connection-
dynamically.png)

Figure 1. Connect to SFTP Servers Dynamically flow

## Create the Mule Application

To create the Mule flow:

  1. In the **Mule Palette** view, select **HTTP > Listener**.

  2. Drag **HTTP Listener** to the Studio canvas.

  3. On the **HTTP Listener** configuration screen, optionally change the value of the **Display Name** field.

  4. Set the **Path** field to `/multitenant`

  5. Click the plus sign (**+**) next to the **Connector configuration** field to configure a global element that can be used by all instances of HTTP Listener in the app.

  6. On the **General** tab, set the following fields:

     * **Host** : `All Interfaces [0.0.0.0] (default)`

     * **Port** : `8081`

  7. Click **OK**.

  8. Drag a **Set Variable** component to the right of the **HTTP Listener** source.

  9. Set the **Name** field to `content` and the **Value** field to `#[payload]`.

  10. Drag the File Connector **Read** operation to the right of the **Set Variable** component.

  11. Set the **File Path** field to `recipients.csv`.  
This reads a CSV file that contains a random set of SFTP destinations with
columns such as `host`, `user`, and `port`.

  12. Click the plus sign (**+**) next to the **Connector configuration** field to configure a global element that can be used by all instances of File Connector in the app.

  13. Accept the default settings and click **OK**.

  14. On the **MIME Type** tab of the **Read** operation, for the **MIME Type** field, select `application/csv`.

### Configure Additional Components and Operations

Continue creating your Mule application by adding additional components and
operations:

  1. In Studio, drag a **Transform Message** component to the right of the **Read** operation.

  2. In the **Output** section of the component, add the following DataWeave code to map the columns of the CSV file:

DataWeave script:

         
         %dw 2.0
         output application/java
         ---
         payload map using (row = $) {
            host: row.Host,
            user: row.User,
            password: row.Password}

  3. Drag a **For Each** component to the right of the **Transform Message** component.

  4. Drag an SFTP **Write** operation into the **For Each** component.  
On each For Each iteration, the **Write** operation writes the contents into
each of the SFTP destinations.

  5. Click the plus sign (**+**) next to the **Connector configuration** field to configure a global element that can be used by all instances of SFTP Write operation in the app, and set the following fields:

     * **Host** : `#[payload.host]`

     * **Username** : `#[payload.username]`

     * **Password** : `#[payload.password]`

  6. Click **OK**.

  7. On the configuration screen, set the **Path** field to `demo.txt`.

  8. Set the **Content** field to `payload`.

  9. Drag a **Set Payload** component to the right of the **For Each** component.

  10. Set the **Value** field to `Multicast Ok`.

## Run and Test your Mule Application

After creating your Mule application, run and test it:

  1. In Studio, save your Mule app.

  2. Click the project name in **Package Explorer** and then click **Run** > **Run As** > **Mule Application**.

  3. Open a browser and type `http://0.0.0.0:8081/multitenant`.  

Note about Mule 4 behavior for Mule 3 users:

  * The information posted through the HTTP Listener source is written to each SFTP site multiple times.

Because the listener makes use of the [repeatable streams feature](../../mule-
runtime/latest/streaming-about), you do not need to worry about consuming the
stream multiple times.

  * The For Each component automatically goes through each line of the CSV file.

In Mule 3, you first needed to transform the CSV file into a Java structure,
but because Mule 4 is now Java agnostic, this works out-of-the-box.

When reading or listing files, you might be interested in the file’s metadata
(for example, the file name, full path, size, timestamp). The connector uses
the Mule message attributes to access this information.

## XML for Connecting to SFTP Servers Dynamically

Paste this code into your Studio XML editor to quickly load the flow for this
example into your Mule app:

    
    
    <?xml version="1.0" encoding="UTF-8"?>
    
    <mule xmlns:sftp="http://www.mulesoft.org/schema/mule/sftp" xmlns:ee="http://www.mulesoft.org/schema/mule/ee/core"
    	xmlns:file="http://www.mulesoft.org/schema/mule/file"
    	xmlns:http="http://www.mulesoft.org/schema/mule/http" xmlns="http://www.mulesoft.org/schema/mule/core" xmlns:doc="http://www.mulesoft.org/schema/mule/documentation" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.mulesoft.org/schema/mule/core http://www.mulesoft.org/schema/mule/core/current/mule.xsd
    http://www.mulesoft.org/schema/mule/http http://www.mulesoft.org/schema/mule/http/current/mule-http.xsd
    http://www.mulesoft.org/schema/mule/file http://www.mulesoft.org/schema/mule/file/current/mule-file.xsd
    http://www.mulesoft.org/schema/mule/ee/core http://www.mulesoft.org/schema/mule/ee/core/current/mule-ee.xsd
    http://www.mulesoft.org/schema/mule/sftp http://www.mulesoft.org/schema/mule/sftp/current/mule-sftp.xsd">
    	<http:listener-config name="HTTP_Listener_config" >
    		<http:listener-connection host="0.0.0.0" port="8081" />
    	</http:listener-config>
    	<file:config name="File_Config" doc:name="File Config"  />
    	<sftp:config name="SFTP_Config" doc:name="SFTP Config"  >
    		<sftp:connection host="#[payload.host]" username="#[payload.user]" password="#[payload.password]" />
    	</sftp:config>
    	<flow name="SFTPexample" >
    		<http:listener doc:name="Listener" config-ref="HTTP_Listener_config" path="/multitenant"/>
    		<set-variable value="#[payload]" doc:name="Set Variable" variableName="content"/>
    		<file:read doc:name="Read" config-ref="File_Config" path="recipients.csv" outputMimeType="application/csv"/>
    		<ee:transform doc:name="Transform Message" >
    			<ee:message >
    				<ee:set-payload ><![CDATA[%dw 2.0
    output application/java
    ---
    payload map using (row = $) {
       host: row.Host,
       user: row.User,
       password: row.Password}]]></ee:set-payload>
    			</ee:message>
    		</ee:transform>
    		<foreach doc:name="For Each" >
    			<sftp:write doc:name="Write" config-ref="SFTP_Config" path="demo.txt">
    			</sftp:write>
    		</foreach>
    		<set-payload value="Multicast OK" doc:name="Set Payload" />
    	</flow>
    </mule>

## See Also

  * [SFTP Connector Examples](sftp-examples)

  * [MuleSoft Help Center](https://help.mulesoft.com)

