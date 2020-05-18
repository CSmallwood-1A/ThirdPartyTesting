#!/usr/bin/env python3

import argparse
import zipfile
import json
import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth

# service account authorised to make calls to issues.citrite.net
username = 'svcacct_third-part'
host = 'issues.citrite.net'


def create_parser():
    parser = argparse.ArgumentParser(description='Format the export to include extra metadata from third parties')
    parser.add_argument('--issueId', type=str, required=True, help='id of the issue that triggered the build')
    parser.add_argument('--jiraPassword', type=str, required=True, help='password for the service account making call to Jira')
    return parser


def get_attachments(jiraPassword, issueId):
    auth = HTTPBasicAuth(username, jiraPassword)
    headers = {'Content-Type': 'application/json'}
    params = {'fields': 'attachment'}
    try:
        response = requests.get(
            url='https://{}/rest/api/2/issue/{}'.format(host, issueId),
            headers=headers,
            auth=auth,
            params=params
        )
        jsonData = response.json()
        print('{}\n'.format(json.dumps(jsonData)))
        for attachment in jsonData['fields']['attachment']:
            filename = attachment['filename']
            url = attachment['content']
            print('fetching {} from url: {}\n'.format(filename, url))
            response = requests.get(
                url=url,
                auth=auth
            )
            open(filename, 'wb').write(response.content)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return


def format_submission(exportFile, vendor, privacyUrl, termsOfUseUrl, helpUrl):
    formattedFile = exportFile.replace('.', '-formatted.')
    with zipfile.ZipFile(exportFile, 'r') as zin:
        with zipfile.ZipFile(formattedFile, 'w') as zout:
            for item in zin.infolist():
                textcontents = zin.read(item.filename)
                if item.filename == 'metadata.json':
                    jsoncontents = json.loads(textcontents)
                    jsoncontents['vendor'] = vendor
                    jsoncontents.pop('tags')
                    jsoncontents.update({'metadata': []})
                    jsoncontents['metadata'].append({'tag': 'privacyUrl', 'value': privacyUrl})
                    jsoncontents['metadata'].append({'tag': 'termsOfUseUrl', 'value': termsOfUseUrl})
                    jsoncontents['metadata'].append({'tag': 'helpUrl', 'value': helpUrl})
                    jsoncontents['metadata'].append({'tag': 'helpUrl', 'value': helpUrl})
                    textcontents = json.dumps(jsoncontents, indent=4)
                    zout.writestr(item.filename, textcontents)
                else:
                    zout.writestr(item, textcontents)


def main():
    # get issueId and service account password from command line
    parser = create_parser()
    args = parser.parse_args()

    # get the relevant fields and attached files from the Jira issue
    get_attachments(args.jiraPassword, args.issueId)

    # reformat the submitted integration file using metadata from the issue
    # format_submission(
    #     issueFields['exportFile'],
    #     issueFields['vendor'],
    #     issueFields['privacyUrl'],
    #     issueFields['termsOfUseUrl'],
    #     helpUrl['helpUrl']
    # )


main()
