# YCSB Benchmark on ZooKeeper Cluster

This document outlines the steps for setting up a ZooKeeper cluster and benchmarking it using YCSB. This is particularly useful for stress-testing ZooKeeper as a metadata coordination service.

---

## Environment Setup

### Machine Information
| Node | IP Address         | myid |
|------|--------------------|------|
| zk1  | 128.105.145.217    | 1    |
| zk2  | 128.105.145.213    | 2    |
| zk3  | 128.105.145.209    | 3    |

### Installation Steps (on all 3 machines)

1. **Download and Extract ZooKeeper 3.8.4**:
```bash
$ wget https://downloads.apache.org/zookeeper/zookeeper-3.8.4/apache-zookeeper-3.8.4-bin.tar.gz
$ tar -xvzf apache-zookeeper-3.8.4-bin.tar.gz
$ mv apache-zookeeper-3.8.4-bin zookeeper
$ cd zookeeper
```

2. **Create data directory and set `myid`:**
```bash
$ sudo mkdir -p /var/lib/zookeeper
# Set myid accordingly
$ echo "1" | sudo tee /var/lib/zookeeper/myid  # On zk1
$ echo "2" | sudo tee /var/lib/zookeeper/myid  # On zk2
$ echo "3" | sudo tee /var/lib/zookeeper/myid  # On zk3
```

3. **Configure `conf/zoo.cfg`:**
```ini
tickTime=2000
initLimit=10
syncLimit=5
dataDir=/var/lib/zookeeper
clientPort=2181

server.1=128.105.145.217:2888:3888
server.2=128.105.145.213:2888:3888
server.3=128.105.145.209:2888:3888
```

4. **Start ZooKeeper on each machine:**
```bash
$ sudo bin/zkServer.sh start
```

5. **Verify cluster status:**
```bash
$ bin/zkServer.sh status
```
One node should be the leader; others should be followers.

---

## Prepare ZooKeeper for Benchmark

1. **Log into the leader (e.g., `128.105.145.213`)**:
```bash
$ bin/zkCli.sh -server 127.0.0.1:2181
```

2. **Create namespace for YCSB**:
```bash
$ create /benchmark ""
```

---

## YCSB Setup (Local Machine)

1. **Clone and build YCSB with ZooKeeper binding:**
```bash
git clone https://github.com/brianfrankcooper/YCSB.git
cd YCSB
mvn -pl site.ycsb:zookeeper-binding -am clean package -DskipTests
```

2. **Load Data into ZooKeeper:**
```bash
./bin/ycsb load zookeeper -s -P workloads/workloadb \
  -p zookeeper.connectString=128.105.145.213:2181/benchmark \
  -p recordcount=10000 > outputLoad.txt
```

3. **Run Benchmark (Read-heavy):**
```bash
./bin/ycsb run zookeeper -s -P workloads/workloadb \
  -p zookeeper.connectString=128.105.145.213:2181/benchmark \
  -p operationcount=10000 \
  -p fieldlength=1000 \
  -p fieldcount=10
```

4. **Multi-node Mode (for read distribution):**
```bash
./bin/ycsb run zookeeper -threads 10 -P workloads/workloadb \
  -p zookeeper.connectString=128.105.145.213:2181,128.105.145.217:2181,128.105.145.209:2181/benchmark
```

---

## Cleanup After Benchmark

1. **Connect to ZooKeeper CLI:**
```bash
bin/zkCli.sh -server 128.105.145.213:2181
```

2. **Delete all benchmark znodes:**
```bash
deleteall /benchmark
```
