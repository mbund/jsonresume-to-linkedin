# JSON Resume to LinkedIn Syncer

Janky solution to syncing a JSON Resume profile to LinkedIn.

> [!CAUTION]
> This might delete things from your LinkedIn profile. You should make a backup first. Use at your own risk.

> [!WARNING]
> This relies on an unofficial LinkedIn API and may break at any time. See [that api's troubleshooting steps](https://github.com/tomquirk/linkedin-api#troubleshooting) for help first to see if it's a problem with the API like the common `CHALLENGE` error, or if the error is with this repository.

## Usage

```
pip3 install git+https://github.com/mbund/jsonresume-to-linkedin.git
LINKEDIN_USERNAME=xxxxx LINKEDIN_PASSWORD=xxxxx jsonresume-to-linkedin
```
