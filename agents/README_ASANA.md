# Design Gaga Marketing Automation - Asana App Setup

## App Configuration
1. Go to https://app.asana.com/0/developer-console
2. Click "Create New App"
3. Fill in the following details:
   - App Name: Design Gaga Marketing Automation
   - App URL: http://localhost:8080 (for development)
   - Redirect URL: http://localhost:8080/oauth/callback
   - App Description: Automated marketing and communication system for Design Gaga's home staging services

## Required Scopes
- `projects:read` - To read project information
- `projects:write` - To create and update projects
- `tasks:read` - To read task information
- `tasks:write` - To create and update tasks
- `workspaces:read` - To read workspace information

## Authentication Flow
1. After creating the app, you'll get:
   - Client ID
   - Client Secret
   - OAuth Redirect URL

2. For development, we can use a Service Account:
   - Go to "Service Accounts" tab
   - Create a new service account
   - Copy the access token

3. Update credentials.json with:
   - Client ID
   - Client Secret
   - Service Account Token

## Testing
1. The service account will have access to:
   - Create projects
   - Create and update tasks
   - Track communication history
   - Manage agent relationships

## Security Notes
- Keep credentials.json secure
- Don't commit tokens to version control
- Use environment variables in production
