#!/usr/bin/env python

import os

import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN
import geni.rspec.emulab.spectrum as spectrum


tourDescription = """
### OAI 5G using the POWDER Indoor OTA Lab

This profile instantiates an experiment for testing OAI 5G with COTS UEs in standalone mode using resources in the POWDER indoor over-the-air (OTA) lab.  The indoor OTA lab includes:

- 4x NI X310 SDRs, each with a UBX-160 daughter card occupying channel 0. The TX/RX and RX2 ports on this channel are connected to broadband antennas. The SDRs are connected via fiber to near-edge compute resources.
- 4x Intel NUC compute nodes, each equipped with a Quectel RM500Q-GL 5G module that has been provisioned with a SIM card. The NUCs are also equipped with NI B210 SDRs, but they are not the focus of this profile.

You can find a diagram of the lab layout here: [OTA Lab Diagram](https://gitlab.flux.utah.edu/powderrenewpublic/powder-deployment/-/raw/master/diagrams/ota-lab.png)

The following will be deployed:

- Server-class compute node (d430) with a Docker-based OAI 5G Core Network
- Server-class compute node (d740) with OAI 5G gNodeB (fiber connection to 5GCN and an X310)
- One to four Intel NUC compute nodes, each with a 5G module and supporting tools

Note: This profile currently requires the use of the 3550-3600 MHz spectrum range and you need an approved reservation for this spectrum in order to use it.  It's also strongly recommended that you include the following necessary resources in your reservation to gaurantee their availability at the time of your experiment:

- A d430 compute node to host the core network
- A d740 compute node for the gNodeB
- One of the four indoor OTA X310s
- All four indoor OTA NUCs

#### Bleeding-edge Software Caveats!

You may see warnings, errors, crashes, etc, when running the OAI gNodeB soft modem. The COTS modules may sometimes fail to attach. Please subscribe to the OAI user or developer mailing lists to monitor and ask questions about the current status of OAI 5G: https://gitlab.eurecom.fr/oai/openairinterface5g/-/wikis/MailingList.

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

Open a session on `ota-x310-X-gnb-comp` and start the gNodeB softmodem:

```
sudo numactl --membind=0 --cpubind=0 \
  /var/tmp/openairinterface5g/cmake_targets/ran_build/build/nr-softmodem -E \
  -O /var/tmp/etc/oai/gnb.sa.band78.fr1.106PRB.usrpx310.conf --sa \
  --MACRLCs.[0].dl_max_mcs 28 --tune-offset 23040000
```

Note: you can add the `-d` flag to the above command to enable the `nrcsope` if you have X-forwarding activated or you're using VNC.

On `ota-nucX`:

After you've started the gNodeB, you can bring the COTS UE online. First, start the Quectel connection manager:

```
sudo quectel-CM -s internet -4
```

In another session on the same node, bring the UE online:

```
# turn modem on
sudo sh -c "chat -t 1 -sv '' AT OK 'AT+CFUN=1' OK < /dev/ttyUSB2 > /dev/ttyUSB2"
```

The UE should attach to the network and pick up an IP address on the wwan interface associated with the module. You'll see the wwan interface name and the IP address in the stdout of the quectel-CM process.

You should now be able to generate traffic in either direction:

```
# from UE to CN traffic gen node (in session on ota-nucX)
ping 192.168.70.135

# from CN traffic generation service to UE (in session on cn node)
sudo docker exec -it oai-ext-dn ping <IP address from quectel-CM>
```

This process may be repeated on the indoor OTA NUCs in order to attach multiple modules to the network.

Known Issues and Workarounds:

- The oai-amf may not list all registered UEs in the assoicated log.
- The gNodeB soft modem may spam warnings/errors about missed DCI or ULSCH detections. It may crash unexpectedly.
- Exiting the gNodeB soft modem with ctrl-c will often leave the SDR in a funny state, so that the next time you start it, it may crash with a UHD error. If this happens, simply start it again.
- The module may not attach to the network or pick up an IP address on the first try. If so, put the module into airplane mode with `sudo sh -c "chat -t 1 -sv '' AT OK 'AT+CFUN=4' OK < /dev/ttyUSB2 > /dev/ttyUSB2"`, kill and restart quectel-CM, then bring the module back online. If the module still fails to associate and/or pick up an IP, try putting the module into airplane mode, rebooting the associated NUC, and bringing the module back online again.
- `chat` may return an error sometimes. If so, just run the command again.

"""

