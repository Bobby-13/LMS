
**Structure** 
      my_local_package/
      ├── setup.py
      └── mypackage/
          ├── __init__.py
          └── mymodule.py


**command to create Distributable file**
python3 setup.py sdist bdist_wheel


**command to install the custom packages**
pip install /path/to/mypackage-0.1.tar.gz
