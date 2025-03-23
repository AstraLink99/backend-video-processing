
Ensure you have the following:

- **Docker Desktop** (for RabbitMQ server)
- **Python 3.8+** 
- **Node.js** 

## Set Up RabbitMQ using Docker

Run the following command to start a RabbitMQ container:

```sh
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
```

- **5672** → Port for RabbitMQ communication
- **15672** → Port for RabbitMQ web management UI

You can access the **RabbitMQ management UI** at: [http://localhost:15672](http://localhost:15672)  
(Default credentials: `guest` / `guest`)

##  Clone the Repository

```sh
git clone https://github.com/backend-video-processing.git
cd backend-video-processing
```

##  Set Up Python Virtual Environment

```sh
python -m venv myenv
source myenv/bin/activate  # On Windows, use `myenv\Scripts\activate`
```

##  Install Dependencies

```sh
pip install -r requirements.txt
```

##  Start Backend Services

This project requires **Four terminals** to run different services:

### Terminal 1: Start Metadata Service

```sh
cd backend
python workers/metadata.py
```

### Terminal 2: Start Enhancement Service

```sh
cd backend
python workers/enhancement.py
```

### Terminal 3: Start FastAPI Backend

```sh
cd backend
uvicorn main:app --reload
```

###  Terminal 4: Start Frontend

navigate to Frontend

```sh
cd frontend
npm install  
npm run dev  
```

##  Testing WebSocket Connection


    1. Open Postman.
    2. Select `WebSocket` request.
    3. Connect to: `ws://localhost:8000/ws/{client_id}`.


## Video Upload & Viewing Process
- **Uploading of videos** can be done via **Frontend** or **Swagger UI** (`http://localhost:8000/docs`).
- **Metadata and enhanced info** will be logged in the **terminal output** of the respective worker processes.



## Troubleshooting

- If RabbitMQ is not running, restart it using:
  
  ```sh
  docker start rabbitmq
  ```
- If you see enhanced info but not the metadata , click on the upload button again on the Frontend.
- Ensure all dependencies are installed correctly.
- make sure you are in the right directory and check if the venv is enabled or not and then try to fireup the servers.

## Known Issues

###  Metadata & Enhancement Info Not Displayed on Frontend
- Currently, the **metadata and enhanced video information** are **only visible in the terminal logs** of the respective worker processes.
- The **Frontend does not display** metadata via WebSockets, even though it should.
