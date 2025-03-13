import os
from pathlib import Path
from modules import DeployClass
from dotenv import load_dotenv


ROOT = Path(__file__).parent

PRODUCTION = False

if PRODUCTION:
    load_dotenv(ROOT / ".testing")
else:
    load_dotenv(ROOT / ".testing")

SETTINGS = {
    "username": os.getenv("USER"),
    "password": os.getenv("PASS"),
    "ip": os.getenv("IP"),
    "log": ROOT / "logging.json",
    "logging": True,
}


def main():
    aci = DeployClass(**SETTINGS)
    aci.template = ROOT / "examples/create_tenant.j2"
    aci.render()
    aci.deploy()


if __name__ == "__main__":
    main()
