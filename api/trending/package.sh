
pip3.9 install --target ./package requests-aws4auth opensearch-py

cd package
zip -r ../deployment-trending.zip .

cd ..
zip deployment-trending.zip index.py
