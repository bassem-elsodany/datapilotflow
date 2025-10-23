# Mule Message Structure

A Mule message is the part of the Mule event that serves as a container for
message content and metadata, typically from external sources, as it is
processed within flows of a Mule app.

The Mule message is immutable, so every change to a Mule message results in
the creation of a new instance. Each processor in a flow that receives a
message returns a new Mule message consisting of these parts:

  * A message `payload`, which contains the body of the message. For example: the content of a file, the HTTP body, a record from a database, or the response to a REST or Web Service request.

  * Message `attributes`, which are metadata associated with the payload, such as HTTP headers and query parameters.

![A Mule message including attributes and payload](_images/mule-message-
structure-82af1.png)

A Mule event source triggers a process that creates a Mule event with a Mule
message and executes the Mule flow that contains the event source. For
example, this process begins each time an [HTTP Listener](../../http-
connector/latest/http-listener-ref) source receives a request or the
[Scheduler](scheduler-concept) executes.

After the flow begins its execution, downstream processors (such as Core
components, File read operations, or the HTTP request operation) can then
retrieve, set, and process Mule message data (payload and attributes) that
reside in the Mule event according to their configurations.

Note that in Anypoint Studio, the [DataSense
Explorer](../../studio/latest/datasense-explorer) shows the structure of a
Mule message at any given point of the flow.

## Message Payload

The message payload contains the content or body of a message. For example,
the payload can contain the results of an HTTP request, the content of records
you retrieve through the Select operation of the Database connector, or the
content of a file that you retrieve through a Read operation to the File or
FTP connector.

The payload content changes as it travels through a flow when message
processors in a Mule flow set it, enrich it, transform it into a new format,
extract information from it, or even store it in a Mule event variable and
produce a new payload.

You can select the payload of a Mule message through a DataWeave expression
that uses the [Mule Runtime variable](../../dataweave/latest/dataweave-
variables-context), `payload`.

For example, a Logger component configured to display the `payload` of a
response to an HTTP request for the JSON content at
`https://jsonplaceholder.typicode.com/users` outputs the following example
JSON content in the Studio console:

Example: HTTP Response Payload

    
    
    [
      {
        "id": 1,
        "name": "Leanne Graham",
        "username": "Bret",
        "email": "Sincere@april.biz",
        "address": {
          "street": "Kulas Light",
          "city": "Gwenborough",
          "zipcode": "92998-3874",
          "geo": {
            "lat": "-37.3159",
            "lng": "81.1496"
          }
        }
      },
      {
        "id": 2,
        "name": "Ervin Howell",
        "username": "Antonette",
        "email": "Shanna@melissa.tv",
        "address": {
          "street": "Victor Plains",
          "city": "Wisokyburgh",
          "zipcode": "90566-7771",
          "geo": {
            "lat": "-43.9509",
            "lng": "-34.4618"
          }
        }
      }
    ]

A Logger component set to display the `payload` for the output of a File Read
operation for a simple JSON file can output the following example JSON content
in the Studio console:

Example: File Payload

    
    
    { "hello" : "world" }

The next message processor in the flow can then act on this payload, for
example, by selecting the value of the JSON object in the payload with
`payload.'hello'` to replace the preceding JSON payload with the string,
`"world"`.

## Attributes

Attributes contain the metadata associated with the body (or payload) of the
message. The specific attributes of a message depend on the connector (such as
HTTP, FTP, File) associated with the message. Metadata can consist of headers
and properties received or returned by a connector, as well as other metadata
that is populated by the connector or through a Core component, such as
Transform Message.

You can select attributes of a Mule message through a DataWeave expression
that uses the [Mule Runtime variable](../../dataweave/latest/dataweave-
variables-context), `attributes`.

For example, when using the `attributes` variable to display HTTP response
metadata through a Logger component, the Studio console outputs the following
example HTTP response attributes:

Example: HTTP Response Attributes

    
    
    {
       Status Code=200
       Reason Phrase=OK
       Headers=[
          date=Sun, 20 Jan 2019 19:13:51 GMT
          content-type=text/html;
          charset=UTF-8
          transfer-encoding=chunked
          connection=keep-alive
          set-cookie=__cfduid=d03462713a0b2c57c8d2ad3bf311287041548011631;
          expires=Mon, 20-Jan-20 19:13:51 GMT;
          path=/;
          domain=.typicode.com;
          HttpOnly
          x-powered-by=Express
          vary=Origin, Accept-Encoding
          access-control-allow-credentials=true
          cache-control=public, max-age=14400
          last-modified=Tue, 15 Jan 2019 18:17:15 GMT
          via=1.1 vegur
          cf-cache-status=HIT
          expires=Sun, 20 Jan 2019 23:13:51 GMT
          expect-ct=max-age=604800,
          report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"
          server=cloudflare
          cf-ray=49c3dc570c2f281c-SJC
       ]
    }

