(
    sam validate --profile dev
) && (
    sam build --profile dev --use-container -b .artifacts
) && (
    sam package --s3-bucket algernonsolutions-layer-dev --template-file .artifacts\template.yaml --profile dev --output-template-file .artifacts\templated.yaml
) && (
aws cloudformation deploy --profile dev --template .artifacts\templated.yaml --stack-name auditor-dev --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND ^
--parameter-overrides ^
OysterBedEndpoint=mh5syterirdvzji7tdbrrmpe7m.appsync-api.us-east-1.amazonaws.com ^
LambdaRoleArn=arn:aws:iam::726075243133:role/worker-leech-dev-2-Oyster-168YECYUUDQMK ^
GraphGqlEndpoint=jlgmowxwofe33pdekndakyzx4i.appsync-api.us-east-1.amazonaws.com ^
IsDev=False ^
--force-upload
)