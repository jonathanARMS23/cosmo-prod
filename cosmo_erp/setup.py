from setuptools import setup, find_packages

setup(
    name="cosmo_erp",
    version="0.1.0",
    description="Custom ERPNext app for cosmetics retail boutique",
    author="ARMS",
    author_email="jonathan@overlord.fund",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.10",
)
