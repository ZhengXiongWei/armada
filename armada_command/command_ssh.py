from __future__ import print_function
import argparse
import os
import json
import subprocess

import armada_api
import armada_utils


def parse_args():
    parser = argparse.ArgumentParser(description='ssh into docker container.')
    add_arguments(parser)
    return parser.parse_args()


def add_arguments(parser):
    parser.add_argument('microservice_name', nargs='?',
                        help='Name of the microservice or container_id to ssh into. '
                             'If not provided it will use MICROSERVICE_NAME env variable.')
    parser.add_argument('command', nargs=argparse.REMAINDER,
                        help='Execute command inside the container.')


def command_ssh(args):
    microservice_name = args.microservice_name or os.environ['MICROSERVICE_NAME']
    if not microservice_name:
        raise ValueError('No microservice name supplied.')

    instances = armada_utils.get_matched_containers(microservice_name)
    instances_count = len(instances)
    if instances_count > 1:
        raise armada_utils.ArmadaCommandException(
            'There are too many ({instances_count}) matching containers. '
            'Provide more specific container_id or microservice name.'.format(**locals()))
    instance = instances[0]

    service_id = instance['ServiceID']
    container_id = service_id.split(':')[0]
    payload = {'container_id': container_id}

    result = json.loads(armada_api.get('ssh-address', payload, ship_name=instance['Node']))

    if result['status'] != 'ok':
        raise armada_utils.ArmadaCommandException('armada API error: {0}'.format(result['error']))
    ssh_host, ssh_port = result['ssh'].split(':')

    print("Connecting to {0} at {1}:{2}...".format(instance['ServiceName'], ssh_host, ssh_port))

    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'keys/docker.key')

    tty = ''
    if args.command:
        command = ' '.join(args.command)
        # TODO: Should we replace this with -t command flag?
        if not command.startswith('bash'):
            tty = '-t'
    else:
        command = 'bash'

    exec_command = 'docker exec -i {tty} {container_id} {command}'.format(**locals())
    ssh_command = 'ssh -t {tty} -p 2201 -i {docker_key_file} -o StrictHostKeyChecking=no docker@{ssh_host} sudo {exec_command}'.format(**locals())
    print(ssh_command)
    subprocess.call(ssh_command, shell=True)
