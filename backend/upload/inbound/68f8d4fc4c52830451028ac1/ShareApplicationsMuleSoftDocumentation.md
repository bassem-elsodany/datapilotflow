# Share Applications

When working on a team, a Mule runtime engine project increases in size,
increases in its number of developers who need to collaborate, and the need to
run the project in both test and production environments. However, you can
offset this project growth by sharing applications.

Sharing applications is an opportunity for splitting work across teams,
whether these teams work on the same overarching project or on different
projects that they intent for reuse. Because applications are stored in self-
contained archives, they can be shared via a simple file or web server.

To share applications, follow these steps:

  1. Document the name and content of the properties file that each application is expecting to use.  
The administrators who deploy and run the Mule application can encrypt the
properties file as detailed in [Secure Configuration Properties](secure-
configuration-properties). Administrators must keep the decryption key of the
properties file secure.

  2. Generate the file used to share the application in one of the following two ways:

     * Export the application from Anypoint Studio and generate a deployable archive `.jar` file.

     * Package your application into one of the following three types of `.jar` files using the Mule Maven Plugin:

       * Deployable archive `.jar` file to deploy into a running Mule runtime engine.

       * Mule app package `.jar` file to import into Studio.

       * Mule app lightweight package `.jar` file to then import it into Studio.

  3. Share the `.jar` file with other developers, as appropriate.

## See Also

  * [Exporting Projects from Studio](../../studio/latest/import-export-packages#export-project-studio)

  * [Mule Application Packaging](package-a-mule-application)

