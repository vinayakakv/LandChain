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

	docker-compose up -d

Execute commands on running images

	docker exec -it <continer name> <command>

Attach the output 

	docker attach <container name>
	

### Note
~~`Dockerfile` has to be modified as importing `bigchaindb` is failing with the error. For solving these error, run `alpine` image with interactive shell, execute the commands as in the order specified in `Dockerfile`, run `pyhton3` and test importing `bigchaindb`. If anything is needed to be installed, modify it in `Dockerfile`~~ 

Fixed in 03ab92353a47e028b09394fc645a0924c5484441
