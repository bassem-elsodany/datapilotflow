// Initialize DataPilotFlow database
db = db.getSiblingDB('datapilotflow');

// Note: Collections and indexes are managed by the application
// This script only ensures the database exists
// The app will create collections and indexes as needed during startup

print('DataPilotFlow database created successfully!');
print('Collections and indexes will be managed by the application.');
