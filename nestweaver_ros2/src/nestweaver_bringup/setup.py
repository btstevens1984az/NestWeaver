from setuptools import setup
import os
from glob import glob

package_name = "nestweaver_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
        ("share/" + package_name + "/config", glob("config/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="NestWeaver Contributors",
    maintainer_email="community@nestweaver.dev",
    description="Launch files and configs to bring up the full NestWeaver stack",
    license="Apache-2.0",
    entry_points={"console_scripts": []},
)
