# PGP Cryptography

Mule can encrypt all or part of a message using Pretty Good Privacy (PGP). PGP
combines data compression and data encryption to secure messages. The
compression reduces the size of the payload to help reduce the transmission
time later on your application.

Due to its increased complexity, PGP encryption is a heavy-load task when
compared to JCE or XML encryption.

This section addresses these scenarios:

  * Encryption: Using another party’s public key to encrypt an outgoing message in a Mule app.

  * Decryption: Using your own private key to decrypt an incoming message in a Mule app.

## Prerequisites

This document assumes that you are reasonably familiar with PGP encryption, as
well as the concepts of public and private keys and asymmetric cryptography.

## Configure PGP Encryption from Anypoint Studio

To configure PGP encryption from Anypoint Studio, follow these steps:

  1. From the Mule palette, add **Crypto** to your project.

See [Install the Extension](cryptography#install-crypto-module) for
instructions.

  2. Select the desired operation, and drag the component to the flow:

![A palette menu for adding PGP encryption and decryption
modules](_images/mruntime-crypto-pgp-add.png)

  3. Open the component properties and select an existing **Module configuration** , or create a new one by specifying the **Public keyring** file and the **Private keyring** file.

You can also add asymmetric key information to be used in the sign operations:

![Global element properties for Crypto PGP with keyring
details](_images/mruntime-crypto-pgp-global-config.png)

  4. Configure **Key selection** by using a **Key id** value previously defined in the module configuration, or define a new one for this operation:

![A configuration settings for PGP encrypt with algorithm and key
selection](_images/mruntime-crypto-pgp-config.png)

  5. Select the algorithm to use during the operation.

## Working with Subkeys

A key can contain subkeys, according to the RFC-4880 standard specification.
When working with subkeys, use the `fingerprint` attribute of the
`<crypto:pgp-asymmetric-key-info>` element in the XML configuration to specify
the key to use.

For example, if you use different keys for signing and encrypting operations,
and each of these keys use different algorithms, like DSA and ElGamal, then
you must reference the appropriate key’s fingerprint, depending on the
operation you want to perform.

In this case, you reference the ElGamal fingerprint to encrypt your messages
and the DSA fingerprint to sign your messages.

## Encrypting Messages with Public Keys

During PGP encryption, the sender of the message must encrypt its content
using the receiver’s public key. So, whenever you want to encrypt messages in
your Mule app using someone else’s public key, you must add the public key to
your key ring. When adding a new PGP configuration to your Mule app, you need
to provide your key ring file so the encryption module can get the public key
from it to encrypt the message.

  1. Use a tool such as GPG Suite to import the other party’s public key. See below for details.

  2. Using the same tool, export the public key, selecting `binary` as the output format. This produces a key ring file with a `.gpg` extension.

  3. Ensure that the key ring (`.gpg`) file is stored where the Mule app can access it during runtime.

Example: PGP Configuration

    
    
    <crypto:pgp-config name="encrypt-conf" publicKeyring="pgp/pubring.gpg">
        <crypto:pgp-key-infos>
            <crypto:pgp-asymmetric-key-info keyId="myself" fingerprint="DE3F10F1B6B7F221"/>
        </crypto:pgp-key-infos>
    </crypto:pgp-config>

  * Using the Encrypt Operation

The next example returns an ASCII-armored encrypted payload, which is suitable
for sending over plain-text channels:

        
        <crypto:pgp-encrypt config-ref="encrypt-conf" keyId="myself"/>

  * Using the Encrypt Binary Operation

If you want to return a binary output instead, you can use the `pgp-encrypt-
binary` operation:

        
        <crypto:pgp-encrypt-binary config-ref="pgp-conf" keyId="recipient"/>

Producing a binary output is faster than using ASCII-armored. However, the
output is not standard and might not be ideal to send to other systems for
decryption.

  * Using the Binary to Armored Operation

If you need to send a payload with binary output to another system, you can
transform it to ASCII-armored:

        
        <crypto:pgp-binary-to-armored/>

This operation has a single input parameter, the message payload to transform.

## Encrypt and Sign

In addition to encrypting, you can atomically encrypt and sign a message,
which returns a message (in ASCII-armored format) similar to the encrypted
one. In this case, the returned message also has a signature inside its
encrypted contents. The signature provides an integrity check of the original
message.

To encrypt and sign, the signer private key (which is usually the sender) must
be in the public key ring. This process always produces an ASCII-armored
output.

Example: PGP Configuration

    
    
    <crypto:pgp-encrypt-and-sign config-ref="encrypt-conf">
        <crypto:encryption-key-selection keyId="recipient-key-id" />
        <crypto:sign-key-selection keyId="signer-key-id" />
    </crypto:pgp-encrypt-and-sign>

## Decrypt

During PGP decryption, the receiver of the message must use its private key to
decrypt the contents of a message that was encrypted using a public key.
Therefore, the receiver must distribute its public key to those who will use
it to send encrypted messages.

Example: PGP Configuration

    
    
    <crypto:pgp-config name="decrypt-conf" privateKeyring="pgp/secring.gpg">
        <crypto:pgp-key-infos>
            <crypto:pgp-asymmetric-key-info keyId="myself" fingerprint="DE3F10F1B6B7F221" passphrase="mule1234"/>
        </crypto:pgp-key-infos>
    </crypto:pgp-config>

In the example above, notice that you need to provide at least three
parameters to be able to use the private key ring in the decrypt operation:

  * Key ID (`keyId`): the internal ID that will allow you to reference this key from an operation.

  * Key Fingerprint (`fingerprint`): The last 16 characters of your key fingerprint, which can be obtained from your external GPG tool (such as GPG Keychain).

  * Passphrase (`passphrase`): The passphrase of the private key.

Example: Using the Decrypt Operation

    
    
    <crypto:pgp-decrypt config-ref="decrypt-conf"/>

## Signing

Sign a message using a configured private key.

Example: PGP Configuration

    
    
    <crypto:pgp-config name="sign-conf" privateKeyring="pgp/secring.gpg">
        <crypto:pgp-key-infos>
            <crypto:pgp-asymmetric-key-info keyId="myself" fingerprint="DE3F10F1B6B7F221" passphrase="mule1234"/>
        </crypto:pgp-key-infos>
    </crypto:pgp-config>

Example: Using the Sign Operation

    
    
    <crypto:pgp-sign config-ref="sign-conf" keyId="myself"/>

## Validating a Signature

Validate the signature of a message using the signer’s public key.

Example: PGP Configuration

    
    
    <crypto:pgp-config name="validate-conf" publicKeyring="pgp/pubring.gpg">
        <crypto:pgp-key-infos>
            <crypto:pgp-asymmetric-key-info keyId="signer" fingerprint="DE3F10F1B6B7F221"/>
        </crypto:pgp-key-infos>
    </crypto:pgp-config>

Example: Using the Validate Operation

    
    
    <crypto:pgp-validate config-ref="validate-conf" value="#[payload]" expected="#[vars.expected]"/>

## Reference

### Module Configuration

Keystore configuration for PGP. Contains a list of keys with internal names to
be used in the operations.

#### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Name | String | The name for this configuration. Connectors reference the configuration with this name. |  | **x**  
Public Keyring |  String | Public key ring file. |  |   
Private Keyring |  String | Private key ring file. |  |   
Pgp Key Infos |  Array of One of:

  * Pgp Asymmetric Key Info

| List of keys to be considered, with internal IDs for referencing them. |  |   
Expiration Policy |  Expiration Policy | Configures the minimum amount of time that a dynamic configuration instance can remain idle before the runtime considers it eligible for expiration. This does not mean that the platform will expire the instance at the exact moment that it becomes eligible. The runtime will actually purge the instances when it sees it fit. |  |   
  
## Pgp Decrypt Operation

`<crypto:pgp-decrypt>`

Decrypt a stream using PGP, giving the original data as a result. The
decryption is done with the private key, so the secret passphrase must be
provided.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | You can decrypt all, or part of a message by using a DataWeave expression.  
For example, you can set Content to `#[payload.name]` to decrypt only an encrypted variable called `name` from the payload | `#[payload]` |   
File Name |  String | the internal file name to decrypt, if not present the first will be used |  |   
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Output Encoding |  String | The encoding of the payload that this operation outputs. |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
Validate Signature if Found |  Boolean | If a contents signature is found in any of the internal decryption stages, the operation will attempt to validate the decrypted contents. Note that this requires the *Signer's public key* to be present in the operation config's public keyring. Also, if the validation fails, the decryption operation will also. | `false` |   
  
### Output Type

Binary

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:KEY`

  * `CRYPTO:PASSPHRASE`

  * `CRYPTO:DECRYPTION`

## Pgp Encrypt Operation

`<crypto:pgp-encrypt>`

Encrypt a stream using PGP, giving an ASCII-armored stream output as a result.
The encryption is done with the public key of the recipient, so the private
keyring and secret passphrase are not required.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | You can encrypt all, or part of a message by using a DataWeave expression.  
For example, you can set Content to `#[payload.name]` to encrypt only a variable called `name` from the payload | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `IDEA`
  * `TRIPLE_DES`
  * `CAST5`
  * `BLOWFISH`
  * `SAFER`
  * `DES`
  * `AES_128`
  * `AES_192`
  * `AES_256`
  * `TWOFISH`
  * `CAMELLIA_128`
  * `CAMELLIA_192`
  * `CAMELLIA_256`

| the symmetric algorithm to use for encryption | `AES_256` |   
File Name |  String | the internal file name to use in the resulting PGP header | stream |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Key Id |  String | The key ID, as defined in the PGP configuration. |  |   
Pgp Key Info |  One of:

  * Pgp Asymmetric Key Info

| An inline key definition. |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
  
### Output Type

Binary

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:ENCRYPTION`

  * `CRYPTO:KEY`

## PGP Encrypt and Sign Operation

`<crypto:pgp-encrypt-and-sign>`

You can encrypt and sign a stream using PGP, producing an ASCII-armored stream
output as a result. The encryption requires the public key of the recipient,
so the secret passphrase is not required. The secret passphrase is required
for signing because the process uses private key of the signer (usually the
sender).

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | You can encrypt all, or part of a message by using a DataWeave expression.  
For example, you can set Content to `#[payload.name]` to encrypt only a variable called `name` from the payload | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `IDEA`
  * `TRIPLE_DES`
  * `CAST5`
  * `BLOWFISH`
  * `SAFER`
  * `DES`
  * `AES_128`
  * `AES_192`
  * `AES_256`
  * `TWOFISH`
  * `CAMELLIA_128`
  * `CAMELLIA_192`
  * `CAMELLIA_256`

| Symmetric algorithm to use for encryption. | `AES_256` |   
File Name |  String | The internal file name to use in the resulting PGP header. | stream |   
Encryption key selection |  A child element with PGP Key Selection | The identifier of the recipient public key. |  |   
Sign key selection |  A child element with PGP Key Selection | The identifier of the signer’s private key. |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Key Id |  String | The key ID, as defined in the PGP configuration. |  |   
Target Variable |  String | The name of a variable in which to store the operation’s output. |  |   
Target Value |  String | An expression that is evaluated against the operation’s output. The result of that expression is stored in the target variable. | `#[payload]` |   
  
### Output Type

Binary

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:ENCRYPTION`

  * `CRYPTO:KEY`

## PGP Encrypt Binary Operation

`<crypto:pgp-encrypt-binary>`

You can encrypt a stream using PGP, producing a binary output as a result.
Because the encryption process uses the public key of the recipient, the
secret passphrase is not required.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | You can encrypt all, or part of a message by using a DataWeave expression.  
For example, you can set Content to `#[payload.name]` to encrypt only a variable called `name` from the payload | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `IDEA`
  * `TRIPLE_DES`
  * `CAST5`
  * `BLOWFISH`
  * `SAFER`
  * `DES`
  * `AES_128`
  * `AES_192`
  * `AES_256`
  * `TWOFISH`
  * `CAMELLIA_128`
  * `CAMELLIA_192`
  * `CAMELLIA_256`

| the symmetric algorithm to use for encryption | `AES_256` |   
File Name |  String | the internal file name to use in the resulting PGP header | stream |   
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Output Encoding |  String | The encoding of the payload that this operation outputs. |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Key Id |  String | The key ID, as defined in the PGP configuration. |  |   
Pgp Key Info |  One of:

  * Pgp Asymmetric Key Info

| An inline key definition. |  |   
Target Variable |  String | The name of a variable on which the operation's output will be placed |  |   
Target Value |  String | An expression that will be evaluated against the operation's output and the outcome of that expression will be stored in the target variable | `#[payload]` |   
  
### Output Type

Binary

### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:ENCRYPTION`

  * `CRYPTO:KEY`

## Pgp Sign Operation

`<crypto:pgp-sign>`

Create a detached (standalone) PGP signature of the stream. The signing is
done with the private key of the sender, so the secret passphrase must be
provided.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | the content to sign | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `MD5`
  * `RIPEMD160`
  * `TIGER_192`
  * `HAVAL_5_160`
  * `DOUBLE_SHA`
  * `SHA1`
  * `SHA224`
  * `SHA256`
  * `SHA384`
  * `SHA512`

| the digest (or hashing) algorithm | `SHA256` |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Key Id |  String | The key ID, as defined in the PGP configuration. |  |   
Pgp Key Info |  One of:

  * Pgp Asymmetric Key Info

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

## Pgp Sign Binary Operation

`<crypto:pgp-sign-binary>`

Create a detached (standalone) PGP signature of the stream. The signing is
done with the private key of the sender, so the secret passphrase must be
provided.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Content |  Binary | the content to sign | `#[payload]` |   
Algorithm |  Enumeration, one of:

  * `MD5`
  * `RIPEMD160`
  * `TIGER_192`
  * `HAVAL_5_160`
  * `DOUBLE_SHA`
  * `SHA1`
  * `SHA224`
  * `SHA256`
  * `SHA384`
  * `SHA512`

| the digest (or hashing) algorithm | `SHA256` |   
Output Mime Type |  String | The mime type of the payload that this operation outputs. |  |   
Output Encoding |  String | The encoding of the payload that this operation outputs. |  |   
Streaming Strategy | 

  * Repeatable In Memory Stream
  * Repeatable File Store Stream
  * non-repeatable-stream

| Configure if repeatable streams should be used and their behavior |  |   
Key Id |  String | The key ID, as defined in the PGP configuration. |  |   
Pgp Key Info |  One of:

  * Pgp Asymmetric Key Info

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

## Pgp Validate Operation

`<crypto:pgp-validate>`

Validate a PGP signature against a stream, to authenticate it. The validation
is done with the public key of the sender, so the secret passphrase is not
required.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Configuration | String | The name of the configuration to use. |  | **x**  
Value |  Binary | the message to authenticate | `#[payload]` |   
Expected |  Binary | the signature |  | **x**  
  
### Throws

  * `CRYPTO:MISSING_KEY`

  * `CRYPTO:VALIDATION`

## Pgp Binary To Armored Operation

`<crypto:pgp-binary-to-armored>`

Converts an encrypted PGP message or a PGP signature to an ASCII armored
representation, suitable for plain text channels.

### Parameters

Name | Type | Description | Default Value | Required  
---|---|---|---|---  
Content |  Binary | the content to convert | `#[payload]` |   
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

  * `CRYPTO:PARAMETERS`

## Types

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
  
### Pgp Asymmetric Key Info

Field | Type | Description | Default Value | Required  
---|---|---|---|---  
Key Id |  String | Internal key ID for referencing from operations. |  | x  
Key Pair Identifier |  PGP Asymmetric Key Identifier | A way to identify the key inside the keystore. |  | x  
Passphrase |  String | The password for unlocking the secret part of the key. |  |   
  
### PGP Asymmetric Key Identifier

Field | Type | Description | Default Value | Required  
---|---|---|---|---  
Fingerprint |  String | The Fingerprint of the configured key |  |   
Principal |  String | A combination of name and email specified while generating the key. When you use this field, you use the primary key. Do not use this field when you are using keys with different algorithms to sign and encrypt (for example, DSA and Elgamal); specify the proper key by using the `fingerprint` property instead. |  |   
  
### PGP Key Selection

Field | Type | Description | Default Value | Required  
---|---|---|---|---  
Key is |  String | Internal key ID for referencing from operations |  |   
Pgp Key info |  One of:

  * Pgp Asymmetric Key Info

| An inline key definition. |  | 

