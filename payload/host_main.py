import os

import uvicorn

from host_broker.broker import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("HOST_BROKER_PORT", "8877")), log_level="warning")
