import setuptools

with open("PACKAGE_README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='fairiskdata',
    version='1.0',
    author="Catarina Pires, Diana Gomes, David Ribeiro, Duarte Folgado, Ricardo Santos, Telmo Barbosa",
    author_email="catarina.pires@fraunhofer.pt, diana.gomes@fraunhofer.pt, david.ribeiro@fraunhofer.pt, duarte.folgado@fraunhofer.pt, ricardo.santos@fraunhofer.pt, telmo.barbosa@fraunhofer.pt",
    description="This package facilitates fetching and handling data related to COVID and estimation of related excess mortality",
    url="https://github.com/fraunhoferportugal/fairisk",
	license="Creative Commons BY-NC-SA 4.0",
	python_requires=">=3.7",
	long_description=long_description,
	long_description_content_type="text/markdown",
	packages=setuptools.find_packages(),
    install_requires=[
        "country-converter==0.7.2",
        "mergedeep==1.3.4",
        "simplejson==3.17.2",
        "pyjstat==2.2.0",
        "requests-futures==1.0.0",
        "hdx-python-api==4.9.5"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
 )