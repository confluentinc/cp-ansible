
# Running

- Run site.yml to setup the whole infrastructure
- Check the tags to see what the instances need to be named as
- A copy of the public IP to DNS name mappings of all the servers will be downloaded to your working dir, this can be added to HOSTS for easy access
- Topics prefixed “r.” will be replicated

# Future Tasks
- C3 alert setup
- Set c3 cluster ids
- Set os hostnames
- Fix replication stream monitoring
 - Interceptors on connect
 - Process supervision and startup - docker? Initd?
- Parameterise version of confluent distributing
- Add other brokers as bootstraps everywhere in ansible loop, or use elb
- Ship all logs with kafka and replicate
- SSD for C3
- Optimise storage devices - incl EBS optimised
- Add correct rack awareness
- Use placement groups
- Separate kafka install, configure, restart
- Increase thread count?
- Lock down connect
- Tighten security groups
- Don’t run apps as root
- Install zkcli
- Use Java 9
- Extract CP version string
- Set offset retention 30 days
- Make images with packer for faster startup / deploy once configuration stabilised
- Security - optional?