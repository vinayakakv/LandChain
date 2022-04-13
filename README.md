# LandChain
A blockchain-based land record management system, done as a Major project in SJCE, Mysuru. 

Won the "Best project award" in 2019.

## Tech-Stack
- BigChainDB (https://www.bigchaindb.com/) for blockchain-based data storage.
- [Flask](https://flask.palletsprojects.com/en/2.0.x/) server.
- Docker and Docker-Compose for node emulation.
- MapBox for mapview.

## Quick Start
- Clone the repo and `cd` to the `docker` folder
- `docker-compose up`

## Services in `docker-compose.yml`
- BigChainDB -- The backend blockchain databse
- Government user -- The government user, runs at http://localhost:8000
- Surveyor -- The user who mesures the land, runs at http://localhost:8080
- User 1 -- Normal user who can buy and sell the land, runs at http://localhost:8088
- User 2 -- runs at http://localhot:8090

## Initialization
In the beging, all pages will show a signup prompt. Even if you sign-up there, we need approval of `Government` user.

![image](https://user-images.githubusercontent.com/24838519/163103449-3aa92af1-5f1d-42e3-bcc8-4dee96ee08b4.png)

First, we shall create the Government user.

1. Get the shell access to Government container -- `docker exec -it <container-name> -- sh`
2. `cd` to `app` folder, run `python3 __create_government_user.py` and note down the public key of the government
![image](https://user-images.githubusercontent.com/24838519/163103609-731e51b6-d668-453e-a5e3-990b12f1a6a1.png)
3. Stop the containers started using `docker-compose`, then terminate them fully with `docker-compose rm`.
4. Edit `.env` file in `docker` folder, replacing `GOVERNMENT_PUBKEY` with the value you noted down in step 4.
5.Start containers again, `docker-compose up`
6. You can now log in to the `localhost:8000` 
![image](https://user-images.githubusercontent.com/24838519/163103788-34fa57bb-23b9-4986-a224-adb34e83c075.png)

## Interfaces

### Government Interface
Government can
1. Approve new users into the blockchain (before that, user has to request signup)
![image](https://user-images.githubusercontent.com/24838519/163104249-c4a7942d-e382-4897-ba87-0f679d5c3b85.png)
2. Distribute land to the people (before that, land has to be surveyed)
![image](https://user-images.githubusercontent.com/24838519/163104459-14b142d3-0e86-441d-9351-91166e16ce63.png)
3. Settle land transfer requests (before that, user has to make a land transfer request)
![image](https://user-images.githubusercontent.com/24838519/163104719-f0e383fc-a8b2-46e2-94e4-d3211df28a02.png)

### Surveyor Interface
Surveyor can just survey the land
![image](https://user-images.githubusercontent.com/24838519/163104362-ba94462b-5f27-4bd6-a618-f34c781b78a0.png)


### User Interface
1. View their current holdings (First, they have to be given land by the government)
![image](https://user-images.githubusercontent.com/24838519/163104579-2d29b8a3-5405-45b0-b7f7-49c12fd6d039.png)
2. Transact the land with other users
![image](https://user-images.githubusercontent.com/24838519/163104637-ab7a6cca-8501-476c-999a-646db4d20761.png)

### Guest Interface
Guests can enter a survey number and view the land transfer history
![image](https://user-images.githubusercontent.com/24838519/163104838-e2ef0131-27a8-431e-89d3-2899ace94b3f.png)
