# tap-mws

## Connecting tap-mws

### Requirements

To set up tap-mws in Stitch, you need:

-  **Amazon MWS Keys** You will need to register as a devloper either through your own seller account or as a standard devloper see ([here](https://docs.developer.amazonservices.com/en_US/dev_guide/DG_Registering.html))
-  **An Amazon Seller Account** You will need an amazon account to pull orders from.

### Setup
Example Config file:
```json
{
  "seller_id": "", // Seller id for the account you would like to pull
  "aws_access_key" : "", // Dev key provided by amazon
  "client_secret" : "", // Dev key provided by amazon
  "marketplace_id": "", // Marketplace id for the marketplace you would like to pull (amazon us vs amazon canada...)
  "start_date" : "2015-01-01T00:00:00Z", // Start date for replication
  "user_agent" : ""
}

```
---

## [tap_name] Replication

If pertinent, include details about how the tap replicates data and/or uses the API. As Stitch users are billed for total rows replicated, any info that can shed light on the number of rows replicated or reduce usage is considered necessary.

Examples:

- Replication strategy - attribution/conversion windows ([Google AdWords](https://www.stitchdata.com/docs/integrations/saas/google-adwords#data-extraction-conversion-window)), event-based updates, etc.
- API usage, especially for services that enforce rate limits or quotas, like Salesforce or [Marketo](https://www.stitchdata.com/docs/integrations/saas/marketo#marketo-daily-api-call-limits)

---

## [tap_name] Table Schemas

For **each** table that the tap produces, provide the following:

- Table name: 
- Description:
- Primary key column(s): 
- Replicated fully or incrementally _(uses a bookmark to maintain state)_:
- Bookmark column(s): _(if replicated incrementally)_ 
- Link to API endpoint documentation:

---

## Troubleshooting / Other Important Info

Anything else users should know about using this tap? For example: `some_column` is a Unix timestamp.
