import subprocess
import argparse
import json
import requests
import os
import shlex
import yaml
from datetime import datetime


sem_token = os.getenv('SEM_TOKEN', '')
sem_projid = os.getenv('SEM_PROJID', '')
cr_sem_baseurl = os.getenv('SEM_URL', '')


class Sem:

    def __init__(self):
        self.headers = {'Authorization': 'Token {}'.format(sem_token)}

    def list_workflows(self):
        url = "{}/api/v1alpha/plumber-workflows?project_id={}".format(cr_sem_baseurl, sem_projid)
        r = requests.get(
            url,
            headers=self.headers)
        return r.json()

    def get_pipelines(self):
        r = requests.get(
            "{}/api/v1alpha/pipelines/?project_id={}".format(cr_sem_baseurl, sem_projid),
            headers=self.headers)
        return r.json()

    def run_workflow(self, branch):
         r = requests.post(
             "{}/api/v1alpha/plumber-workflows?project_id={}&reference={}".format(cr_sem_baseurl, sem_projid, branch),
             headers=self.headers)
         return r.json()

    def stop_pipeline_by_projid(self, projid):
        r = requests.post(
            "{}/api/v1alpha/pipelines?project_id={}".format(cr_sem_baseurl, projid),
            headers=self.headers
        )
        return r.json()

    def install_and_connect_sem(self):
        return_code_sem_install =  subprocess.call("bash {}/get_sem_cli.sh".format(os.path.dirname(os.path.abspath(__file__))),
                                                  shell=True)
        assert not return_code_sem_install, return_code_sem_install
        return_code_sem_connect = subprocess.call("sem connect {} {}".format(cr_sem_baseurl, sem_token),
                                                  shell=True)
        assert not return_code_sem_connect, return_code_sem_connect

    def get_project(self, project_name):
        res = subprocess.run(["sem", "get", "project", project_name], stdout=subprocess.PIPE).stdout.decode('utf-8')
        return res

    def get_project_id(self, command):
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, encoding='utf8')
        i=0
        stop = 100
        while True:
            output = process.stdout.readline()
            if output:
                if output.strip() == 'metadata:':
                    stop = i+2
                if i == stop:
                    return output.split(':')[1].strip()
            if output == '':
                break
            i+=1

    def create_sem_secret(self, secrets=None, secret_name=None):
        """
        :param secrets: <dict>
        :param num: <int>
        :return:
        """
        sem_cmd = "sem create secret qa-environments-{}".format(secret_name)
        for each in secrets:
            sem_cmd += ' -e "{}"="{}"'.format(each, secrets[each])
        print("CREATING SEM SECRET - {}".format(sem_cmd))
        return_code_sem_create = subprocess.call(sem_cmd, shell=True)
        if return_code_sem_create:
            return_code_sem_delete = subprocess.call("sem delete secret qa-environments-{}".format(secret_name), shell=True)
            assert not return_code_sem_delete
            return_code_sem_create = subprocess.call(sem_cmd, shell=True)
            assert not return_code_sem_create

    def get_sem_secret(self, num):
        res = subprocess.run(["sem", "get", "secret", "qa-environments-{}".format(num)], stdout=subprocess.PIPE).stdout.decode('utf-8')
        return res

    def delete_sem_secret(self, secret_name):
        return_code_sem_delete = subprocess.call("sem delete secret qa-environments-{}".format(secret_name), shell=True)
        return return_code_sem_delete

    def stop_pipeline(self, branch=None, terminate_pipe_with_age_less_than=2.5):
        terminate_pipeline = False
        result = subprocess.run(['sem', 'get', 'workflow'], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')
        for i, each in enumerate(result):
            if each and i:
                row = each.split('  ')
                if row[3].lstrip() == branch:
                    formatted_created_ts = datetime.strptime(row[2], ' %Y-%m-%d %H:%M:%S')
                    timedelta = datetime.now() - formatted_created_ts
                    minutes_timedelta = timedelta.seconds/60
                    print("Found pipeline started {} minutes ago".format(minutes_timedelta))
                    if minutes_timedelta < terminate_pipe_with_age_less_than:
                        pipelineid = row[1].lstrip()
                        stop_result = subprocess.run(['sem', 'stop', 'pipeline', pipelineid], stdout=subprocess.PIPE).stdout.decode('utf-8')
                        print(stop_result)
                        assert "Pipeline termination started." in stop_result
                        terminate_pipeline = True
                        break
        assert terminate_pipeline
        return terminate_pipeline


def main():
    parser = argparse.ArgumentParser(
        description='SEM'
    )
    parser.add_argument(
        '--secret_name',
        default='',
        required=False,
        help='sem secret name'
    )
    parser.add_argument(
            '--delete',
            default='',
            required=False,
            help='delete sem secret'
        )
    args = parser.parse_args()
    sem = Sem()
    sem.install_and_connect_sem()
    if args.delete:
        print('Deleting sem secret {}'.format(args.secret_name))
        sem.delete_sem_secret(secret_name=args.secret_name)

    # marketing = sem.get_sem_secret("marketing")
    # load_yml = yaml.safe_load(marketing)
    # print(load_yml['data']['env_vars'][0]['value'])

if __name__ == '__main__':
    main()
