# XML Cryptography

## Configure XML Encryption from Anypoint Studio

To configure XML encryption from Anypoint Studio, follow these steps:

  1. From the Mule palette, add **Crypto** to your project.

See [Install the Extension](cryptography#install-crypto-module) for
instructions.

  2. Select the desired operation, and drag the component to the flow:

![A palette menu for adding XML cryptographic operations](_images/mruntime-
crypto-xml-add.png)

  3. Open the component properties and select an existing **Module configuration** , or create a new one by specifying the **Keystore** , **Type** (JKS, JCEKS, PKCS12) and **Password**.

You can also add symmetric or asymmetric key information to be used in the
sign operations:

![Global configuration properties for Crypto JCE](_images/mruntime-crypto-jce-
global-config.png)

  4. Configure **Key selection** by using a **Key id** value previously defined in the module configuration, or define a new one for this operation:

![A configuration panel for XML signing](_images/mruntime-crypto-xml-
config.png)

  5. Select **Digest Algorithm** , **Canonicalization Algorithm** , **Type** , and **Element path**.

## Encrypting

This example configures a keystore that contains a symmetric key that will
later be used for encryption.

Example: JCE Configuration

    
    
    <crypto:jce-config name="symmetricConfig" keystore="secret.jks" password="mule1234" type="JCEKS">
        <crypto:jce-key-infos>
            <crypto:jce-symmetric-key-info keyId="mySymKey" alias="aes128test" password="mule1234"/>
        </crypto:jce-key-infos>
    </crypto:jce-config>

In the next example, the XML encrypt operation is used to encrypt a specific
element of the XML document.

Example: Using the Encrypt Operation

    
    
    <crypto:xml-encrypt config-ref="symmetricConfig" keyId="mySymKey" algorithm="AES_CBC" elementPath="//song"/>

The `elementPath` is an XPath expression that identifies the element to
encrypt. Depending on your needs, you can use a symmetric or asymmetric key
for encrypting an XML document.

## Decrypting

Example: JCE Configuration

    
    
    <crypto:jce-config name="jceConfig" keystore="keystore.jks" password="mule1234">
        <crypto:jce-key-infos>
            <crypto:jce-symmetric-key-info keyId="mySymKey" alias="aes128test" password="mule1234"/>
            <crypto:jce-asymmetric-key-info keyId="myAsymKey" alias="test1" password="test1234"/>
        </crypto:jce-key-infos>
    </crypto:jce-config>

In the next example, the XML decrypt operation (`crypto:xml-decrypt`) is used
to decrypt an XML document. The operation uses the asymmetric key stored in
the referenced keystore.

Example: Using the Decrypt Operation

    
    
    <crypto:xml-decrypt config-ref="jceConfig" keyId="myAsymKey"/>

Depending on your needs, you can use a symmetric or asymmetric key for
decryption.

## Signing

Example: JCE Configuration

    
    
    <crypto:jce-config name="asymmetricConfig" keystore="keystore.jks" password="mule1234">
        <crypto:jce-key-infos>
            <crypto:jce-asymmetric-key-info keyId="myAsymKey" alias="test1" password="test1234"/>
        </crypto:jce-key-infos>
    </crypto:jce-config>

The next example uses the asymmetric key to sign an XML document by creating
an XML envelope and inserting the signature inside the content that is being
signed.

Example: Enveloped Signature

    
    
    <crypto:xml-sign config-ref="asymmetricConfig" keyId="myAsymKey" type="ENVELOPING" digestAlgorithm="SHA256" elementPath="/PurchaseOrder/Buyer"/>

In the next example, a detached XML signature is created based on an element
of the XML document. Instead of being inserted in the signed content, the
detached signature is returned as a separate XML element.

Example: Detached Signature

    
    
    <crypto:xml-sign config-ref="asymmetricConfig" keyId="myAsymKey" type="DETACHED" digestAlgorithm="SHA256" elementPath="/PurchaseOrder/Buyer"/>

### Selecting the Signing Algorithm

In the **XML Sign** operation, the `digestAlgorithm` parameter defines the
hashing algorithm applied to the content before signing, for example SHA1,
SHA256, or SHA512.

However, the final XML signature algorithm is not manually selected. It is
automatically determined based on the type of key (RSA, DSA, EC, HMAC)
configured in the module.

The signing process combines the chosen hash algorithm `digestAlgorithm` with
the key type to produce the signature method used in the XML document.

For example:

  * An RSA key with `digestAlgorithm=SHA256` results in the `rsa-sha256` signature method.

  * A DSA key with `digestAlgorithm=SHA1` results in the `dsa-sha1` signature method.

  * An EC key with `digestAlgorithm=SHA256` results in the `ecdsa-sha256` signature method.

If you want to use a different signature method, you must change the type of
key in the `digestAlgorithm` parameter configuration. It is not currently
possible to manually select the signature method within the operation.

## Validating a Signature

Example: JCE Configuration

    
    
    <crypto:jce-config name="asymmetricConfig" keystore="keystore.jks" password="mule1234">
        <crypto:jce-key-infos>
            <crypto:jce-asymmetric-key-info keyId="myAsymKey" alias="test1" password="test1234"/>
        </crypto:jce-key-infos>
    </crypto:jce-config>

In the next example, the asymmetric key is used to validate the signature of
the XML element specified by the `elementPath` XPath expression.

Example: Using the Validate Operation

    
    
    <crypto:xml-validate config-ref="asymmetricConfig" keyId="myAsymKey" elementPath="/PurchaseOrder/Buyer"/>

If the document has multiple signatures, set `elementPath` to select the
signature to validate. Specify a signed element using an XPath expression to
validate the signature for that element.

## Targeting a Custom Namespace by Using elementPath

To sign or validate an XML element that is inside a custom namespace, specify
the namespace by using the XPath functions: [namespace-
uri](https://developer.mozilla.org/en-US/docs/Web/XPath/Functions/namespace-
uri) and [local-name](https://developer.mozilla.org/en-
US/docs/Web/XPath/Functions/local-name).

For example, consider the following document:

    
    
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope/">
        <FirstElement>
            <!-- Some content -->
        </FirstElement>
        <SecondElement>
            <!-- Additional content -->
        </SecondElement>
    </soap:Envelope>

To target the content of `FirstElement` inside `soap:Envelope`, you specify
the `xmlns:soap` namespace. The XML schema for `xmlns:soap` is defined in
`<http://www.w3.org/2003/05/soap-envelope/>`.

The following example shows an `xml-sign` operation configured to sign
`FirstElement`:

    
    
    <crypto:xml-sign
        config-ref="asymmetricConfig"
        keyId="myAsymKey"
        type="DETACHED"
        digestAlgorithm="SHA256"
        elementPath="/*[namespace-uri()='http://www.w3.org/2003/05/soap-envelope/' and local-name()='Envelope']/FirstElement"/>

Note that the `elementPath` expression specifies the `xmlns:soap` namespace.

## Reference

### Module Configuration

JCE Configuration for Java keystores and inline keys to sign or encrypt XML
documents or elements.

#### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Name | String | The name for this configuration. Connectors reference the configuration with this name. |  | **x**  
Keystore |  String | Path to the keystore file. |  |   
Type |  Enumeration, one of:

  * `JKS`
  * `JCEKS`
  * `PKCS12`

| Type of the keystore. | `JKS` |   
Password |  String | Password for unlocking the keystore. |  |   
Jce Key Infos |  Array of One of:

  * Jce Asymmetric Key Info
  * Jce Symmetric Key Info

| List of keys to be considered, with internal IDs for referencing them. |  |   
Expiration Policy |  Expiration Policy | Configures the minimum amount of time that a dynamic configuration instance can remain idle before the runtime considers it eligible for expiration. This does not mean that the platform will expire the instance at the exact moment that it becomes eligible. The runtime will actually purge the instances when it sees it fit. |  |   
  
## Xml Decrypt Operation

`<crypto:xml-decrypt>`

Decrypts the XML document.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | the document to decrypt | `#[payload]` |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Key Id |  String | The key ID, as defined in the JCE configuration. |  |   
Jce Key Info |  One of:

  * Jce Asymmetric Key Info
  * Jce Symmetric Key Info

| An inline key definition. |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
  
### Output Type

Binary

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:KEY`

  * `CRYPTO:PASSPHRASE`

  * `CRYPTO:PARAMETERS`

  * `CRYPTO:DECRYPTION`

## Xml Encrypt Operation

`<crypto:xml-encrypt>`

Encrypt the XML document.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | the document to encrypt | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `AES_CBC`
  * `AES_GCM`
  * `TRIPLEDES`

| the algorithm for encryption | `AES_CBC` |   
Element Path |  String | the path to the element to encrypt, if empty the whole document is considered |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Key Id |  String | The key ID, as defined in the JCE configuration. |  |   
Jce Key Info |  One of:

  * Jce Asymmetric Key Info
  * Jce Symmetric Key Info

| An inline key definition. |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
  
### Output Type

Binary

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:ENCRYPTION`

  * `CRYPTO:KEY`

  * `CRYPTO:PARAMETERS`

## Xml Sign Operation

`<crypto:xml-sign>`

Sign an XML document.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | the XML document to sign | `#[payload]` |   
Digest Algorithm |  Enumeration, one of:

  * `RIPEMD160`
  * `SHA1`
  * `SHA256`
  * `SHA512`

| the hashing algorithm for signing | `SHA256` |   
Canonicalization Algorithm |  Enumeration, one of:

  * `EXCLUSIVE`
  * `EXCLUSIVE_WITH_COMMENTS`
  * `INCLUSIVE`
  * `INCLUSE_WITH_COMMENTS`

| the canonicalization method for whitespace and namespace unification | `EXCLUSIVE` |   
Type |  Enumeration, one of:

  * `DETACHED`
  * `ENVELOPED`
  * `ENVELOPING`

| the type of signature to create | `ENVELOPED` |   
Element Path |  String | for internally detached signatures, an unambiguous XPath expression resolving to the element to sign |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Key Id |  String | The key ID, as defined in the JCE configuration. |  |   
Jce Key Info |  One of:

  * Jce Asymmetric Key Info
  * Jce Symmetric Key Info

| An inline key definition. |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
  
### Output Type

Binary

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:KEY`

  * `CRYPTO:PASSPHRASE`

  * `CRYPTO:SIGNATURE`

## Xml Validate Operation

`<crypto:xml-validate>`

Validate an XML signed document.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | Specifies the document to verify (includes the signature). | `#[payload]` |   
Element Path |  String | For internally detached signatures, an unambiguous XPath expression that resolves to the signed element. |  |   
Use inline certificate if present |  Boolean | Specify whether or not to validate the signature against a certificate contained in the `ds:Signature` element, if the certificate is present. | `"false"` |   
Key Id |  String | Specifies the key ID, as defined in the JCE configuration. |  |   
Jce Key Info |  One of:

  * Jce Asymmetric Key Info
  * Jce Symmetric Key Info

| An inline key definition. |  |   
  
### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:PARAMETERS`

  * `CRYPTO:VALIDATION`

## Types Definition

### Expiration Policy

Field | Type | Description | Default Value | Required  
---|---|---|---|---  
Max Idle Time |  Number | A scalar time value for the maximum amount of time a dynamic configuration instance should be allowed to be idle before it’s considered eligible for expiration |  |   
Time Unit |  Enumeration, one of:

  * `NANOSECONDS`
  * `MICROSECONDS`
  * `MILLISECONDS`
  * `SECONDS`
  * `MINUTES`
  * `HOURS`
  * `DAYS`

| A time unit that qualifies the maxIdleTime attribute |  |   
  
### Repeatable In Memory Stream

Field | Type | Description | Default Value | Required  
---|---|---|---|---  
Initial Buffer Size |  Number | This is the amount of memory that will be allocated in order to consume the stream and provide random access to it. If the stream contains more data than can be fit into this buffer, then it will be expanded by according to the `bufferSizeIncrement` attribute, with an upper limit of `maxInMemorySize`. |  |   
Buffer Size Increment |  Number | This is by how much will be buffer size by expanded if it exceeds its initial size. Setting a value of zero or lower will mean that the buffer should not expand, meaning that a `STREAM_MAXIMUM_SIZE_EXCEEDED` error will be raised when the buffer gets full. |  |   
Max Buffer Size |  Number | This is the maximum amount of memory that will be used. If more than that is used then a `STREAM_MAXIMUM_SIZE_EXCEEDED` error will be raised. A value lower or equal to zero means no limit. |  |   
Buffer Unit |  Enumeration, one of:

  * `BYTE`
  * `KB`
  * `MB`
  * `GB`

| The unit in which all these attributes are expressed |  |   
  
### Repeatable File Store Stream

Field | Type | Description | Default Value | Required  
---|---|---|---|---  
Max In Memory Size |  Number | Defines the maximum memory that the stream should use to keep data in memory. If more than that is consumed then it will start to buffer the content on disk. |  |   
Buffer Unit |  Enumeration, one of:

  * `BYTE`
  * `KB`
  * `MB`
  * `GB`

| The unit in which maxInMemorySize is expressed |  |   
  
### Jce Asymmetric Key Info

Field | Type | Description | Default Value | Required  
---|---|---|---|---  
Key Id |  String | Internal key ID for referencing from operations. |  | x  
Alias |  String | Alias of the key in the keystore. |  | x  
Password |  String | Password used to unlock the private part of the key. |  |   
  
### Jce Symmetric Key Info

Field | Type | Description | Default Value | Required  
---|---|---|---|---  
Key Id |  String | Internal key ID for referencing from operations. |  | x  
Alias |  String | Alias of the key in the keystore. |  | x  
Password |  String | Password used to unlock the key. |  | x

