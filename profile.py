#!/usr/bin/env python

import os

import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN
import geni.rspec.emulab.spectrum as spectrum


tourDescription = """
### OAI 5G RAN Slicing

This profile instantiates an experiment for testing OAI 5G RAN slicing. Currently, it deploys only the modified version of OAI Core Network.

- Server-class compute node (d430) with a Docker-based OAI 5G Core Network
- A d430 compute node to host the core network

"""

tourInstructions = """

Startup scripts will still be running when your experiment becomes ready.  Watch the "Startup" column on the "List View" tab for your experiment and wait until all of the compute nodes show "Finished" before proceeding.

After all startup scripts have finished...

On `cn5g-docker-host`, open a terminal session via SSH, or using the shell option for that node in the portal.

Start the 5G core network services.

```
cd /var/tmp/oai-cn5g
sudo docker compose up -d
```
 
It will take several seconds for the services to start up. Since we started the services in detached mode, you can check the status of the services with:

```
sudo docker compose ps
```

In another session, start following the logs for the AMF. This way you can see when the UE attaches to the network.

```
cd /var/tmp/oai-cn5g
sudo docker compose logs -f oai-amf
```

If you'd like to monitor traffic between the various network functions and the gNodeB, start tshark in yet another session:

```
sudo tshark -i oai-cn5g \
  -f "not arp and not port 53 and not host archive.ubuntu.com and not host security.ubuntu.com"
```

"""

BIN_PATH = "/local/repository/bin"
ETC_PATH = "/local/repository/etc"
UBUNTU_IMG = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
# COTS_UE_IMG = "urn:publicid:IDN+emulab.net+image+PowderTeam:cots-jammy-image"
COMP_MANAGER_ID = "urn:publicid:IDN+emulab.net+authority+cm"
DEFAULT_NR_CN_HASH = "v2.1.9"
# DEFAULT_NR_RAN_HASH = "f3eb713084e4134ca265f1153b68a102714a319a" # 2025.wk15
OAI_CN5G_DEPLOY_SCRIPT = os.path.join(BIN_PATH, "deploy-oai-cn5g.sh")


pc = portal.Context()

node_types = [
    ("d430", "Emulab, d430"),
    ("d710", "Emulab, d710"),
]

pc.defineParameter(
    name="repo_url", 
    description="GitHub repo for CN5G", 
    typ=portal.ParameterType.STRING,
    defaultValue="https://github.com/gulechakan/oai-5gc-modified"
    )

pc.defineParameter(
    name="repo_branch", 
    description="Branch or commit hash", 
    typ=portal.ParameterType.STRING, 
    defaultValue="main"
    )

pc.defineParameter(
    name="cn_nodetype",
    description="Type of compute node to use for CN node (if included)",
    typ=portal.ParameterType.STRING,
    defaultValue=node_types[0],
    legalValues=node_types
)

pc.defineParameter(
    name="oai_cn_commit_hash",
    description="Commit hash for OAI (5G)CN",
    typ=portal.ParameterType.STRING,
    defaultValue="",
    advanced=True
)

# portal.context.defineStructParameter(
#     "freq_ranges", "Frequency Ranges To Transmit In",
#     defaultValue=[{"freq_min": 3550.0, "freq_max": 3600.0}],
#     multiValue=True,
#     min=0,
#     multiValueTitle="Frequency ranges to be used for transmission.",
#     members=[
#         portal.Parameter(
#             "freq_min",
#             "Frequency Range Min",
#             portal.ParameterType.BANDWIDTH,
#             3550.0,
#             longDescription="Values are rounded to the nearest kilohertz."
#         ),
#         portal.Parameter(
#             "freq_max",
#             "Frequency Range Max",
#             portal.ParameterType.BANDWIDTH,
#             3600.0,
#             longDescription="Values are rounded to the nearest kilohertz."
#         ),
#     ]
# )

params = pc.bindParameters()
pc.verifyParameters()
request = pc.makeRequestRSpec()

# role = "cn"

# CN5G Host
cn_node = request.RawPC("cn5g-host")
cn_node.component_manager_id = COMP_MANAGER_ID
cn_node.hardware_type = params.cn_nodetype
cn_node.disk_image = UBUNTU_IMG

# CN5G Interface + Subnet
# cn_if = cn_node.addInterface("cn-if")
# cn_if.addAddress(rspec.IPv4Address("192.168.1.1", "255.255.255.0"))
# cn_link = request.Link("cn-link")
# cn_link.setNoBandwidthShaping()
# cn_link.addInterface(cn_if)

# if params.oai_cn_commit_hash:
#     oai_cn_hash = params.oai_cn_commit_hash
# else:
#     oai_cn_hash = DEFAULT_NR_CN_HASH

# cmd = "{} '{}' {}".format(OAI_CN5G_DEPLOY_SCRIPT, oai_cn_hash, role)
# cn_node.addService(rspec.Execute(shell="bash", command=cmd))

# CN5G Startup Script
deploy_cmd = "/local/repository/bin/deploy-oai-cn5g.sh {} {}".format(params.repo_url, params.repo_branch)
cn_node.addService(rspec.Execute(shell="bash", command=deploy_cmd))

# for frange in params.freq_ranges:
#     request.requestSpectrum(frange.freq_min, frange.freq_max, 0)

# Tour
tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

pc.printRequestRSpec(request)
