
pip3.9 install --target ./package requests-aws4auth opensearch-py

cd package
zip -r ../deployment-recommend.zip .

cd ..
zip deployment-recommend.zip index.py
