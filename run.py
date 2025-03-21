import os
from pathlib import Path
from devaci_module import DeployClass
from dotenv import load_dotenv


ROOT = Path(__file__).parent

load_dotenv(ROOT / ".env")

SETTINGS = {
    "username": os.getenv("USER"),
    "password": os.getenv("PASS"),
    "ip": os.getenv("IP"),
    "log": ROOT / "logging.json",
    "logging": True,
}


if __name__ == "__main__":
    aci = DeployClass(**SETTINGS)
    aci.template = [
        ROOT / "testing/shutdown_interfaces.j2",
    ]
    aci.check()
    #aci.deploy()
