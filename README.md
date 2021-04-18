<p align="center">
  <img src="https://user-images.githubusercontent.com/23141800/113610876-632a4300-9656-11eb-9583-d07f4e34d774.png" width="350px" alt="DivideAndScan">
</p>

<p align="center">
  <strong>Divide <strike>Et Impera</strike> And Scan (and also merge the scan results)</strong>
</p>

<p align="center">
  <a href="https://github.com/snovvcrash/DivideAndScan/blob/main/pyproject.toml#L3"><img src="https://img.shields.io/badge/version-0.1.3-success" alt="version" /></a>
  <a href="https://github.com/snovvcrash/DivideAndScan/search?l=python"><img src="https://img.shields.io/badge/python-3.7-blue?logo=python&logoColor=white" alt="python" /></a>
  <a href="https://www.codacy.com/gh/snovvcrash/DivideAndScan/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=snovvcrash/DivideAndScan&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/35f0bdfece9846d7aab3888b01642813" alt="codacy" /></a>
  <a href="https://github.com/snovvcrash/DivideAndScan/actions/workflows/publish-to-pypi.yml"><img src="https://github.com/snovvcrash/DivideAndScan/actions/workflows/publish-to-pypi.yml/badge.svg" alt="pypi" /></a>
  <a href="https://github.com/snovvcrash/DivideAndScan/actions/workflows/publish-to-docker-hub.yml"><img src="https://github.com/snovvcrash/DivideAndScan/actions/workflows/publish-to-docker-hub.yml/badge.svg" alt="docker" /></a>
</p>

---

**D**ivide**A**nd**S**can is used to efficiently automate port scanning routine by splitting it into 3 phases:

1. Discover open ports for a bunch of targets.
2. Run Nmap individually for each target with version grabbing and NSE actions.
3. Merge the results into a single Nmap report (different formats available).

