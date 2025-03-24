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
    "testing": True,
    "logging": True,
    "render_to_xml": True,
    "log": ROOT / "logging.json",
}


if __name__ == "__main__":
    aci = DeployClass(**SETTINGS)
    aci.template = [
        ROOT / "testing/create_tenant1.j2",
        ROOT / "testing/create_tenant2.j2",
    ]
    aci.deploy()
    aci.show_output()
