## Docker files
This directory contains a `Dockerfile` and `docker-compose.yml`

### Build Instructions

Pull the images 
	- `docker pull bigchaindb/bigchaindb:all-in-one`
	- `docker pull alpine`

Build custom image
	- `cd` to this directory
	- `docker build . -t cryptimage`
	- Modify `docker-compose.yml` as needed

### Run instructions

Run images
	- `docker-compose up -d`

Execute commands on running images
	- `docker exec -it <continer name> <command>`

Attach the output 
	- `docker attach <container name>`
