from setuptools import find_namespace_packages, setup


setup(
    name="cli-anything-voicebox",
    version="0.1.0",
    description="CLI-Anything harness for the Voicebox local voice studio.",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click>=8.0"],
    entry_points={
        "console_scripts": [
            "cli-anything-voicebox=cli_anything.voicebox.voicebox_cli:main",
        ],
    },
    python_requires=">=3.10",
)
