/**
 * Postman Collection Setup Script
 * 
 * This script can be used in Postman's "Tests" tab to automatically
 * extract and store the access token from login responses.
 * 
 * Add this to the "Tests" tab of the Login request:
 */

// Extract access token from login response
if (pm.response.code === 200) {
    const responseJson = pm.response.json();
    
    if (responseJson.access_token) {
        // Store the access token in environment variable
        pm.environment.set("access_token", responseJson.access_token);
        console.log("✅ Access token stored successfully");
        
        // Store refresh token if available
        if (responseJson.refresh_token) {
            pm.environment.set("refresh_token", responseJson.refresh_token);
            console.log("✅ Refresh token stored successfully");
        }
        
        // Also store user info if available
        if (responseJson.user) {
            pm.environment.set("user_id", responseJson.user.id);
            pm.environment.set("username", responseJson.user.username);
            console.log("✅ User info stored successfully");
        }
    } else {
        console.log("❌ No access token found in response");
    }
} else {
    console.log("❌ Login failed with status:", pm.response.code);
}

/**
 * Additional helper functions for other requests:
 */

// Extract configuration ID from create response
function extractConfigId() {
    if (pm.response.code === 201) {
        const responseJson = pm.response.json();
        if (responseJson.id) {
            pm.environment.set("config_id", responseJson.id);
            console.log("✅ Configuration ID stored:", responseJson.id);
        }
    }
}

// Extract job ID from create response
function extractJobId() {
    if (pm.response.code === 201) {
        const responseJson = pm.response.json();
        if (responseJson.id) {
            pm.environment.set("job_id", responseJson.id);
            console.log("✅ Job ID stored:", responseJson.id);
        }
    }
}

// Extract conversation ID from create response
function extractConversationId() {
    if (pm.response.code === 201) {
        const responseJson = pm.response.json();
        if (responseJson.id) {
            pm.environment.set("conversation_id", responseJson.id);
            console.log("✅ Conversation ID stored:", responseJson.id);
        }
    }
}

// Extract role ID from create response
function extractRoleId() {
    if (pm.response.code === 201) {
        const responseJson = pm.response.json();
        if (responseJson.id) {
            pm.environment.set("role_id", responseJson.id);
            console.log("✅ Role ID stored:", responseJson.id);
        }
    }
}

// Extract notification ID from create response
function extractNotificationId() {
    if (pm.response.code === 201) {
        const responseJson = pm.response.json();
        if (responseJson.id) {
            pm.environment.set("notification_id", responseJson.id);
            console.log("✅ Notification ID stored:", responseJson.id);
        }
    }
}

// Extract file ID from upload response
function extractFileId() {
    if (pm.response.code === 201) {
        const responseJson = pm.response.json();
        if (responseJson.file_id) {
            pm.environment.set("file_id", responseJson.file_id);
            console.log("✅ File ID stored:", responseJson.file_id);
        }
    }
}

// Test response status
function testResponseStatus(expectedStatus = 200) {
    pm.test(`Response status is ${expectedStatus}`, function () {
        pm.response.to.have.status(expectedStatus);
    });
}

// Test response has required fields
function testRequiredFields(fields) {
    fields.forEach(field => {
        pm.test(`Response has ${field}`, function () {
            const responseJson = pm.response.json();
            pm.expect(responseJson).to.have.property(field);
        });
    });
}

/**
 * Usage Examples:
 * 
 * For Login request Tests tab:
 * - Just use the main script above
 * 
 * For Create Configuration request Tests tab:
 * testResponseStatus(201);
 * testRequiredFields(['id', 'name', 'user_id']);
 * extractConfigId();
 * 
 * For Create Job request Tests tab:
 * testResponseStatus(201);
 * testRequiredFields(['id', 'name', 'status']);
 * extractJobId();
 * 
 * For Create Conversation request Tests tab:
 * testResponseStatus(201);
 * testRequiredFields(['id', 'name', 'candidate_id']);
 * extractConversationId();
 * 
 * For Create Role request Tests tab:
 * testResponseStatus(201);
 * testRequiredFields(['id', 'name', 'permissions']);
 * extractRoleId();
 * 
 * For Create Notification request Tests tab:
 * testResponseStatus(201);
 * testRequiredFields(['id', 'title', 'message']);
 * extractNotificationId();
 * 
 * For File Upload request Tests tab:
 * testResponseStatus(201);
 * testRequiredFields(['file_id', 'status']);
 * extractFileId();
 * 
 * For other requests Tests tab:
 * testResponseStatus(200);
 * testRequiredFields(['id', 'name']); // adjust fields as needed
 */
