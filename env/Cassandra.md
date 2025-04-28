# Cassandra 3-Node Cluster Setup with YCSB Benchmark

## Environment Setting
- 3 machines (e.g., CloudLab nodes):
  - Node 0: `128.105.144.87`
  - Node 1: `128.105.144.78`
  - Node 2: `128.105.144.101`


### Install Java 11
```bash
$ sudo apt update && sudo apt upgrade
$ sudo apt install openjdk-11-jdk
$ java -version
```
If Java 17 is installed and Cassandra fails with GC error, switch to Java 11:
```bash
$ sudo update-alternatives --config java
```


### Download and Install Apache Cassandra
```bash
# Add Cassandra GPG key
$ curl https://downloads.apache.org/cassandra/KEYS | sudo gpg --dearmor -o /usr/share/keyrings/cassandra.gpg

# Add APT repo
$ echo "deb [signed-by=/usr/share/keyrings/cassandra.gpg] https://apache.jfrog.io/artifactory/cassandra-deb 41x main" | \
  sudo tee /etc/apt/sources.list.d/cassandra.list

# Install
$ sudo apt update
$ sudo apt install cassandra -y
```


### Configure Cassandra
Edit `/etc/cassandra/cassandra.yaml`:
```yaml
seed_provider:
  - class_name: org.apache.cassandra.locator.SimpleSeedProvider
    parameters:
      - seeds: "128.105.144.87,128.105.144.78,128.105.144.101"

endpoint_snitch: GossipingPropertyFileSnitch
rpc_address: 0.0.0.0
start_native_transport: true

listen_address: <THIS_NODE_IP>
broadcast_address: <THIS_NODE_IP>
broadcast_rpc_address: <THIS_NODE_IP>
```

Edit `/etc/cassandra/cassandra-rackdc.properties`:
```bash
dc=datacenter1
rack=rack1
```


### Start Cassandra
```bash
$ sudo systemctl enable --now cassandra
```

Verify cluster:
```bash
$ nodetool status
```

To check logs:
```bash
$ tail -n 50 /var/log/cassandra/system.log
```


### Install CQLSH (This step can be done on local machine)
```bash
sudo snap install cqlsh
```


### Create YCSB Keyspace and Table
```bash
cqlsh 128.105.144.87 9042

CREATE KEYSPACE ycsb WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 3};
USE ycsb;

CREATE TABLE usertable (
  y_id varchar PRIMARY KEY,
  field0 varchar,
  field1 varchar,
  field2 varchar,
  field3 varchar,
  field4 varchar,
  field5 varchar,
  field6 varchar,
  field7 varchar,
  field8 varchar,
  field9 varchar
);
```

---

## Running YCSB benchmark
```bash
git clone https://github.com/brianfrankcooper/YCSB.git
cd YCSB
mvn -pl site.ycsb:cassandra2 -am clean package -DskipTests
```

```bash
./bin/ycsb load cassandra2-cql -s -P workloads/workloada \
  -p hosts=128.105.144.87,128.105.144.78,128.105.144.101 \
  -p cassandra.keyspace=ycsb > outputLoad.txt

./bin/ycsb run cassandra2-cql -s -P workloads/workloada \
  -p hosts=128.105.144.87,128.105.144.78,128.105.144.101 \
  -p cassandra.keyspace=ycsb > outputRun.txt
```

---

## Parser

```bash
python parser/cassandra_benchmark_parser.py --results-dir results/cassandra2 --output-dir charts/cassandra
```