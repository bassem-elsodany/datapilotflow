# Managing Business Groups

Use business groups to delegate administrative responsibilities, control
access to resources, and structure your organization’s access management.

In the Access Management **Business Groups** page, you can:

  * Create business groups.

  * View a hierarchical tree of all of the business groups you have permissions to view.

  * View and edit properties of a business group.

Permissions determine What you can view and edit.

  * Add and delete business groups (if enabled at the root business group level).

  * View the Client ID and Client Secret for environments.

## Access a Business Group

  1. Sign in to Anypoint Platform using an account that has the root Organization Administrator permission.

  2. In the navigation bar or the main Anypoint Platform page, click **Access Management**.

  3. In the Access Management navigation menu, click **Business Groups**.

  4. Click the name of the root business group.

## Create a Business Group

When you create a new business group under the top-level (root) business
group, all the current users with the Organization Administrator permission in
the root business group appear in the list of users in the newly created
business group.

  1. Sign in to Anypoint Platform using an account that has the root Organization Administrator permission.

  2. In the navigation bar or the main Anypoint Platform page, click **Access Management**.

  3. In the Access Management navigation menu, select **Business Groups**.

  4. Click the name of the business group.

The **Settings** section appears, showing details about the root organization
or business group.

  5. To create the root business group for your organization, click **Create business group**.

  6. To create a child business group, click the **…​** menu for the parent business group.

  7. Click **Create child group**.

  8. In the dialog box, enter:

     * **Business Group name** : Name for the new business group.

     * **Owner** : Assign an existing Organization Administrator as the business group owner.

     * Select **Can create Business Groups** to allow the owner to create child business groups under this business group.

     * Select **Can create environments** to allow the owner to create environments within this business group.

     * You can assign some or all of the redistributable resources (vCores, VPCs, and so on) that your organization owns to an individual business group. This ensures that the resources are used by the CloudHub deployments that belong to the business group. You can assign the resources when you create the business group, or edit these settings later.

     * **Enable CloudHub global deployment**  
This option is available only if global deployment is enabled on the parent
business group. When global deployment is enabled, the region is auto-
populated according to the region you specified.

     * **Static IPs**

This option is available only if the parent business group has static IPs
assigned to it. This option enables the use of static IP addresses.

  9. Click **Add Business Group**.  
The business group appears in the hierarchy, under the root organization.

__ |  Allocating redistributable resources to a business group makes those resources available only to that business group, which makes them unavailable to the parent organization.  
---|---  
  
## Create a Child Business Group

Create a business group hierarchy to help you better control user access to
resources.

  1. To create a child business group, click the **…​** menu for the parent business group.

  2. In the **Add Business Group** dialog, enter a **Business Group name** and **Owner** , then select from these options:  

     * **Owner can create Business Groups**

Users with the Organization Administrator permission can create child business
groups in a business group that they own.

     * **Owner can create environments**

Users with the Organization Administrator permission can create environments
within their business groups.

     * **Enable CloudHub global deployment**

This option is available only if global deployment is enabled on the parent
business group. When global deployment is enabled, the region is auto-
populated according to the region you specified.

     * **Static IPs** :

This option is available only if the parent business group has static IPs
assigned to it. This option enables the use of static IP addresses.

  3. Click **Add Business Group**.  
The new business group appears in the parent business group hierarchy.

## Navigate Between Business Groups

When your organization has multiple business groups, you can switch between
them in the list of business groups. Switching between business groups changes
the list of available CloudHub deployments, APIs, users, and roles settings.

![A business group and a list of its sub-groups](_images/switch-suborg.png)

__ |  When you create a business group, sign out and sign in to Anypoint Platform to see newly-created business groups in the business group navigation menu. When you sign in to Anypoint Platform, you return to the business group where you were last active when you signed out of Anypoint Platform.  
---|---  
  
If you don’t have the Organization Administrator permission, you can view only
the business groups that you have permissions to view. In the **Organization**
tab, your organization tree displays only the business groups to which you
belong.

### View User and Team Access

