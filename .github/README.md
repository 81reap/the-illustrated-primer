## Locally Running Workflows

1. Instal [`act`](https://github.com/nektos/act#installation).
2. Create a Github access token.
	- Go to your GitHub account settings.
	- Navigate to "Developer settings" > "Personal access tokens".
	- Click on "Generate new token".
	- Give your token a name and select the necessary scopes (e.g., repo for full control of private repositories).
	- Click "Generate token" and copy the generated token.
3. Save this token to a file.
```bash
$ cat ~/.secrets                                        
GITHUB_TOKEN=ghp_Q1y...
```
4. Run `act` commands with this token. 
```bash
$ act pull_request --job validate_title --secret-file ~/.secrets --container-architecture linux/amd64 --eventpath <(echo '{"pull_request":{"number":<NUMBER>}}')
```