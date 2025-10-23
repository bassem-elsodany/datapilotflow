# Getting Alerts in Anypoint Monitoring

[ ![](../_/img/icons/info.svg) ](/monitoring/#billing)

Alerts indicate whether a resource (such as a Mule app or API) is behaving as
expected or exceeding a defined threshold.

![Alerts in Anypoint Monitoring](_images/intro-alerts.png)

You can create these types of alerts:

  * [Basic alerts](basic-alerts) for servers, Mule apps, and APIs

  * [Custom dashboard alerts](custom-dashboard-alerts) for graphs in custom dashboards in Anypoint Monitoring

  * Other alerts in API Manager or Runtime Manager:

    * Operational alerts for APIs through API Manager

    * Operational alerts for server and app events through Runtime Manager

For alerts in Anypoint Monitoring, you can:

  * Enable or disable alerts configured for graphs in custom dashboards

  * Filter by alert status

  * Filter by alert severity

## Alert Thresholds

For basic and custom dashboard alerts in Anypoint Monitoring, thresholds are
checked every five minutes. The evaluated query is the average value of the
metric in the last five minutes. For custom dashboard alerts, the evaluated
metric is the one referenced in the **General** tab for the graph. If the
value of the metric passes the threshold, the alert triggers. The alert
triggers only if the alert state changes (from `OK` state to `Alerting` state
or vice versa). If you change the email address of the alert recipient, the
recipient doesn’t receive an email until the alert triggers.

## Alert Limits

The number of active alerts allocated to your organization depends on your
organization’s pricing model.

Pricing Package | Active Basic Alerts | Active Advanced Alerts  
---|---|---  
Anypoint Integration Advanced | 10 per app or API instance | 10 per app or API instance  
Gold Subscription | 50 across the organization | None  
Platinum Subscription | 50 across the organization | None  
Titanium Subscription | 50 times the number of vCores in your org, plus 100 | 20 across the organization  
  
### Filter Alerts by Alert State

Filter alerts based on state using the following filters:

All states

    

Lists all alerts

No data

    

No data is available in the series to evaluate the alert threshold.

Disabled

    

The alert is disabled.

Alerting

    

The value of the metric passes the specified threshold.

OK

    

The value of the metric has not passed the threshold.

Pending

    

The alert is enabled and waiting for evaluation.

### Filter Alerts by Alert Severity

When you create basic and custom dashboard alerts, you can select the severity
for those alerts. The severity indicates how important the alert is for the
recipients of the alerts.

Filter alerts based on severity using the following filters:

All severities

    

Lists all severities

Not defined

    

Lists alerts that do not have severities assigned

Info

    

May be assigned to alerts that do not require immediate attention when
triggered. This severity indicates the metric should be passively monitored.

Warning

    

May be assigned to alerts that require prompt attention when triggered. This
severity indicates an alert should be closely monitored.

Critical

    

May be assigned to alerts that require immediate attention when triggered.
This severity indicates an alert should receive an immediate response.

### Enable and Disable Alerts

You can enable or disable an alert by toggling the switch on the right:

  * Enabling a disabled alert causes the alert to transition to `Pending` until it is time for evaluation.

Depending on the value, the alert transitions to `OK` or `Alerting`.

  * Disabling an alert causes the alert to transition to `Disabled`.

## Add API Manager and Runtime Manager Alerts

In addition to creating basic and custom dashboard alerts in Anypoint
Monitoring, you can navigate from Anypoint Monitoring to the alert-creation
pages in API Manager and Runtime Manager.

![Alerts menu options to set up basic, custom dashboard, or other types of
alerts](_images/alerts-menu.png)

__ |  Alerts created in API Manager and Runtime Manager aren’t listed in the Anypoint Monitoring Alerts page.   
---|---  
  
  1. From **Alerts** in Anypoint Monitoring, click **\+ New alert**.

  2. Select **Other** for API Manager or Runtime Manager to access its alert configuration page.

     * **Create an alert for your API in API Manager**

     * **Create an alert for your API in Runtime Manager**

  3. To create these alerts, proceed to:

     * [Runtime Manager Alerts](../runtime-manager/alerts-on-runtime-manager)

     * [API Manager Alerts](../api-manager/latest/using-api-alerts)

## See Also

  * [Basic Alerts](basic-alerts)

  * [Custom Dashboard Alerts](custom-dashboard-alerts)

