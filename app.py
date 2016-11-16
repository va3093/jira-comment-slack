# -*- coding: utf-8 -*-
import json
import logging
import os
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)


# Mandatory settings
slack_url = os.environ['slack_url']
slack_channel = os.environ['channel']

# Optional settings
slack_post = os.environ.get('slack_post', True)
flask_host = os.environ.get('host', '127.0.0.1')
flask_port = os.environ.get('port', 11000)
flask_logfile = os.environ.get('logfile', None)
flask_logaddress = os.environ.get('syslog_address', '/dev/log')
flask_debug = os.environ.get('debug', False)



@app.route('/webhook', methods=['GET', 'POST'])
def tracking():
    if request.method == 'POST':
        rd = request.get_json()
        if 'comment' in rd:
            comment_body = rd['comment']['body']
            comment_author = rd['comment']['updateAuthor']['displayName']
            comment_id = rd['comment']['id']

            if rd['comment']['created'] == rd['comment']['updated']:
                comment_type = 'created'
                slack_color = '#439FE0'
            else:
                comment_type = 'updated'
                slack_color = '#7CD197'

            task_key = rd['issue']['key']
            task_id = rd['issue']['id']
            task_link = str(rd['issue']['self']).replace('rest/api/2/issue', 'browse').replace(task_id, task_key)
            task_summary = rd['issue']['fields']['summary']

            comment_link = ('%(task_link)s?focusedCommentId=%(comment_id)s&'
                            'page=com.atlassian.jira.plugin.system.issuetabpanels:'
                            'comment-tabpanel#comment-%(comment_id)s') % {
                'task_link': task_link,
                'comment_id': comment_id,
            }

            slack_pretext = comment_author + ' ' + comment_type + ' comment'
            slack_title = task_key + ' : ' + task_summary
            slack_data = {
                'username': 'JIRA Comment',
                'channel': slack_channel,
                'attachments': [
                    {
                        'fallback': slack_pretext + ' - ' + slack_title + ' - ' + comment_link,
                        'pretext': slack_pretext,
                        'title': slack_title,
                        'title_link': comment_link,
                        'text': comment_body,
                        'color': slack_color
                    }
                ]
            }
            if slack_post:
                response = requests.post(
                    slack_url, data=json.dumps(slack_data),
                    headers={'Content-Type': 'application/json'}
                )
                if response.status_code != 200:
                    raise ValueError(
                        'Request to slack returned an error %s, the response is:\n%s'
                        % (response.status_code, response.text)
                    )
            else:
                app.logger.warn('Slack posting was disabled by config')

            app.logger.info(comment_body)

        data = jsonify(rd)
        return data
    else:
        app.logger.info(request)
        return 'It Works!'  # Imitating Apache?


def main():
    app.run(debug=flask_debug, host=flask_host, port=flask_port, passthrough_errors=True)


if __name__ == '__main__':
    main()