BIN_PATH = "/local/repository/bin"
ETC_PATH = "/local/repository/etc"
UBUNTU_IMG = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
COTS_UE_IMG = "urn:publicid:IDN+emulab.net+image+PowderTeam:cots-jammy-image"
COMP_MANAGER_ID = "urn:publicid:IDN+emulab.net+authority+cm"
DEFAULT_NR_CN_HASH = "v2.1.9"
DEFAULT_NR_RAN_HASH = "f3eb713084e4134ca265f1153b68a102714a319a" # 2025.wk15
OAI_DEPLOY_SCRIPT = os.path.join(BIN_PATH, "deploy-oai.sh")


def x310_node_pair(idx, x310_radio):
    role = "nodeb"
    node = request.RawPC("{}-gnb-comp".format(x310_radio))
    node.component_manager_id = COMP_MANAGER_ID
    node.hardware_type = params.sdr_nodetype

    if params.sdr_compute_image:
        node.disk_image = params.sdr_compute_image
    else:
        node.disk_image = UBUNTU_IMG

    node_radio_if = node.addInterface("usrp_if")
    node_radio_if.addAddress(rspec.IPv4Address("192.168.40.1",
                                               "255.255.255.0"))

    radio_link = request.Link("radio-link-{}".format(idx))
    radio_link.bandwidth = 10*1000*1000
    radio_link.addInterface(node_radio_if)

    radio = request.RawPC("{}-gnb-sdr".format(x310_radio))
    radio.component_id = x310_radio
    radio.component_manager_id = COMP_MANAGER_ID
    radio_link.addNode(radio)

    nodeb_cn_if = node.addInterface("nodeb-cn-if")
    nodeb_cn_if.addAddress(rspec.IPv4Address("192.168.1.{}".format(idx + 2), "255.255.255.0"))
    cn_link.addInterface(nodeb_cn_if)

    if params.oai_ran_commit_hash:
        oai_ran_hash = params.oai_ran_commit_hash
    else:
        oai_ran_hash = DEFAULT_NR_RAN_HASH

    cmd = "{} '{}' {}".format(OAI_DEPLOY_SCRIPT, oai_ran_hash, role)
    node.addService(rspec.Execute(shell="bash", command=cmd))
    node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/tune-sdr-iface.sh"))

def b210_nuc_pair(b210_node):
    node = request.RawPC("{}-cots-ue".format(b210_node))
    node.component_manager_id = COMP_MANAGER_ID
    node.component_id = b210_node
    node.disk_image = COTS_UE_IMG
    node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/module-off.sh"))
    node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/update-udhcpc-script.sh"))
    node.addService(rspec.Execute(shell="bash", command="sudo apt install -y iperf3"))

pc = portal.Context()

node_types = [
    ("d430", "Emulab, d430"),
    ("d740", "Emulab, d740"),
    ("d760p", "Emulab, d760p"),
    ("d760-gpu", "Emulab, d760-gpu"),
]
pc.defineParameter(
    name="sdr_nodetype",
    description="Type of compute node paired with the SDRs",
    typ=portal.ParameterType.STRING,
    defaultValue=node_types[1],
    legalValues=node_types
)

pc.defineParameter(
    name="cn_nodetype",
    description="Type of compute node to use for CN node (if included)",
    typ=portal.ParameterType.STRING,
    defaultValue=node_types[0],
    legalValues=node_types
)

