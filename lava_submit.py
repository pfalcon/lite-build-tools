import os
import sys


# Actually submit job to LAVA
SUBMIT = 1


def submit_testjob(jobdef):
    import xmlrpc.client
    import requests
    from urllib.parse import urlsplit

    via_squad = os.getenv("USE_QA_SERVER") == "1"

    if via_squad:
        lava_uri = os.getenv("LAVA_SERVER")
        if "://" not in lava_uri:
            lava_uri = "https://" + lava_uri

        qa_server_uri = os.getenv("QA_SERVER")
        qa_server_group = os.getenv("QA_SERVER_GROUP")
        qa_server_project = os.getenv("QA_SERVER_PROJECT")
        qa_server_build = os.getenv("EXTERNAL_BUILD_ID")
        if qa_server_build is None:
            print(
                "Warning: EXTERNAL_BUILD_ID environment variable is not set, "
                "using GIT_COMMIT_ID instead."
            )
            qa_server_build = os.getenv("GIT_COMMIT_ID")
        qa_server_env = os.getenv("PLATFORM")
        qa_server_api = "%s/api/submitjob/%s/%s/%s/%s" % (
            qa_server_uri,
            qa_server_group,
            qa_server_project,
            qa_server_build,
            qa_server_env)
        headers = {
            "Auth-Token": os.getenv("QA_REPORTS_TOKEN")
        }
        data = {
            "definition": jobdef,
            "backend": urlsplit(lava_uri).netloc  # qa-reports backends are named as lava instances
        }
        print("POST:", qa_server_api, data)
        results = requests.post(qa_server_api, data=data, headers=headers)
        if results.status_code < 300:
            print("%s/testjob/%s" % (qa_server_uri, results.text))
        else:
            print("status code: %s" % results.status_code)
            print(results.text)

    else:
        username = os.getenv("LAVA_USER")
        token = os.getenv("LAVA_TOKEN")
        uri = os.getenv("LAVA_SERVER")
        if not uri.endswith("/"):
            uri += "/"
        server = xmlrpc.client.ServerProxy("https://%s:%s@%s" % (username, token, uri))

        job_id = server.scheduler.submit_job(jobdef)
        if isinstance(job_id, list):
            job_id = job_id[0]
        print("LAVA: https://%s../scheduler/job/%s" % (uri, job_id))


with open(sys.argv[1]) as f:
    jobdef = f.read()

if SUBMIT:
    submit_testjob(jobdef)
