#!/usr/bin/env python
# encoding: utf-8

import json
import sys
import argparse
import requests
import datetime

from markdown import markdown
from weasyprint import HTML
from thehive4py.api import TheHiveApi

HTML_TEMPLATE = u"""
<!DOCTYPE html>
<html lang="en">

<head>
<meta charset="utf-8">
<link rel="stylesheet" type="text/css" href="./codehilite.css">
</head>

<body>

{}

</body>
</html>
"""

class TheHiveExtendedApi(TheHiveApi):
    def get_case_tasks(self, caseId):
        """
        :param caseId: Case identifier
        :return: request.response object with case tasks list
        """

        req = self.url + "/api/case/task/_search?range=all"
        params = {
            "range": "all",
            "sort": "startDate"
        }
        data = {
            'query': {
                '_parent': {
                    '_type': 'case',
                    '_query': {
                        '_id': caseId
                    }
                }
            }
        }

        try:
            return requests.post(req, json=data, proxies=self.proxies, auth=self.auth)
        except requests.exceptions.RequestException as e:
            sys.exit("Error: {}".format(e))

    def get_task_logs(self, taskId):
        """
        :param taskId: Task identifier
        :return: request.response with task log records list
        """

        req = self.url + "/api/case/task/log/_search"
        params = {
            "range": "all",
            "sort": "startDate"
        }
        data = {
            "query": {
                "_and": [{
                    "_parent": {
                        "_type": "case_task",
                        "_query": {
                            "_id": taskId
                        }
                    }
                }]
            }
        }

        try:
            return requests.post(req, json=data, params=params, proxies=self.proxies, auth=self.auth)
        except requests.exceptions.RequestException as e:
            sys.exit("Error: {}".format(e))


class TheHiveRetriever:
    def __init__(self, host, user, password, proxies=None):
        self.api = TheHiveExtendedApi(host, user, password, proxies=proxies)

    def fetch_case(self, case_id):
        case = self.api.get_case(case_id).json()

        title = case['title']
        description = case['description']
        # created_date = case['createdAt']
        # severity = case['severity']
        # tags = case['tags']

        observables = self.fetch_observables(case_id)
        tasks = self.fetch_tasks(case_id)

        case_markdown = unicode()
        case_markdown += u'{}\n{}\n\n'.format(title, '---')
        case_markdown += u'{}\n\n'.format(description)

        if observables:
            case_markdown += observables

        if tasks:
            case_markdown += tasks

        return case_markdown

    def fetch_observables(self, case_id):
        obs = self.api.get_case_observables(case_id).json()
        if not obs:
            return None

        observables_markdown = u'## Observables\n\nData | Type | Message | Analysis\n---|---|---|---\n'

        for artifact in obs:
            observables_markdown += u'{} | {} | {} | {}'.format(artifact['data'],
                                        artifact['dataType'],
                                        artifact['message'],
                                        artifact['reports'] if artifact['reports'] else 'Not available')
        return observables_markdown + '\n\n'

    def fetch_tasks(self, case_id):
        tasks = self.api.get_case_tasks(case_id).json()
        if not tasks:
            return None

        tasks_markdown = unicode('## Tasks\n\n')

        for task in tasks:
            tasks_markdown += u'### {}\n\n'.format(task['title'])
            tasks_markdown += self.fetch_task_logs(task['id'])

        return tasks_markdown

    def fetch_task_logs(self, task_id):
        logs = self.api.get_task_logs(task_id).json()
        task_log_markdown = u''

        for log in logs:
            date = datetime.datetime.utcfromtimestamp(log['startDate']/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
            task_log_markdown += u'{} ({})\n---\n\n{}\n\n'.format(
                    log['createdBy'],
                    date,
                    log['message']
            )

        return task_log_markdown

    def case_to_pdf(self, case_id, output_filename):
        case_md = self.fetch_case(case_id)
        case_html = HTML_TEMPLATE.format(markdown(case_md, output_format='html5'))

        with open(output_filename, "w+b") as out:
            HTML(string=case_html).write_pdf(out)

        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--url', required=True, type=str, help='TheHive server URL')
    parser.add_argument('-u', '--user', required=True, type=str, help='Username')
    parser.add_argument('-p', '--password', required=True, type=str, help='User password')
    parser.add_argument('-c', '--case', required=True, type=str, help='Case ID, could be retrieved from case URL')
    parser.add_argument('-o', '--output', required=True, type=str, help='PDF output filename')
    args = parser.parse_args()

    the_hive = TheHiveRetriever(args.url, args.user, args.password)
    if the_hive.case_to_pdf(args.case, args.output):
        print("Successfully written report to {}".format(args.output))
