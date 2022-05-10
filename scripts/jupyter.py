import os

# env={"ServerApp.token": "asd123456"}
env = os.environ
env.update({"JUPYTER_TOKEN": "asd12345"})
jupyter_addr = "0.0.0.0"
jupyter_port = "9995"
jupyter_base_url = "/test"


run()
