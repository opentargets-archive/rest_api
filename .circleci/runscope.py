#!/usr/bin/env python

import requests
import sys
import time
import os


def host_url():
    if 'CIRCLE_TAG' in os.environ:
        return '{}-dot-{}.appspot.com'.format(os.environ['CIRCLE_TAG'],os.environ['GOOGLE_PROJECT_ID'])
    elif 'CIRCLE_BRANCH':
        return '{}-dot-{}.appspot.com'.format(os.environ['CIRCLE_BRANCH'],os.environ['GOOGLE_PROJECT_ID'])
    else:
        print "CIRCLE_BRANCH or CIRCLE_TAGGED not defined - which service should we test?"
        raise SystemExit

def base_path():
    return '/v{}/platform'.format(os.environ['API_VERSION'])

def ping():
    return requests.get('https://' + 
                            host_url() + 
                            base_path() + 
                            '/public/utils/ping')

TRIGGER_URL = "https://api.runscope.com/radar/bucket/{}/trigger".format(os.environ['RUNSCOPE_BUCKET_ID'])


PAYLOAD = {
    'runscope_environment': os.environ['RUNSCOPE_ENV_UUID_EU_DEV'],
    'host': host_url(),
    'basePath': base_path()
    }


def main():

    print 'Attempting to connect to API deployed at {}{}'.format(host_url(),base_path())

    attempts=1
    while ping().status_code != 200:
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(1)
        attempts+=1
        if attempts > 10: raise SystemExit('no API available')


    print 'Triggering runscope tests'    
    trigger_resp = requests.get(TRIGGER_URL,params=PAYLOAD)

    if trigger_resp.ok:
        trigger_json = trigger_resp.json().get("data", {})

        test_runs = trigger_json.get("runs", [])

        print "Started {} test runs.".format(len(test_runs))

        results = {}
        while len(results.keys()) < len(test_runs):
            time.sleep(5)

            for run in test_runs:
                test_run_id = run.get("test_run_id")
                if not test_run_id in results:
                    result = _get_result(run)
                    if result.get("result") in ["pass", "fail"]:
                        results[test_run_id] = result

        pass_count = sum([r.get("result") == "pass" for r in results.values()])
        fail_count = sum([r.get("result") == "fail" for r in results.values()])

        if fail_count > 0:
            print "{} test runs passed. {} test runs failed.".format(pass_count, fail_count)
            sys.exit(1)

        print "All test runs passed."


def _get_result(test_run):
    # generate Personal Access Token at https://www.runscope.com/applications
    if not "RUNSCOPE_ACCESS_TOKEN" in os.environ:
        print "Please set the environment variable RUNSCOPE_ACCESS_TOKEN. You can get an access token by going to https://www.runscope.com/applications"
        sys.exit(1)

    API_TOKEN = os.environ["RUNSCOPE_ACCESS_TOKEN"]
    
    opts = {
        "base_url": "https://api.runscope.com",
        "bucket_key": test_run.get("bucket_key"),
        "test_id": test_run.get("test_id"),
        "test_run_id": test_run.get("test_run_id")
    }
    result_url = "{base_url}/buckets/{bucket_key}/tests/{test_id}/results/{test_run_id}".format(**opts)
    print "Getting result: {}".format(result_url)

    headers = {
        "Authorization": "Bearer {}".format(API_TOKEN),
        "User-Agent": "python-trigger-sample"
    }
    result_resp = requests.get(result_url, headers=headers)

    if result_resp.ok:
        return result_resp.json().get("data")

    return None


if __name__ == '__main__':
    main()