For the 1st phase a *fast* port scanner is intended to be used ([Masscan](https://github.com/robertdavidgraham/masscan) / [RustScan](https://github.com/RustScan/RustScan) / [Naabu](https://github.com/projectdiscovery/naabu)), whose output is parsed and stored in a database ([TinyDB](https://github.com/msiemens/tinydb)). Next, during the 2nd phase individual Nmap scans are launched for each target with its set of open ports (multiprocessing is supported) according to the database data. Finally, in the 3rd phase separate Nmap outputs are merged into a single report in different formats (XML / HTML / simple text / grepable) with [nMap_Merger](https://github.com/CBHue/nMap_Merger).

Potential use cases:

* Pentest engagements / red teaming with a large scope to enumerate.
* Cybersecurity wargames / training CTF labs.
* OSCP certification exam.

## How It Works

![how-it-works.png](https://user-images.githubusercontent.com/23141800/113610892-67566080-9656-11eb-8520-8fa2dcaf3463.png)

## How to Install

### Prerequisites

To successfully *divide and scan* we need to get some good port scanning tools.

📑 **Note:** if you don't feel like messing with dependecies on your host OS, skip to the [Docker](#using-from-docker) part.

#### Nmap

```bash
sudo apt install nmap sudo xsltproc -y
sudo nmap --script-updatedb
```

#### Masscan

```bash
cd /tmp
git clone https://github.com/robertdavidgraham/masscan.git
cd masscan
make
sudo make install
cd && rm -rf /tmp/masscan
```

#### RustScan

```bash
cd /tmp

wget -qO- https://api.github.com/repos/RustScan/RustScan/releases/latest \
| grep "browser_download_url.*amd64.deb" \
| cut -d: -f2,3 \
| tr -d \" \
| wget -qO rustscan.deb -i-

sudo dpkg -i rustscan.deb
cd && rm /tmp/rustscan.deb

sudo wget https://gist.github.com/snovvcrash/c7f8223cc27154555496a9cbb4650681/raw/a76a2c658370d8b823a8a38a860e4d88051b417e/rustscan-ports-top1000.toml -O /root/.rustscan.toml
```

#### Naabu

```bash
sudo mkdir /opt/projectdiscovery
cd /opt/projectdiscovery

wget -qO- https://api.github.com/repos/projectdiscovery/naabu/releases/latest \
| grep "browser_download_url.*linux-amd64.tar.gz" \
| cut -d: -f2,3 \
| tr -d \" \
| sudo wget -qO naabu.tar.gz -i-

sudo tar -xzf naabu.tar.gz
sudo mv naabu-linux-amd64 naabu
sudo rm LICENSE.md naabu.tar.gz README.md
sudo ln -s /opt/projectdiscovery/naabu /usr/local/bin/naabu
```

### Installation

DivideAndScan is available on PyPI as `divideandscan`, though I recommend installing it from GitHub with [pipx](https://github.com/pipxproject/pipx) in order to always have the bleeding-edge version:

```console
~$ pipx install -f "git+https://github.com/snovvcrash/DivideAndScan.git"
~$ das
```

For debbugging purposes you can set up a dev environment with [poetry](https://github.com/python-poetry/poetry):

```console
~$ git clone https://github.com/snovvcrash/DivideAndScan
~$ cd DivideAndScan
~$ poetry install
~$ poetry run das
```

📑 **Note:** DivideAndScan uses sudo to run all the port scanners, so it will ask for the password when scanning commands are invoked.

### Using from Docker

You can run DivideAndScan in a Docker container as follows:

```console
~$ docker run -it --rm --name das -v `pwd`:/app snovvcrash/divideandscan
```

Since the tool requires some input data and produces some output data, you should specify your current working directory as the mount point at `/app` within the container. You may want to set an alias to make the base command shorter:

```console
~$ alias das='docker run -it --rm --name das -v `pwd`:/app snovvcrash/divideandscan'
~$ das
```

## How to Use

![how-to-use.png](https://user-images.githubusercontent.com/23141800/113610915-6fae9b80-9656-11eb-8b1a-db503dd43861.png)

> More examples coming soon at [snovvcrash.rocks](https://snovvcrash.rocks/)...

### 0. Preparations

<table>
<tr>
<td>

Make a new directory to start DivideAndScan from. The tool will create subdirectories in CWD to store the output, so I recommend launching it from a clean directory to stay organized:

```console
~$ mkdir divideandscan
~$ cd divideandscan
```

</td>
</tr>
</table>

### 1. Filling the DB

<table>
<tr>
<td>

Provide the `add` module a command for a fast port scanner to discover open ports in a desired range.

⚠️ **Warning:** please, make sure that you understand what you're doing, because nearly all port scanning tools [can damage the system being tested](https://github.com/RustScan/RustScan/wiki/Usage#%EF%B8%8F-warning) if used improperly.

```console
# Masscan example
~$ das add -db testdb masscan '--rate 1000 -iL hosts.txt --open -p1-65535'
# RustScan example
~$ das add -db testdb rustscan '-b 1000 -t 2000 -u 5000 -a hosts.txt -r 1-65535 -g --no-config'
# Naabu example
~$ das add -db testdb naabu '-rate 1000 -iL hosts.txt -p - -silent -s s'
```

When the module completes its work, a hidden directory `.db` is created in CWD containig the database file and raw scan results.

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
~$ das scan -db testdb -hosts all -oA report1
~$ das scan -db testdb -hosts 192.168.1.0/24,10.10.13.37 -oA report1
~$ das scan -db testdb -hosts hosts.txt -oA report1
# Scan by ports
~$ das scan -db testdb -ports all -oA report2
~$ das scan -db testdb -ports 22,80,443,445 -oA report2
~$ das scan -db testdb -ports ports.txt -oA report2
```

To start Nmap simultaneously in multiple processes, specify the `-parallel` switch and set number of workers with the `-proc` option (if no value is provided, it will default to the number of processors on the machine):

```console
~$ das scan -db testdb -hosts all -oA report -parallel [-proc 4]
```

The output format is selected with `-oX`, `-oN`, `-oG` and `-oA` options for XML+HTML formats, simple text format, grepable format and all formats respectively. When the module completes its work, a hidden directory `.nmap` is created in CWD containig Nmap raw scan reports.

Also, you can inspect the contents of the database with `-show` option before actually launching the scans:

```console
~$ das scan -db testdb -hosts all -show
```

</td>
</tr>
</table>

### 3 (Optional). Merging the Reports

<table>
<tr>
<td>

In order to generate a report independently of the `scan` module, you should use the `report` module. It will search for Nmap raw scan reports in the `.nmap` directory and process and merge them based on either `-hosts` or `-ports` option:

```console
# Merge outputs by hosts
~$ das report -db testdb -hosts all -oA report1
~$ das report -db testdb -hosts 192.168.1.0/24,10.10.13.37 -oA report1
~$ das report -db testdb -hosts hosts.txt -oA report1
# Merge outputs by ports
~$ das report -db testdb -ports all -oA report2
~$ das report -db testdb -ports 22,80,443,445 -oA report2
~$ das report -db testdb -ports ports.txt -oA report2
```

📑 **Note:** keep in mind that the `report` module does **not** search the DB when processing the `-hosts` or `-ports` options, but looks for Nmap raw reports directly in `.nmap` directory instead; it means that `-hosts 127.0.0.1` argument value will be successfully resolved only if `.nmap/127-0-0-1.*` file exists, and `-ports 80` argument value will be successfully resolved only if `.nmap/port80.*` file exists.

</td>
</tr>
</table>

## Help

```
usage: das [-h] {add,scan,report} ...

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
  {add,scan,report}
    add              run a full port scan {masscan,rustscan,naabu} and add the output to DB
    scan             run targeted Nmap scans against hosts and ports from DB
    report           merge separate Nmap outputs into a single report in different formats

optional arguments:
  -h, --help         show this help message and exit

Psst, hey buddy... Wanna do some organized p0r7 5c4nn1n6?
```

## ToDo

* [x] Add [projectdiscovery/naabu](https://github.com/projectdiscovery/naabu) parser
* [ ] Add armada scanner (?) parser

## Support

If this tool has been useful for you, feel free to buy me a <strike>beer</strike> coffee!

[![beer.png](https://user-images.githubusercontent.com/23141800/113611163-d03dd880-9656-11eb-9279-e5e2689b0c1b.png)](https://buymeacoff.ee/snovvcrash)
