# tap-mws

## Connecting tap-mws

### Requirements

To set up tap-mws in Stitch, you need:

-  **Amazon MWS Keys** You will need to register as a devloper either through your own seller account or as a standard devloper see [here](https://docs.developer.amazonservices.com/en_US/dev_guide/DG_Registering.html)
-  **An Amazon Seller Account** You will need an amazon account to pull orders from.

### Setup
Example Config file:
```javascript
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

## tap-mws Table Schemas

**orders**
- Table name: orders
- Description: order level data for amazon orders
- Primary key column(s): AmazonOrderId
- Replicated incrementally time
- Bookmark column(s): CreatedAfter
- Link to API endpoint documentation: http://docs.developer.amazonservices.com/en_US/orders-2013-09-01/Orders_ListOrders.html

**order items**
- Table name: order_items
- Description: Line level data for orders
- Primary key column(s): AmazonOrderId
- Replicated fully
- Link to API endpoint documentation: http://docs.developer.amazonservices.com/en_US/orders-2013-09-01/Orders_ListOrderItems.html
