from re import template
from werkzeug.exceptions import Unauthorized
from broker.ga4gh.broker.endpoints.repositories import generate_id
from typing import (Dict)
from random import choice
import datetime

from flask import (current_app)
import logging

from pymongo.errors import DuplicateKeyError
from broker.errors.exceptions import (InternalServerError, NotFound, RepositoryNotFound)
from git import Repo, repo
import yaml
from kubernetes import client, config

logger = logging.getLogger(__name__)

template_file='/app/broker/ga4gh/broker/endpoints/template/template.yaml'

def register_builds(repository_id: str, access_token: str,data: Dict):
    retries=3
    db_collection_builds = (
        current_app.config['FOCA'].db.dbs['brokerStore'].
        collections['builds'].client
    )
    db_collection_repositories = (
        current_app.config['FOCA'].db.dbs['brokerStore'].
        collections['repositories'].client
    )
    id_length = (
            current_app.config['FOCA'].endpoints['repository']['id_length']
    )
    id_charset: str = (
            current_app.config['FOCA'].endpoints['repository']['id_charset']
    )
    try:
        id_charset = eval(id_charset)
    except Exception:
        id_charset = ''.join(sorted(set(id_charset)))
    
    dataFromDB = db_collection_repositories.find_one({'id':repository_id})
    if dataFromDB != None:
        if dataFromDB['access_token'] == access_token:
            for i in range(retries + 1):
                logger.debug(f"Trying to insert/update object: try {i}" + str(data))
                data['id'] = repository_id + generate_id(
                    charset=id_charset, 
                    length=id_length, 
                )
                db_collection_repositories.update({"id": repository_id}, {"$push":{"buildList": data['id']}} )
                try:
                    data['finished_at'] = "NULL"
                    data['started_at'] = str(datetime.datetime.now().isoformat())
                    data['status'] = "QUEUED"
                    db_collection_builds.insert_one(data)
                    create_build(repo_url='https://github.com/elixir-cloud-aai/drs-filer.git', branch='dev', commit='122c34d', base_dir='/file', build_id= data['id'], dockerfile_location='/Dockerfile', registry_destination='akash7778/test-image:v0.0.1')
                    break
                except DuplicateKeyError:
                    continue
            return {'id': data['id']}
        else:
            raise Unauthorized
    else:
        raise NotFound



def get_builds(repository_id: str):
    db_collection_repositories = (
        current_app.config['FOCA'].db.dbs['brokerStore'].
        collections['repositories'].client
    )
    data=[]
    dataFromDB = db_collection_repositories.find_one({'id':repository_id})
    if dataFromDB != None:
        for build_id in dataFromDB['buildList']:
            build_data = get_build_info(repository_id, build_id)
            build_data['id'] = build_id
            data.append(build_data)
        logger.info('mData   : '  + str(data))
        #get_build_info()
        return data
    else:
        raise NotFound


def get_build_info(repository_id: str, build_id: str):
    db_collection_builds = (
        current_app.config['FOCA'].db.dbs['brokerStore'].
        collections['builds'].client
    )
    try:
        data= db_collection_builds.find( 
        {'id':build_id}, {'_id': False}
        ).limit(1).next()
        del data['id']
        return data
    except RepositoryNotFound:
        raise NotFound  


def create_build(repo_url, branch, commit, base_dir, build_id, dockerfile_location, registry_destination):
    deployment_file_location = base_dir + '/' + build_id + '/' + build_id + '.yaml'
    clone_path = git_clone_and_checkout(repo_url=repo_url, branch=branch, commit=commit, base_dir=base_dir, build_id=build_id)
    create_deployment_YAML(clone_path + dockerfile_location, registry_destination, clone_path, deployment_file_location)
    build_push_image_using_kaniko(deployment_file_location=deployment_file_location)
    print('START')


def git_clone_and_checkout(repo_url: str, branch: str, commit: str, base_dir: str, build_id: str):
    clone_path = base_dir + '/' + build_id + '/' + repo_url.split('/')[4].split('.')[0]
    try:
        repo = Repo.clone_from(repo_url, clone_path, branch=branch)
        repo.git.checkout(commit)
        return clone_path
    except RepositoryNotFound:
        raise RepositoryNotFound


def create_deployment_YAML(dockerfile: str, destination: str, build_context: str, deployment_file_location: str):
    try:
        fstream = open(template_file, 'r')
        data = yaml.load(fstream)
        data['metadata']['name'] = deployment_file_location.split('.')[0].split('/')[2]
        data['spec']['containers'][0]['args'] = [f"--dockerfile={dockerfile}", f"--destination={destination}", f"--context={build_context}"]
        data['spec']['containers'][0]['volumeMounts'][1]['mountPath'] = '/kaniko/.docker/config.json'
        data['spec']['containers'][0]['volumeMounts'][1]['name'] = 'task-pv-storage'
        data['spec']['containers'][0]['volumeMounts'][1]['subPath'] = 'config.json'
        with open(deployment_file_location, 'w') as yaml_file:
            yaml_file.write( yaml.dump(data, default_flow_style=False))
        return deployment_file_location
    except IOError:
        raise IOError


def build_push_image_using_kaniko(deployment_file_location: str):
    k8s_config = config.load_incluster_config()
    v1 = client.CoreV1Api()
    apiV1 = client.AppsV1Api()
    namespace='default'
    with open(deployment_file_location) as f:
        dep = yaml.safe_load(f)
        resp = v1.create_namespaced_pod(
            body=dep, namespace="default")
        print("Deployment created. status='%s'" % resp.metadata.name)