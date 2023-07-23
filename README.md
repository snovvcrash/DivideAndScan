<p align="center">
  <img src="https://user-images.githubusercontent.com/23141800/113610876-632a4300-9656-11eb-9583-d07f4e34d774.png" width="350px" alt="DivideAndScan">
</p>

<p align="center">
  <strong>Divide <strike>Et Impera</strike> And Scan (and also merge the scan results)</strong>
</p>

<p align="center">
  <a href="https://github.com/snovvcrash/DivideAndScan/blob/main/pyproject.toml#L3"><img src="https://img.shields.io/badge/version-1.0.1-success" alt="version" /></a>
  <a href="https://github.com/snovvcrash/DivideAndScan/search?l=python"><img src="https://img.shields.io/badge/python-3.9-blue?logo=python&logoColor=white" alt="python" /></a>
  <a href="https://www.codacy.com/gh/snovvcrash/DivideAndScan/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=snovvcrash/DivideAndScan&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/35f0bdfece9846d7aab3888b01642813" alt="codacy" /></a>
  <a href="https://github.com/snovvcrash/DivideAndScan/actions/workflows/publish-to-pypi.yml"><img src="https://github.com/snovvcrash/DivideAndScan/actions/workflows/publish-to-pypi.yml/badge.svg" alt="pypi" /></a>
  <a href="https://github.com/snovvcrash/DivideAndScan/actions/workflows/publish-to-docker-hub.yml"><img src="https://github.com/snovvcrash/DivideAndScan/actions/workflows/publish-to-docker-hub.yml/badge.svg" alt="docker" /></a>
</p>

---

**D**ivide**A**nd**S**can is used to efficiently automate port scanning routine by splitting it into 3 phases:

1. Discover open ports for a bunch of targets.
2. Run Nmap individually for each target with version grabbing and NSE actions.
3. Merge the results into a single Nmap report (different formats available).

