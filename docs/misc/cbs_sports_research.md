# CBS Sports Fantasy Hockey API Research

## Authentication
- **Login URL**: [Fill in the login URL you used]
- **Required Headers**: [List any headers you see in requests]
- **Session Cookies**: [List any important cookies]
- **Authentication Method**: [Cookies, Bearer token, etc.]

## API Endpoints Discovered

### 1. Waiver Status
- **Endpoint**: `/league/transactions/waiver-status`
- **Method**: GET
- **Full URL**: [Fill in the base URL + endpoint]
- **Response Structure**:
```json
{
    "uriAlias": "/league/transactions/waiver-status",
    "statusCode": 200,
    "body": {
        "waiver_status": {
            "need_to_start_waivers": 0,
            "season_start_date": "20241004"
        }
    },
    "uri": "/league/transactions/waiver-status",
    "statusMessage": "OK"
}
```

### 2. [Next Endpoint - Fill in as you discover]
- **Endpoint**: [URL path]
- **Method**: [GET/POST]
- **Full URL**: [Complete URL]
- **Response Structure**: [Paste JSON response]

### 3. [Continue for each endpoint...]

## Key Data Structures

### League Information
- **League ID**: [How is the league identified?]
- **Season**: [Format: YYYYMMDD like "20241004"]
- **Team Count**: [Number of teams in league]

### Player Information
- **Player ID Format**: [How are players identified?]
- **Player Name Format**: [How are names stored?]
- **Position Codes**: [What position codes are used?]

### Team Information
- **Team ID Format**: [How are teams identified?]
- **Team Name Format**: [How are team names stored?]
- **Owner Information**: [How is owner data structured?]

## Request Headers Observed
```
[Paste any important headers you see in the Network tab]
```

## Rate Limiting
- **Rate Limit Observed**: [Any 429 errors or rate limiting?]
- **Request Frequency**: [How often can you make requests?]

## Notes
- [Any other important observations]
- [Error messages encountered]
- [Authentication flow details]

## Next Steps
- [ ] Find team roster endpoints
- [ ] Find player stats endpoints
- [ ] Find league standings endpoints
- [ ] Test endpoints without authentication
- [ ] Document all response formats 