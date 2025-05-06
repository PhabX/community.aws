#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: lightsail_disk
version_added: 9.2.0
short_description: Manage Disks in AWS Lightsail
description:
  - Manage Disks in AWS Lightsail.
author:
  - "Fabricio Lopez (@fabriciolopez)"
options:
  state:
    description:
      - Describes the desired state.
    default: present
    choices: ['present', 'absent']
    type: str
  name:
    description: Name of the Disk.
    required: true
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: Create a Lightsail Disk
  community.aws.lightsail_disk:
    state: present
    name: my_disk
  register: my_disk

- name: Delete a Lightsail Disk
  community.aws.lightsail_disk:
    state: absent
    name: my_disk
"""

RETURN = r"""
disk:
  description: disk data
  returned: always
  type: dict
  sample:
    name: "string"
    arn: "string"
    support_code: "string"
    created_at: "2021-02-28T00:04:05.202000+10:30"
    location:
        availability_zone: "string"
        region_name: "us-(east|west)-(1|2)"
    resource_type: Disk
    tags: "dict"
    sizeInGb: "123"
    isSystemDisk: "True|False"
    iops: "123"
    path: "string"
    state: "pending|error|available|in-use|unknown"
    attachedTo: "string"
    isAttached: "True|False"
    attachmentState: "string"
    gbInUse: "123"
    autoMountStatus: "Failed|Pending|Mounted|NotMounted"
"""

try:
    import botocore
except ImportError:
    # will be caught by AnsibleAWSModule
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import (
    is_boto3_error_code,
)

from ansible_collections.community.aws.plugins.module_utils.modules import (
    AnsibleCommunityAWSModule as AnsibleAWSModule,
)


def find_disk_info(module, client, disk_name, fail_if_not_found=False):
    try:
        res = client.get_disk(diskName=disk_name)
    except is_boto3_error_code("NotFoundException") as e:
        if fail_if_not_found:
            module.fail_json_aws(e)
        return None
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)
    return res["disk"]


def create_disk(module, client, disk_name, zone):
    inst = find_disk_info(module, client, disk_name)
    if inst:
        module.exit_json(changed=False, disk=camel_dict_to_snake_dict(inst))
    else:
        create_params = {
            "diskName": disk_name,
            "sizeInGb": 8,
            "availabilityZone": zone,
        }

        try:
            client.create_disk(**create_params)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)

        inst = find_disk_info(module, client, disk_name, fail_if_not_found=True)

        module.exit_json(changed=True, disk=camel_dict_to_snake_dict(inst))


def delete_disk(module, client, disk_name):
    inst = find_disk_info(module, client, disk_name)
    if inst is None:
        module.exit_json(changed=False, disk={})

    changed = False
    try:
        client.delete_disk(diskName=disk_name)
        changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(changed=changed, disk=camel_dict_to_snake_dict(inst))


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        zone=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    client = module.client("lightsail")

    name = module.params.get("name")
    state = module.params.get("state")
    zone = module.params.get("zone")

    if state == "present":
        create_disk(module, client, name, zone)
    elif state == "absent":
        delete_disk(module, client, name)


if __name__ == "__main__":
    main()
