# Benchmarking Redis with YCSB

This guide walks through setting up a 3-node Redis deployment (1 master, 2 replicas) and benchmarking it using YCSB.

---

## Environment Setup

### Install Redis on All Nodes

On each node:
```bash
sudo apt update
sudo apt install redis-server -y
```

### Configure Redis Master
Edit `/etc/redis/redis.conf`:
```ini
bind 0.0.0.0
port 6379
protected-mode no
```

Start Redis:
```bash
$ sudo systemctl restart redis-server
```
### Configure Redis Replicas
Edit `/etc/redis/redis.conf`:
```ini
bind 0.0.0.0
port 6379
protected-mode no
replicaof <master ipv4 address> <master port>
```

## Verify Replication
On the master:
```bash
$ redis-cli -h <master address> info replication
```

Expected output:
```makefile
role:master
connected_slaves:2
...
```

On a replica:
```bash
redis-cli -h <slave address> info replication
```

Expected output:
```makefile
role:slave
master_host:<slave address>
master_link_status:up
```


## Run YCSB benchmark

### Install Java & Maven
Make sure Java and Maven are installed on the YCSB machine.

### Set Up YCSB
```bash
$ git clone https://github.com/brianfrankcooper/YCSB.git
$ cd YCSB
$ mvn -pl site.ycsb:redis-binding -am clean package
```

### Run Benchmark
Load data:
```bash
$ ./bin/ycsb load redis -s -P workloads/workloada \
  -p "redis.host=128.105.145.184" \
  -p "redis.port=6379" \
  > outputLoad.txt
```

Run Workload
```bash
$ ./bin/ycsb run redis -s -P workloads/workloada \
  -p "redis.host=128.105.145.184" \
  -p "redis.port=6379" \
  > outputRun.txt
```