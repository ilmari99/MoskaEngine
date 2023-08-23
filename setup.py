from setuptools import setup, find_packages

requirements = [
    "numpy==1.24.3",
    "scikit-learn==1.2.2",
    "tensorflow==2.11",
]

# Read the README.md file
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='MoskaEngine',
    version='0.1.6',
    description='A card game engine for the card game Moska. Contains game engine, players, simulation tools, and human interface.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Ilmari Vahteristo',
    url="https://github.com/ilmari99/MoskaEngine",
    # Used libraries are in the requirements.txt file
    packages=find_packages(),
    # Include the model files, and the player config files
    package_data={
        'MoskaEngine': ['Models/*/*.tflite', 'Play/PlayerConfigs/*.json']
    },
    install_requires=requirements,
    # Require python 3.6 or higher, but not 3.11 or higher
    python_requires='>=3.6, <3.11',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

)



