# JCE Cryptography

The JCE strategy enables you to use the wider range of cryptography
capabilities provided by the Java Cryptography Extension.

You can use cryptography capabilities in two ways:

  * Password-based encryption (PBE):  
This method enables you to encrypt and sign content by providing only an
encryption password.

  * Key-based encryption:  
Similar to how PGP and XML encryption works, this method enables you to
configure a symmetric or asymmetric key to perform encryption and signing
operations.

You can encrypt all, or part of a message using any of these two methods.

## PBE

This method applies a hash function over the provided password to generate a
symmetric key that is compatible with standard encryption algorithms. Because
PBE only requires a password, a global configuration element is not needed for
the PBE operations.

### Configure Password-Based Encryption from Anypoint Studio

To configure PBE from Anypoint Studio, follow these steps:

  1. From the Mule palette, add **Crypto** to your project.

See [Install the Extension](cryptography#install-crypto-module) for
instructions.

  2. Select the desired operation, and drag the component to the flow:

![A palette menu for adding password-based encryption modules in a
cryptographic flow](_images/mruntime-crypto-pbe-add.png)

  3. In the component view, configure the **Algorithm** and **Password** properties:

![A configuration settings for JCE encrypt PBE with algorithm and password
options](_images/mruntime-crypto-pbe-config.png)

### XML Examples

The following are XML examples for each of the PBE operations:

  * PBE Encryption
        
        <crypto:jce-encrypt-pbe password="a-Sup3r_Secure-Passw0rd"/>

If no algorithm is specified, `PBEWithHmacSHA256AndAES_128` is used.

  * PBE Decryption
        
        <crypto:jce-decrypt-pbe algorithm="PBEWithHmacSHA256AndAES_128" password="a-Sup3r_Secure-Passw0rd"/>

  * PBE Signature
        
        <crypto:jce-sign-pbe password="a-Sup3r_Secure-Passw0rd"/>

If no algorithm is specified, `PBEWithHmacSHA256` is used.

  * PBE Signature Validation
        
        <crypto:jce-validate-pbe password="a-Sup3r_Secure-Passw0rd" algorithm="PBEWithHmacSHA256" expected="#[vars.expectedSignature]"/>

The `expected` parameter defines the signature used to validate the message.

## Key-Based Encryption

Configure a symmetric or asymmetric key to perform encryption and signing
operations.

### Configure Key-Based Encryption from Anypoint Studio

To configure key-based encryption operations from Anypoint Studio, follow
these steps:

  1. From the Mule palette, add **Crypto** to your project.

See [Install the Extension](cryptography#install-crypto-module) for
instructions.

  2. Select the desired operation, and drag the component to the flow:

![A crypto-examples project with components for encryption and
decryption](_images/mruntime-crypto-jce-add.png)

  3. Open the component properties and select an existing module configuration, or create a new one by specifying values for **Keystore** , **Type** (JKS, JCEKS, PKCS12), and **Password**.

You can also add symmetric or asymmetric key information to be used in the
sign operations:

![Global configuration properties for Crypto JCE with keystore
details](_images/mruntime-crypto-jce-global-config.png)

  4. Configure **Key selection** by using a **Key id** value previously defined in the module configuration, or define a new one for this operation:

![A configuration panel for JCE encryption showing settings for content,
algorithm, and key selection](_images/mruntime-crypto-jce-config.png)

  5. Select the algorithm to use during the operation.

### XML Examples

The following XML examples show a JCE configuration that defines symmetric and
asymmetric keys and different operations using these keys.

  * Configuration

In this example, a keystore with different types of keys is defined in a JCE
configuration:

        
        <crypto:jce-config name="jceConfig" keystore="jce/keys.jceks" password="123456" type="JCEKS">
            <crypto:jce-key-infos>
                <crypto:jce-symmetric-key-info keyId="aes128" alias="aes128" password="123456"/>
                <crypto:jce-symmetric-key-info keyId="blowfish" alias="blowfish" password="123456"/>
                <crypto:jce-symmetric-key-info keyId="hmacsha256" alias="hmacsha256" password="123456"/>
                <crypto:jce-asymmetric-key-info keyId="rsa" alias="myrsakey" password="123456"/>
                <crypto:jce-asymmetric-key-info keyId="dsa" alias="mydsakey" password="123456"/>
            </crypto:jce-key-infos>
        </crypto:jce-config>

  * Asymmetric Encryption

The following example operations use the asymmetric keys defined in the
previous configuration.

Encrypting a Message

        
        <crypto:jce-encrypt config-ref="jceConfig" keyId="rsa" algorithm="RSA"/>

Decrypting a Message

        
        <crypto:jce-decrypt config-ref="jceConfig" keyId="rsa" algorithm="RSA"/>

  * Symmetric Encryption

The following example operations use the symmetric keys defined in the
previous configuration.

Encrypting a Message

        
        <crypto:jce-encrypt config-ref="jceConfig" keyId="aes128" algorithm="AES"/>

Decrypting a Message

        
        <crypto:jce-decrypt config-ref="jceConfig" keyId="aes128" algorithm="AES"/>

  * Signature and Validation

The following are examples of sign and validate operations that use a key
defined in the previous configuration:

Signing a Message

        
        <crypto:jce-sign config-ref="jceConfig" keyId="dsa" algorithm="SHA256withDSA"/>

Validating a Signature

        
        <crypto:jce-validate config-ref="jceConfig" keyId="dsa" algorithm="SHA256withDSA" expected="#[vars.expectedSignature]"/>

The `expected` parameter defines the signature used to validate the message.

## Reference

### Module Configuration

JCE configuration for Java keystores and inline keys.

#### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Name | String | The name for this configuration. Connectors reference the configuration with this name. |  | **x**  
Keystore |  String | Path to the keystore file. |  | X  
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
  
## Jce Decrypt Operation

`<crypto:jce-decrypt>`

Decrypt a stream using JCE, with a key.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | You can decrypt all, or part of a message by using a DataWeave expression.  
For example, you can set Content to `#[payload.name]` to decrypt only an encrypted variable called `name` from the payload | `#[payload]` |   
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Output Encoding |  String | The encoding of the payload that this operation outputs. |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Cipher |  String | A raw cipher string in the form "algorithm/mode/padding" according to the Java crypto documentation, for example `AES/CBC/PKCS5Padding`. Note that GCM mode is currently not supported, and not all algorithm/mode/padding combinations are valid. |  |   
Algorithm |  Enumeration, one of:

  * `AES`
  * `AESWrap`
  * `ARCFOUR`
  * `Blowfish`
  * `DES`
  * `DESede`
  * `RC2`
  * `DESedeWrap`
  * `RSA`

|  Algorithm from a list of valid definitions. When you specify this field,
Mule automatically selects the mode and padding to use according to the
following list:

  * `AES/CBC/PKCS5Padding`
  * `AESWrap/ECB/NoPadding`
  * `ARCFOUR/ECB/NoPadding`
  * `Blowfish/CBC/PKCS5Padding`
  * `DES/CBC/PKCS5Padding`
  * `DESede/CBC/PKCS5Padding`
  * `RC2/CBC/PKCS5Padding`
  * `DESedeWrap/CBC/NoPadding`
  * `RSA/ECB/OAEPWithSHA-256AndMGF1Padding`

|  |   
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

## Jce Encrypt Operation

`<crypto:jce-encrypt>`

Encrypt a stream using JCE, with a key.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | You can encrypt all, or part of a message by using a DataWeave expression.  
For example, you can set Content to `#[payload.name]` to encrypt only a variable called `name` from the payload | `#[payload]` |   
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Output Encoding |  String | The encoding of the payload that this operation outputs. |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Cipher |  String | A raw cipher string in the form "algorithm/mode/padding" according to the Java crypto documentation, for example `AES/CBC/PKCS5Padding`. Note that GCM mode is currently not supported, and not all algorithm/mode/padding combinations are valid. |  |   
Algorithm |  Enumeration, one of:

  * `AES`
  * `AESWrap`
  * `ARCFOUR`
  * `Blowfish`
  * `DES`
  * `DESede`
  * `RC2`
  * `DESedeWrap`
  * `RSA`

|  Algorithm from a list of valid definitions. When you specify this field,
Mule automatically selects the mode and padding to use according to the
following list:

  * `AES/CBC/PKCS5Padding`
  * `AESWrap/ECB/NoPadding`
  * `ARCFOUR/ECB/NoPadding`
  * `Blowfish/CBC/PKCS5Padding`
  * `DES/CBC/PKCS5Padding`
  * `DESede/CBC/PKCS5Padding`
  * `RC2/CBC/PKCS5Padding`
  * `DESedeWrap/CBC/NoPadding`
  * `RSA/ECB/OAEPWithSHA-256AndMGF1Padding`

|  |   
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

## Jce Sign Operation

`<crypto:jce-sign>`

Sign a stream using JCE, with a key.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | The content to sign | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `MD2withRSA`
  * `MD5withRSA`
  * `SHA1withRSA`
  * `SHA224withRSA`
  * `SHA256withRSA`
  * `SHA384withRSA`
  * `SHA512withRSA`
  * `NONEwithDSA`
  * `SHA1withDSA`
  * `SHA224withDSA`
  * `SHA256withDSA`
  * `HmacMD5`
  * `HmacSHA1`
  * `HmacSHA224`
  * `HmacSHA256`
  * `HmacSHA384`
  * `HmacSHA512`

| The algorithm used for signing | `HmacSHA256` |   
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Key Id |  String | The key ID, as defined in the JCE configuration. |  |   
Jce Key Info |  One of:

  * Jce Asymmetric Key Info
  * Jce Symmetric Key Info

| An inline key definition. |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
  
### Output Type

String

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:KEY`

  * `CRYPTO:PASSPHRASE`

  * `CRYPTO:SIGNATURE`

## Jce Validate Operation

`<crypto:jce-validate>`

Validate a stream against a signature, using a key.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Value |  Binary | the message to authenticate | `#[payload]` |   
Expected |  String | the signature to validate |  | **x**  
Algorithm |  Enumeration, one of:

  * `MD2withRSA`
  * `MD5withRSA`
  * `SHA1withRSA`
  * `SHA224withRSA`
  * `SHA256withRSA`
  * `SHA384withRSA`
  * `SHA512withRSA`
  * `NONEwithDSA`
  * `SHA1withDSA`
  * `SHA224withDSA`
  * `SHA256withDSA`
  * `HmacMD5`
  * `HmacSHA1`
  * `HmacSHA224`
  * `HmacSHA256`
  * `HmacSHA384`
  * `HmacSHA512`

| The algorithm used for signing | `HmacSHA256` |   
Key Id |  String | The key ID, as defined in the JCE configuration. |  |   
Jce Key Info |  One of:

  * Jce Asymmetric Key Info
  * Jce Symmetric Key Info

| An inline key definition. |  |   
  
### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:VALIDATION`

## Jce Decrypt Pbe Operation

`<crypto:jce-decrypt-pbe>`

Decrypt a stream using JCE, with a password.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Content |  Binary | You can decrypt all, or part of a message by using a DataWeave expression.  
For example, you can set Content to `#[payload.name]` to decrypt only an encrypted variable called `name` from the payload | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `PBEWithMD5AndDES`
  * `PBEWithMD5AndTripleDES`
  * `PBEWithSHA1AndDESede`
  * `PBEWithSHA1AndRC2_40`
  * `PBEWithSHA1AndRC2_128`
  * `PBEWithSHA1AndRC4_40`
  * `PBEWithSHA1AndRC4_128`
  * `PBEWithHmacSHA1AndAES_128`
  * `PBEWithHmacSHA224AndAES_128`
  * `PBEWithHmacSHA256AndAES_128`
  * `PBEWithHmacSHA384AndAES_128`
  * `PBEWithHmacSHA512AndAES_128`
  * `PBEWithHmacSHA1AndAES_256`
  * `PBEWithHmacSHA224AndAES_256`
  * `PBEWithHmacSHA256AndAES_256`
  * `PBEWithHmacSHA384AndAES_256`
  * `PBEWithHmacSHA512AndAES_256`

| The algorithm for generating a key from the password | `PBEWithHmacSHA256AndAES_128` |   
Password |  String | The password for decryption |  | **x**  
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Output Encoding |  String | The encoding of the payload that this operation outputs. |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
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

## Jce Encrypt Pbe Operation

`<crypto:jce-encrypt-pbe>`

Encrypt a stream using JCE, with a password.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Content |  Binary | You can encrypt all, or part of a message by using a DataWeave expression.  
For example, you can set Content to `#[payload.name]` to encrypt only a variable called `name` from the payload | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `PBEWithMD5AndDES`
  * `PBEWithMD5AndTripleDES`
  * `PBEWithSHA1AndDESede`
  * `PBEWithSHA1AndRC2_40`
  * `PBEWithSHA1AndRC2_128`
  * `PBEWithSHA1AndRC4_40`
  * `PBEWithSHA1AndRC4_128`
  * `PBEWithHmacSHA1AndAES_128`
  * `PBEWithHmacSHA224AndAES_128`
  * `PBEWithHmacSHA256AndAES_128`
  * `PBEWithHmacSHA384AndAES_128`
  * `PBEWithHmacSHA512AndAES_128`
  * `PBEWithHmacSHA1AndAES_256`
  * `PBEWithHmacSHA224AndAES_256`
  * `PBEWithHmacSHA256AndAES_256`
  * `PBEWithHmacSHA384AndAES_256`
  * `PBEWithHmacSHA512AndAES_256`

| The algorithm for generating a key from the password | `PBEWithHmacSHA256AndAES_128` |   
Password |  String | The password for encryption |  | **x**  
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Output Encoding |  String | The encoding of the payload that this operation outputs. |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
  
### Output Type

Binary

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:ENCRYPTION`

  * `CRYPTO:KEY`

  * `CRYPTO:PARAMETERS`

## Jce Sign Pbe Operation

`<crypto:jce-sign-pbe>`

Sign a stream using JCE, with a key.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Content |  Binary | the content to sign | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `HmacPBESHA1`
  * `PBEWithHmacSHA1`
  * `PBEWithHmacSHA224`
  * `PBEWithHmacSHA256`
  * `PBEWithHmacSHA384`
  * `PBEWithHmacSHA512`

| The algorithm used for signing | `PBEWithHmacSHA256` |   
Password |  String | The password used to sign |  | **x**  
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
  
### Output Type

String

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:KEY`

  * `CRYPTO:PASSPHRASE`

  * `CRYPTO:SIGNATURE`

## Jce Validate Pbe Operation

`<crypto:jce-validate-pbe>`

Validate a stream against a signature, using a key.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Value |  Binary | the message to authenticate | `#[payload]` |   
Expected |  String | the signature to validate |  | **x**  
Algorithm |  Enumeration, one of:

  * `HmacPBESHA1`
  * `PBEWithHmacSHA1`
  * `PBEWithHmacSHA224`
  * `PBEWithHmacSHA256`
  * `PBEWithHmacSHA384`
  * `PBEWithHmacSHA512`

| The algorithm used for signing | `PBEWithHmacSHA256` |   
Password |  String | The password used to sign |  | **x**  
  
### Throws

  * `CRYPTO:MISSING_KEY`

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

