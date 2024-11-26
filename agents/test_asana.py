from asana import Client as AsanaClient
import json

# Create client with direct PAT
client = AsanaClient.access_token('b22f1074330d136d69e777978f300156')

# Get user info
me = client.users.me()
print("\nUser info:")
print(me)

# List workspaces
print("\nWorkspaces:")
for workspace in client.workspaces.find_all():
    print(workspace)