You can view a list of users or teams that have access to a business group or
environment and filter by their assigned permissions.

  1. In the Access Management navigation menu, select **Business Groups**.

  2. Click the name of the business group.

The **Settings** section appears, showing details about the root organization
or business group.

  3. Select the **Access Overview** tab.

     1. Select the business group or environment from the dropdown to view a list of users with access to the selected business group or environment.

     2. Select a permission from the dropdown to see a list of users with the selected permission in the selected business group or environment.

  4. To see teams with access to the selected business group or environment, select **Teams** from the dropdown.

  5. To see teams that have specific permissions assigned, select the permission from the dropdown.

Permissions that are granted directly to users outside of the Teams feature
aren’t shown.

### View Roles Associated with the Business Group

  1. In the Access Management navigation menu, select **Business Groups**.

  2. Click the name of the business group.

The **Settings** section appears, showing details about the root organization
or business group.

  3. Select the **Roles** tab.

## Delete a Business Group

Only an organization administrator that belongs to a business group can delete
it. The top-level (root) business group can’t be deleted, even by an
organization administrator.

  1. In the Access Management navigation menu, click **Business Groups**.

  2. Click the name of your root organization.

  3. Click the **…​** menu for the business group to delete.

  4. In the confirmation dialog, enter the name of the business group and then click **Delete**.

## Redistribute Resources Between Existing Business Groups

You can redistribute resources (like vCores, VPCs, load balancers, small or
large Managed Flex Gateways) between business groups at the business group
level only, not at the root organization level.

You must have the Organization Administrator permission for the root
organization to redistribute resources.

__ |  Allocating redistributable resources to a business group makes those resources available only to that business group, which makes them unavailable to the parent organization.  
---|---  
  
The business group hierarchy prevents a child business group from consuming
additional resources from its parent group unless an organization
administrator redistributes those resources to the child group. Resource
distribution proceeds from root to parent to child. For example, you can’t
redistribute sandbox VCores to a child business group if the parent business
group doesn’t have any sandbox vCores available, even if the root organization
has sandbox vCores available.

Additionally, the root organization or parent business group can’t reclaim
resources allocated to a business group that isn’t a direct child.

  1. In the Access Management navigation menu, click **Business Groups**.

  2. Click the name of the business group to reassign resources to.

The **Settings** section appears, showing details about the root organization
or business group.

  3. Click the **Settings** tab.

  4. Enter the number of vCores you want the business group to have.

  5. Click **Save changes**.

The **Business Group Info** window includes a resource counter that shows a
value representing available resources, the sum of those resources that are
reassigned to child business groups, and resources currently in use by the
selected business group.

### View Resource Usage

To see resource utilization for the root organization, navigate to **Access
Management > Subscription > Runtime Manage Subscription**.

## Client ID and Client Secret

Each root business group, child business group, and environment, has its own
associated unique client ID and client secret. These are used for
authentication by users who aren’t business group administrators to access
assets within a business group. The client ID and password are generated by
Anypoint Platform for each environment you create, and they are globally
unique.

To deploy proxies or APIs to CloudHub, you must use these values to configure
a customer-hosted Mule Runtime or legacy API Gateway.

__ |  Business group-level client IDs and client secrets are supported only for backward compatibility. In newer Anypoint Platform accounts, use the client ID and client secret for an environment instead. See [Environments](environments).   
---|---  
  
### View the Client ID and Secret for Environments

  1. Sign in to Anypoint Platform using an account that has the root Organization Administrator permission.

  2. In the navigation bar or the main Anypoint Platform page, click **Access Management**.

  3. In the Access Management navigation menu, click **Business Groups**.

  4. Click the name of your root organization.

  5. Click the **Environments** tab.

  6. Click the name of the environment.

  7. Next to the client secret, click **Show**.

### View the Client ID and Secret for Business Groups

  1. Sign in to Anypoint Platform using an account that has the root Organization Administrator permission.

  2. In the navigation bar or the main Anypoint Platform page, click **Access Management**.

  3. In the Access Management navigation menu, click **Business Groups**.

  4. Click the name of your root organization.

  5. Click the **Settings** tab.

  6. Next to the client secret, click **Show**.