pc.defineParameter(
    name="oai_ran_commit_hash",
    description="Commit hash for OAI RAN",
    typ=portal.ParameterType.STRING,
    defaultValue="",
    advanced=True
)

pc.defineParameter(
    name="oai_cn_commit_hash",
    description="Commit hash for OAI (5G)CN",
    typ=portal.ParameterType.STRING,
    defaultValue="",
    advanced=True
)

pc.defineParameter(
    name="sdr_compute_image",
    description="Image to use for compute connected to SDRs",
    typ=portal.ParameterType.STRING,
    defaultValue="",
    advanced=True
)

indoor_ota_x310s = [
    ("ota-x310-1",
     "USRP X310 #1"),
    ("ota-x310-2",
     "USRP X310 #2"),
    ("ota-x310-3",
     "USRP X310 #3"),
    ("ota-x310-4",
     "USRP X310 #4"),
]
pc.defineParameter(
    name="x310_radio",
    description="X310 Radio (for OAI gNodeB)",
    typ=portal.ParameterType.STRING,
    defaultValue=indoor_ota_x310s[0],
    legalValues=indoor_ota_x310s
)

indoor_ota_nucs = [
    ("ota-nuc{}".format(i), "Indoor OTA nuc{} with B210 and COTS UE".format(i)) for i in range(1, 5)
]

pc.defineStructParameter(
    name="ue_nodes",
    description="Indoor OTA NUC with COTS UE (can't be the same as gNodeB node!)",
    defaultValue=[{ "node_id": "ota-nuc2" }],
    multiValue=True,
    min=1,
    max=4,
    members=[
        portal.Parameter(
            "node_id",
            "Indoor OTA NUC",
            portal.ParameterType.STRING,
            indoor_ota_nucs[0],
            indoor_ota_nucs
        )
    ]
)

portal.context.defineStructParameter(
    "freq_ranges", "Frequency Ranges To Transmit In",
    defaultValue=[{"freq_min": 3550.0, "freq_max": 3600.0}],
    multiValue=True,
    min=0,
    multiValueTitle="Frequency ranges to be used for transmission.",
    members=[
        portal.Parameter(
            "freq_min",
            "Frequency Range Min",
            portal.ParameterType.BANDWIDTH,
            3550.0,
            longDescription="Values are rounded to the nearest kilohertz."
        ),
        portal.Parameter(
            "freq_max",
            "Frequency Range Max",
            portal.ParameterType.BANDWIDTH,
            3600.0,
            longDescription="Values are rounded to the nearest kilohertz."
        ),
    ]
)

params = pc.bindParameters()
pc.verifyParameters()
request = pc.makeRequestRSpec()

role = "cn"
cn_node = request.RawPC("cn5g-docker-host")
cn_node.component_manager_id = COMP_MANAGER_ID
cn_node.hardware_type = params.cn_nodetype
cn_node.disk_image = UBUNTU_IMG
cn_if = cn_node.addInterface("cn-if")
cn_if.addAddress(rspec.IPv4Address("192.168.1.1", "255.255.255.0"))
cn_link = request.Link("cn-link")
cn_link.setNoBandwidthShaping()
cn_link.addInterface(cn_if)

if params.oai_cn_commit_hash:
    oai_cn_hash = params.oai_cn_commit_hash
else:
    oai_cn_hash = DEFAULT_NR_CN_HASH

cmd = "{} '{}' {}".format(OAI_DEPLOY_SCRIPT, oai_cn_hash, role)
cn_node.addService(rspec.Execute(shell="bash", command=cmd))

# single x310 for now
x310_node_pair(0, params.x310_radio)

for ue_node in params.ue_nodes:
    b210_nuc_pair(ue_node.node_id)

for frange in params.freq_ranges:
    request.requestSpectrum(frange.freq_min, frange.freq_max, 0)

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

pc.printRequestRSpec(request)
