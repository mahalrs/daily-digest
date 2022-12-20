
pip3.9 install --target ./package bs4

cd package
zip -r ../deployment-processor.zip .

cd ../src
zip ../deployment-processor.zip index.py