__ | 

  * For newer Anypoint Platform accounts, the client ID and secret apply to environments rather than business groups. See [Environments](environments).
  * To change the client secret for an environment or business group, see [How to Set Environment client_secret in Anypoint Platform](https://help.salesforce.com/s/articleView?id=001115221&type=1), or contact your customer support representative.

  
---|---  
  
## Manage Root Business Group Settings

Only users with the Organization Administrator permission can manage these
settings.

An organization administrator can modify the business group owner, name,
domain name, and session timeout for its users.

To access these settings:

  1. Sign in to Anypoint Platform using an account that has the root Organization Administrator permission.

  2. In the navigation bar or the main Anypoint Platform page, click **Access Management**.

  3. In the Access Management navigation menu, click **Business Groups**.

  4. Click the name of your root organization.

  5. Click the **Settings** tab.

  6. Modify any of the following settings, then click **Save changes**.

     * **Name**

This can be anything, for example, the name of the company.

     * **Owner**

The owner of the business group.

__ |  Business groups are hierarchical. The owner of a parent business group automatically has and retains administrator permissions for any child business group of that parent, even if they make another Organization Administrator user owner of a child business group.   
---|---  
  
     * **Organization domain**

Although multiple business groups can be created by different users using the
same business group name, each business group must have a unique domain name.

__ |  Changing the name or domain name of a business group changes the deep links to any existing API Portals in your business group.   
---|---  
  
     * **Default session timeout**

Set the amount of time (in minutes) a user is inactive before they are
automatically signed out of Anypoint Platform. The default is 60 minutes, the
minimum is 15 minutes, and the maximum is 180 minutes.

     * **Confidentiality Notification**

Create a custom popup that appears when users sign in to your business group.
The character limit is 1000 alphanumeric characters and symbols: `@`, `:`,
`?`, `!`, `,`, `.`, `;`, `'`, `_`, and `-`. You can also add line breaks using
`\n` and tabs using `\t`. If you leave this field blank, users don’t receive a
notification at signin.

     * **Runtime Manager**

The default region for Runtime Manager.

You can also view the business group ID, client ID, and client secret. These
values apply to the root business group and grant permissions for all of the
business groups contained within.

To modify your [multi-factor authentication settings](multi-factor-
authentication) for your business group, click the **Identity Providers** in
the Access Management navigation menu. Business groups created after April 30,
2022 require multi-factor authentication by default for all users.

## View Limits for a Business Group

Each business group has a **Limits** section that shows how close it is to
reaching the limits that are imposed by Anypoint Platform.

To view limits:

  1. In the Access Management navigation menu, select **Business Groups**.

  2. Click the name of the business group.

The **Settings** section appears, showing details about the root organization
or business group.

  3. Click the business group for which you want to view limits.

  4. Click the **Limits** tab.

For more information on limits in access management, see
[Limits](troubleshooting-anypoint-platform-access#access-management-limits).

## Find your Business Group ID

Some operations require you to specify your business group (organization) ID,
or _orgId_. You also need your business group ID to designate a business group
or root business group when creating certain types of requests.

You can get your business group ID from your business group URL, executing an
Anypoint CLI command, or using a token to invoke the Anypoint Platform REST
API.

### View Your Business Group URL

After signing in to Anypoint Platform, you can view your business group ID by
accessing [business
groups](https://anypoint.mulesoft.com/accounts/businessGroups).

  1. Log in to Anypoint Platform.

  2. In the navigation bar or the main Anypoint Platform page, click **Access Management**.

  3. If you are using the new feature UI (Teams feature is enabled):

     1. In the Access Management navigation menu, click **Business Groups**.

     2. In the tree that contains the root business group, click the root business group name.

The URL in your browser’s address bar now appears in the following format:
`[https://anypoint.mulesoft.com/accounts/businessGroups/<XXXXXXX-XXXX-XXXX-
XXXX-XXXXXXX>](https://anypoint.mulesoft.com/accounts/businessGroups/<XXXXXXX-
XXXX-XXXX-XXXX-XXXXXXX>);`.

The business group ID is `XXXXXXX-XXXX-XXXX-XXXX-XXXXXXX` in the example, and
it appears after `businessGroups/` in your URL.

  4. If you are using the classic UI (Teams feature is not enabled):

     1. In the Access Management navigation menu, click **Business Groups**.  
A tree containing the root business group and child business groups appears.

     2. Click the business group.

The business group ID appears in the **Business Group Id** field.

## Use Anypoint CLI to Get Business Group Details

If you have the [Anypoint CLI (command-line interface) tool](../anypoint-
cli/latest/account) installed, you can use it to get a list of the business
groups, their types, and the business group ID.

For example, when you execute the `account:business-group:list [flags]`
command, your business group information appears in the following format:

Name | Type | ID  
---|---|---  
Great Company | Root | 12345678-7831-8734-9999-a0a0a0a0a0a0  
Retail | Business unit | abcdef01-1234-53e1-a3b4-b0b0b0b0b0b0  
Engineering | Business unit | 87654321-abcd-e8e2-bab4-c0c0c0c0c0c0  
  
In the example, the ID next to `Root` is the business group ID.

## Anypoint Platform REST API

To get a token to invoke the Anypoint Platform REST API, see [How to generate
your Authorization Bearer token for Anypoint
Platform](https://help.mulesoft.com/s/article/How-to-generate-your-
Authorization-Bearer-token-for-Anypoint-Platform). Then, invoke the URL
`<https://anypoint.mulesoft.com/accounts/api/me>` using the token.

For example:

`$ curl -H "Authorization: Bearer [YOUR_ACCESS_TOKEN]"
<https://anypoint.mulesoft.com/accounts/api/me>`

## Share Business Group Resources

All API versions and CloudHub environments that you create in a business group
are accessible only to users within the business group.

If you want to share resources with a user, you have to invite the user to
join your business group, and the user must accept the invitation and join the
business group you sent the invitation from. See [Inviting
Users](users#inviting-users) for more information.

__ |  Because the business group name (often the company name) isn’t necessarily unique, it isn’t sufficient for the invited user to join the business group and use the company name associated with the root business group. The organization domain name you set in the business group information is what distinguishes your business group from other business groups. Invited users must use the link they receive in the invitation email to join your business group.  
---|---  
  
If your business group is configured to use an external federated identity
system, you don’t need to invite users, as they are authenticated by the
external identity provider.

After a user joins your business group, they have access to the resources
associated with the permissions or roles assigned to them. You can assign
permissions to grant users access to different resources within the business
group. A best practice is to assign permissions to the user at the time you
invite them to join your business group so the roles are in effect when the
user signs in for the first time.

If your business group contains business groups, you can give users access to
multiple business groups by granting them permissions within each group.

## Connect MuleSoft Composer to Anypoint Platform

Business groups that use both MuleSoft Composer and Anypoint Platform can
connect the two products.

To link Composer to Anypoint Platform:

  1. Sign in to Anypoint Platform using an account that has the root Organization Administrator permission.

  2. In the navigation bar or the main Anypoint Platform page, click **Access Management**.

  3. In the Access Management navigation menu, click **Composer Sync**.

  4. In the **Composer Sync Orgs** page, click **Add Composer Orgs**.

  5. In the **Add organization** window, in the **Organization ID** box, enter your Composer organization and then click **Add**.

__ |  You can locate your Composer Organization ID by navigating to **Composer** > **Settings** > **Account** > **General Information**.   
---|---  
  
An email is generated and sent to the Composer organization admin that
provides a link to sync Anypoint Platform to Composer.

## See Also

  * [Resource Organization and Access Control with Business Groups](business-groups)

  * [Using Roles to Manage Permissions](roles)

  * [Using Teams to Manage User Permissions](teams)

  * [Managing Permissions](managing-permissions)

  * [Environments](environments)

