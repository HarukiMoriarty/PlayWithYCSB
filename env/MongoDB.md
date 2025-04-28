# MongoDB Replica Set + YCSB Benchmark (Quick Reference)

## Cluster Setup
- Nodes: 128.105.145.227, .228, .229 allocated from CloudLab
- MongoDB 7.0, replica set name: `rs0`

### Install MongoDB on each node
```bash
# Add MongoDB 7.0 repo
$ wget -qO - https://pgp.mongodb.com/server-7.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg

$ echo "deb [ arch=amd64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

$ sudo apt update && sudo apt install -y mongodb-org

$ sudo systemctl enable --now mongod
```

### Edit `/etc/mongod.conf`
```yaml
net:
  bindIp: 0.0.0.0
replication:
  replSetName: rs0
```
```bash
$ sudo systemctl restart mongod
```

### Initialize Replica Set
```bash
$ mongosh "mongodb://128.105.145.227:27017/?replicaSet=rs0"
```

```js
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "128.105.145.227:27017" },
    { _id: 1, host: "128.105.145.228:27017" },
    { _id: 2, host: "128.105.145.229:27017" }
  ]
})
```

Notice the replica cluster need sometime to choose out a Primary node, you can check cluster status using

```js
rs.status()
```

## YCSB benchmark

### Setup
```bash
$ sudo apt install -y openjdk-17-jdk maven

$ git clone https://github.com/brianfrankcooper/YCSB.git && cd YCSB

$ mvn -pl site.ycsb:mongodb-binding -am clean package
```

### Run Workload A
```bash
$ export MONGODB_URL="mongodb://128.105.145.227,128.105.145.228,128.105.145.229/ycsbdb?replicaSet=rs0"

$ ./bin/ycsb load mongodb -s -P workloads/workloada -p mongodb.url="$MONGODB_URL" > outputLoad.txt

$ ./bin/ycsb run mongodb -s -P workloads/workloada -p mongodb.url="$MONGODB_URL" -threads 16 > outputRun.txt
```

### Display Results

```bash
$ python3 parser/mongodb_benchmark_parser.py --results_dir results/mongodb --output_dir charts/mongodb
```