The example is a response from an HTTP Request operation to the web page
`https://jsonplaceholder.typicode.com/users`.

Notice that each attribute is a key-value pair separated by an equal sign
(`=`). When using a connector or component (such as the Logger) in your flow,
you can use the `attribute` variable with specific attributes and their inner
attributes to select the attribute values that you require, such as the status
code or content type. For example, you can select the values of attributes in
an HTTP response using the following syntax:

  * `attributes.statusCode` to select an HTTP status code like `200`.

  * `attributes.headers.date` to select `Sun, 20 Jan 2019 18:54:54 GMT` from the header of an HTTP response.

  * `attributes.headers.'content-type'` to select the HTTP content type `application/json`.

To select the value of inner attributes like `content-type`, you must surround
the name `content-type` in quotes. You do not need quotes around values like
`date` because DataWeave applies the rules described in Valid Identifiers for
Attribute Names to inner values. To understand why you use `statusCode` for
the selector instead of `'Status Code'` or `"Status Code"` to select the
status code value, see the note in that section.

For file metadata, the attributes are different. For example, when using the
`attributes` variable to display file metadata through a Logger component, the
Studio console displays the following example content:

Example: File Attributes

    
    
    LocalFileAttributes[
      lastModifiedTime=2019-01-20T08:17:55,
      lastAccessTime=2019-01-20T10:54:55,
      creationTime=2019-01-20T08:17:55,
      size=22,
      regularFile=true,
      directory=false,
      symbolicLink=false,
      path=/Users/me/Desktop/myJson.json,
      fileName=myJson.json

Notice that each attribute is a key-value pair (such as
`fileName=myJson.json`). You can select the value of an attribute by
referencing its key, for example:

  * `attributes.'fileName'` to return the file name: `myJson.json`.

  * `attributes.size` to return the size of the file: `22`.

### Valid Identifiers for Attribute Names

You can access and declare attribute names that follow the rules described in
[Rules for Declaring Valid Identifiers](../../dataweave/latest/dataweave-
language-introduction#valid-identifiers) without using any quotation marks.

To use an attribute name that is not a valid identifier, surround the
attribute name with any of the following characters:

  * Single quotation marks (`'`)

  * Double quotation marks (`"`)

  * Backticks (```)

For example, consider the following DataWeave variable declaration:

    
    
    var myVar = {
                  id : "1234",
                  "123 abc !@#" : "some_value"
                }

Because attribute name `123 abc !@#` is not a valid identifier, you must use
quotation marks or backticks to declare it.

To access the value from attribute `123 abc !@#`, which is `"some_value"`, use
quotation marks or backticks:

    
    
    myVar.'123 abc !@#'

Using quotation marks or backticks to declare an attribute or select a value
from an attribute when the attribute name is a valid identifier is optional.

In the previous variable declaration example, attribute `id` is declared
without using any quotation marks. To access the value stored in attribute
`id`, you can use any of the following methods:

  * `myVar.id`

  * `myVar.'id'`

  * `myVar."id"`

  * `myVar.`id``

Note that human-readable names, such as `Status Code`, that you see in console
output for top-level attributes can differ from the name to use for selecting
the attribute, which is `statusCode`. Putting quotes around the human-readable
name `Status Code` returns `null` instead of making that top-level attribute
selectable. You can find the syntax to use for selecting the top-level
attribute names, such as `Status Code`, `Reason Phrase`, and `Headers`,
through [autocompletion in Studio](../../studio/latest/datasense-
concept#using-datasense-for-autocomplete) or in the connector documentation,
for example, in [HTTP Request](../../http-connector/latest/http-connector-xml-
reference#http-request) documentation.

## See Also

  * [Predefined Variables](../../dataweave/latest/dataweave-variables-context)

  * [Mule Events](about-mule-event)

  * [DataWeave Selectors](../../dataweave/latest/dataweave-selectors)

  * [Set Payload Transformer](set-payload-transformer-reference)

