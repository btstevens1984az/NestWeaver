from setuptools import setup

package_name = "nestweaver_tidy_behaviors"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", []),
        ("share/" + package_name + "/config", []),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="NestWeaver Contributors",
    maintainer_email="community@nestweaver.dev",
    description="Tidy / fetch behavior trees and action helpers",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "tidy_behaviors_node = nestweaver_tidy_behaviors.tidy_behaviors_node:main",
        ],
    },
)
