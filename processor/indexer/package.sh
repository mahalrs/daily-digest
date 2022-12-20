
pip3.9 install --target ./package requests-aws4auth opensearch-py

cd package
zip -r ../deployment-indexer.zip .

cd ../src
zip ../deployment-indexer.zip index.py