For the 1st phase a *fast port scanner*\* is intended to be used, whose output is parsed and stored in a single file database ([TinyDB](https://github.com/msiemens/tinydb)). Next, during the 2nd phase individual Nmap scans are launched for each target with its set of open ports (multiprocessing is supported) according to the database data. Finally, in the 3rd phase separate Nmap outputs are merged into a single report in different formats (XML / HTML / simple text / grepable) with [nMap_Merger](https://github.com/CBHue/nMap_Merger). The visualization portion is provided by [DrawNmap](https://github.com/jor6PS/DrawNmap).

Potential use cases:

* Pentest engagements / red teaming with a large scope to enumerate.
* Cybersecurity wargames / training CTF labs.
* OSCP certification exam.

\* Available port scanners:

* [Nmap](https://github.com/nmap/nmap)
* [Masscan](https://github.com/robertdavidgraham/masscan)
* [RustScan](https://github.com/RustScan/RustScan)
* [Naabu](https://github.com/projectdiscovery/naabu)
* [NimScan](https://github.com/elddy/NimScan)
* [sx](https://github.com/v-byte-cpu/sx)

> **DISCLAIMER.** All information contained in this repository is provided for educational and research purposes only. The author is not responsible for any illegal use of this tool.

## How It Works

![how-it-works.png](https://user-images.githubusercontent.com/23141800/113610892-67566080-9656-11eb-8520-8fa2dcaf3463.png)

## How to Install

### Prerequisites

To successfully *divide and scan* we need to get some good port scanning tools (in the examples below GitHub releases are grabbed via [eget](https://github.com/zyedidia/eget)).

📑 **Note:** if you don't feel like messing with dependecies on your host OS, skip to the [Docker](#using-from-docker) part.

#### Nmap

```bash
sudo apt install nmap xsltproc -y
sudo nmap --script-updatedb
```

#### Masscan

```bash
pushd /tmp
wget https://github.com/robertdavidgraham/masscan/archive/refs/heads/master.zip -O masscan-master.zip
unzip masscan-master.zip
cd masscan-master
make
sudo make install
popd && rm -rf /tmp/masscan-master*
```

#### RustScan

```bash
eget -t 2.0.1 -a amd64 RustScan/RustScan --to /tmp/rustscan.deb
sudo dpkg -i /tmp/rustscan.deb && rm /tmp/rustscan.deb
sudo wget https://gist.github.com/snovvcrash/8b85b900bd928493cd1ae33b2df318d8/raw/fe8628396616c4bf7a3e25f2c9d1acc2f36af0c0/rustscan-ports-top1000.toml -O /root/.rustscan.toml
```

#### Naabu

```bash
sudo mkdir /opt/naabu
sudo eget -s linux/amd64 projectdiscovery/naabu --to /opt/naabu
sudo ln -sv /opt/naabu/naabu /usr/local/bin/naabu
```

#### NimScan

```bash
sudo mkdir /opt/nimscan
sudo eget -a NimScan elddy/NimScan --to /opt/nimscan
sudo ln -sv /opt/nimscan/nimscan /usr/local/bin/nimscan
```

#### sx

```bash
sudo mkdir /opt/sx
sudo eget -s linux/amd64 v-byte-cpu/sx --to /opt/sx
sudo ln -sv /opt/sx/sx /usr/local/bin/sx
```

#### dnsx

```bash
sudo mkdir /opt/pd
sudo eget -s linux/amd64 projectdiscovery/dnsx --to /opt/pd
sudo ln -sv /opt/pd/dnsx /usr/local/bin/dnsx
```

### Installation

DivideAndScan is available on PyPI as `divideandscan`, though I recommend installing it from GitHub with [pipx](https://github.com/pipxproject/pipx) in order to always have the bleeding-edge version:

```console
~$ pipx install -f "git+https://github.com/snovvcrash/DivideAndScan.git"
~$ das
```

For debbugging purposes you can set up a dev environment with [poetry](https://github.com/python-poetry/poetry):

```console
~$ git clone --recurse-submodules https://github.com/snovvcrash/DivideAndScan
~$ cd DivideAndScan
~$ poetry install
~$ poetry run das
```

📑 **Note:** DivideAndScan uses sudo to run all the port scanners, so it will ask for the password when scanning commands are invoked.

### Using from Docker

[![dockeri.co](https://dockeri.co/image/snovvcrash/divideandscan)](https://hub.docker.com/r/snovvcrash/divideandscan)

You can run DivideAndScan in a Docker container as follows:

```console
~$ docker run --rm -it --name das -v ~/.das:/root/.das -v `pwd`:/app -p 8050:8050 snovvcrash/divideandscan
```

Since the tool requires some input data and produces some output data, you should specify your current working directory as the mount point at `/app` within the container. Also publishing port 8050 on host allows to access the [Dash](https://github.com/plotly/dash) app used for Nmap reports visualization.

You may want to set an alias to make the base command shorter:

```console
~$ alias das='docker run --rm -it --name das -v ~/.das:/root/.das -v `pwd`:/app -p 8050:8050 snovvcrash/divideandscan'
~$ das
```

## How to Use

![how-to-use.png](https://user-images.githubusercontent.com/23141800/113610915-6fae9b80-9656-11eb-8b1a-db503dd43861.png)

### 1. Filling the DB

<table>
<tr>
<td>

Provide the `add` module a command for a fast port scanner to discover open ports in a desired range.

⚠️ **Warning:** please, make sure that you understand what you're doing, because nearly all port scanning tools [can damage the system being tested](https://github.com/RustScan/RustScan/wiki/Usage#%EF%B8%8F-warning) if used improperly.

```console
# Nmap, -v flag is always required for correct parsing!
~$ das add nmap '-v -n -Pn -e eth0 --min-rate 1000 -T4 -iL hosts.txt -p1-65535 --open'
# Masscan
~$ das add masscan '--rate 1000 -iL hosts.txt -p1-65535 --open'
# RustScan
~$ das add rustscan '-b 1000 -t 2000 -u 5000 -a hosts.txt -r 1-65535 -g --no-config'
# Naabu
~$ das add naabu '-rate 1000 -iL hosts.txt -p - -silent -s s'
# NimScan
~$ das add nimscan '192.168.1.0/24 -vi -p:1-65535 -f:500'
# sx
~$ sudo sx arp -i eth0 192.168.1.0/24 --json | tee arp.cache
~$ das add sx 'tcp syn -a arp.cache -i eth0 --rate 1000/s 192.168.1.0/24 -p 445,3389'
```

When the module starts its work, a directory `~/.das/db` is created where the database file and raw scan results will be put when the module routine finishes.

</td>
</tr>
</table>

### 2. Targeted Scanning

<table>
<tr>
<td>

Launch targeted Nmap scans with the `scan` module. You can adjust the scan surface with either `-hosts` or `-ports` option:

```console
# Scan by hosts
~$ das scan -hosts all -oA report1
~$ das scan -hosts 192.168.1.0/24,10.10.13.37 -oA report1
~$ das scan -hosts hosts.txt -oA report1
# Scan by ports
~$ das scan -ports all -oA report2
~$ das scan -ports 22,80,443,445 -oA report2
~$ das scan -ports ports.txt -oA report2
```

To start Nmap simultaneously in multiple processes, specify the `-parallel` switch and set number of workers with the `-proc` option (if no value is provided, it will default to the number of processors on the machine):

```console
~$ das scan -hosts all -oA report -parallel [-proc 4]
```

The output format is selected with `-oX`, `-oN`, `-oG` and `-oA` options for XML+HTML formats, simple text format, grepable format and all formats respectively. When the module completes its work, a directory `~/.das/nmap_<DB_NAME>` is created containig Nmap raw scan reports.

Also, you can inspect the contents of the database with `-show` option before actually launching the scans:

```console
~$ das scan -hosts all -show
```

</td>
</tr>
</table>

### 3 (Optional). Merging the Reports

<table>
<tr>
<td>

In order to generate a report independently of the `scan` module, you should use the `report` module. It will search for Nmap raw scan reports in the `~/.das/nmap_<DB_NAME>` directory and process and merge them based on either `-hosts` or `-ports` option:

```console
# Merge outputs by hosts
~$ das report -hosts all -oA report1
~$ das report -hosts 192.168.1.0/24,10.10.13.37 -oA report1
~$ das report -hosts hosts.txt -oA report1
# Merge outputs by ports
~$ das report -ports all -oA report2
~$ das report -ports 22,80,443,445 -oA report2
~$ das report -ports ports.txt -oA report2
```

📑 **Note:** keep in mind that the `report` module does **not** search the DB when processing the `-hosts` or `-ports` options, but looks for Nmap raw reports directly in `~/.das/nmap_<DB_NAME>` directory instead; it means that `-hosts 127.0.0.1` argument value will be successfully resolved only if `~/.das/nmap_<DB_NAME>/127-0-0-1.*` files exist, and `-ports 80` argument value will be successfully resolved only if `~/.das/nmap_<DB_NAME>/port80.*` files exist.

</td>
</tr>
</table>

<details>
<summary><strong>🔥 Example 🔥</strong></summary>

Let's enumerate open ports for all live machines on [Hack The Box](https://www.hackthebox.eu/home/machines).

1. Add mappings "host ⇄ open ports" to the database with Masscan. For demonstration purposes I will exclude dynamic port range to avoid unnecessary stuff by using `-p1-49151`. On the second screenshot I'm reviewing scan results by hosts and by ports:

```console
~$ das -db htb add -rm masscan '-e tun0 --rate 1000 -iL hosts.txt -p1-49151 --open'
```

<p align="center">
  <img src="https://user-images.githubusercontent.com/23141800/117919590-f578d300-b2f5-11eb-8afb-f8e3ed851e62.png" alt="example-1.png">
</p>

```console
~$ das -db htb scan -hosts all -show
~$ das -db htb scan -ports all -show
```

<p align="center">
  <img src="https://user-images.githubusercontent.com/23141800/117919602-fa3d8700-b2f5-11eb-8d4a-f2edb0272e2e.png" alt="example-2.png">
</p>

2. Launch Nmap processes for each target to enumerate only ports that we're interested in (the open ports). On the second screenshot I'm doing the same but starting Nmap processes simultaneously:

```console
~$ das -db htb scan -hosts all -oA report
```

<p align="center">
  <img src="https://user-images.githubusercontent.com/23141800/117919624-03c6ef00-b2f6-11eb-9539-64a5a6ced1cf.png" alt="example-3.png">
</p>

```console
~$ das -db htb scan -hosts all -oA report -nmap '-Pn -sVC -O' -parallel
```

<p align="center">
  <img src="https://user-images.githubusercontent.com/23141800/117919633-0a556680-b2f6-11eb-8cbe-78d1e9ce16f1.png" alt="example-4.png">
</p>

3. As a result we now have a single report in all familiar Nmap formats (simple text, grepable, XML) as well as a pretty HTML report.

<p align="center">
  <img src="https://user-images.githubusercontent.com/23141800/117919635-0c1f2a00-b2f6-11eb-933f-ee812e6f6bd0.png" alt="example-5.png">
</p>

</details>

## Bring Your Own Scanner!

You can pair your favourite port scanner with DivideAndScan by implementing a single **parse** method for its output in `das/parsers/DUMMY_SCANNER.py` (see [example](/das/parsers/masscan.py) for masscan):

```python
from das.parsers import IAddPortscanOutput


class AddPortscanOutput(IAddPortscanOutput):
    """Child class for processing DUMMY_SCANNER output."""

    def parse(self):
        """
        DUMMY_SCANNER raw output parser.

        :return: a pair of values (portscan raw output filename, number of hosts added to DB)
        :rtype: tuple
        """
        hosts = set()
        for line in self.portscan_raw:
            # DUMMY_SCANNER parser implementation
            pass

        return (self.portscan_out, len(hosts))
```

## Help

```
usage: das [-h] [-db DB] {db,add,scan,dns,report,parse,draw,tree,help} ...

 -----------------------------------------------------------------------------------------------
|  ________  .__      .__    .___        _____              .____________                       |
|  \______ \ |__|__  _|__| __| _/____   /  _  \   ____    __| _/   _____/ ____ _____    ____    |
|   |    |  \|  \  \/ /  |/ __ |/ __ \ /  /_\  \ /    \  / __ |\_____  \_/ ___\\__  \  /    \   |
|   |    `   \  |\   /|  / /_/ \  ___//    |    \   |  \/ /_/ |/        \  \___ / __ \|   |  \  |
|  /_______  /__| \_/ |__\____ |\___  >____|__  /___|  /\____ /_______  /\___  >____  /___|  /  |
|          \/                 \/    \/        \/     \/      \/       \/     \/     \/     \/   |
|  {@snovvcrash}            {https://github.com/snovvcrash/DivideAndScan}             {vX.Y.Z}  |
 -----------------------------------------------------------------------------------------------

positional arguments:
  {db,add,scan,dns,report,parse,draw,tree,help}
    db                  utilities for manual DB manipulations
    add                 run a full port scan and add the output to DB
    scan                run targeted Nmap scans against hosts and ports from DB
    dns                 map domain names from an input file to corresponding IP addresses from the DB
    report              merge separate Nmap outputs into a single report (https://github.com/CBHue/nMap_Merger)
    parse               parse raw Nmap XML reports by service names and print entries in format {service}://{host}:{port}}
    draw                visualize Nmap XML reports (https://github.com/jor6PS/DrawNmap)
    tree                show contents of the ~/.das/ directory using tree
    help                show builtin --help dialog of a selected port scanner

options:
  -h, --help            show this help message and exit
  -db DB                DB name to work with

Psst, hey buddy... Wanna do some organized p0r7 5c4nn1n6?
```

## ToDo

* [x] <strike>Add [projectdiscovery/naabu](https://github.com/projectdiscovery/naabu) parser</strike>
* [x] <strike>Add [elddy/NimScan](https://github.com/elddy/NimScan) parser</strike>
* [x] <strike>Add [sx](https://github.com/v-byte-cpu/sx) parser</strike>
* [ ] Add [ZMap](https://github.com/zmap/zmap) parser
* [x] <strike>Store hostnames (if there're any) next to their IP values</strike>
* [x] <strike>Add `fuff` switch to automate web directory fuzzing</strike> (added `parse` module)
