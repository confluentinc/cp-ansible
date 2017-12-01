
# Running

- Run site.yml to setup the whole infrastructure
- Check the tags to see what the instances need to be named as
- A copy of the public IP to DNS name mappings of all the servers will be downloaded to your working dir, this can be added to HOSTS for easy access
- Topics prefixed “r.” will be replicated
- Assumes Terraform json inventory is copied into the working dir as `inventory.json`
  - See `https://github.com/astubbs/cp-cluster-multi-region-terraform/tree/master` for details

# Features
- Multi SASL secured connect replicator (different credentials for different clusters)
- SSL, SASL_SSL, SASL_PLAIN and PLAINTEXT all working (no Kerberos)
- Automated self signed certificate generation and installation (same cert for every server)
- Choose between sec protocols for clients
- Choose which sec you want broker to listen for except Kerberos 
- Both Clusters monitored by C3
- C3 monitoring of both clusters in central cluster
- SASL_PLAIN - Digest secured Zookeeper (that’s with replicator running against it too)
- TLS with self signed certificates
- Variable size instances
- Variable quantity of instances
- Locked down security groups
- Fully deployed in under 10 minutes
- Fast dynamic inventory lookup via the Terraform.py project
- Bootstrap the Ansible library onto a bastion host for faster performance if on a slow connection

# Missing Features
- ACL
- Kerberos
- Performance tuning
- Unique SSL certs per server
- C3 Alerts
- C3 HTTPS
- C3 LDAP integration
- Documentation

# Future Tasks
- C3 alert setup
- Set c3 cluster ids
- Set os hostnames
- Process supervision and startup - docker? Initd?
- Parameterise version of confluent distributing fully
- Add other brokers as bootstraps everywhere in ansible loop, or use elb
- Ship all logs with kafka and replicate
- Add correct rack awareness
- Use placement groups
- Increase thread count - tuning / performance
- Install zkcli
- Use Java 9
- Set offset retention 30 days
- Make images with packer for faster startup / deploy once configuration stabilised
- Make security type for connect and c3 configurable
- Make replication setups and directions configurable 
- Turn on inter broker security?
- Give servers their own TLS keys
  - Run key generate script if they don’t exist
- Add latency analysis to proof app
- Turn on HTTPS for C3
- Turn on simple login for C3
- Turn on ACL
- Set OS hostnames so they show at login prompts - easy
- Client metric monitoring
- Increase broker heap space (1GB?)
- Publish proof result to a topic
- C3 alert setup
- Set max connections on servers
- Different secure users in different regions?
- Configure min.insync.replicas for c3

