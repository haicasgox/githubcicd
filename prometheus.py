import boto3
import json
import sys
import ruamel.yaml
import requests
import time

def lambda_handler(event, context):
  yaml = ruamel.yaml.YAML()
# Tạo S3_Client
  s3 = boto3.client('s3')
# Get file txtTarget.txt từ S3: s3://khoi--grafana/txtTarget.txt
  dictAllCus = s3.get_object(Bucket = 'khoi--grafana', Key = 'txtTarget.txt')
# Đọc Data trong Body_dictAllCus và Convert String_to_List bằng split()
  lstAllCus = dictAllCus['Body'].read().decode('utf-8').split()
  
# Tạo List chứa Index_CustomLabel lấy từ lstAllCus
# Tách lstAllCus thành nhiều List, mỗi List dành cho một Customer và chứa CustomerLabel & CustomerTarget
  lstIdxCus = [idx for idx, val in enumerate(lstAllCus) if val.isupper() is True]
  sizeAllCus = len(lstAllCus)
  lstIdxCus_1 = (lstIdxCus + [sizeAllCus])[1: sizeAllCus]
  lstCus = [lstAllCus[i: j] for i, j in zip(lstIdxCus, lstIdxCus_1)]            # List tổng mà mỗi phần tử là một List con chứa Data của 1 Customer
  
############################################# Chuyển Data từ file "txtTarget.txt" vào Table_DynamoDB ###############################################

# Truy cập vào Table_DynamoDB: "PromTarget"
  dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('PromTarget')
# Vòng lặp duyệt toàn bộ phần tử của lstCus:
  # Tại mỗi phần tử sẽ Parse Data thành dạng Dictionary với 2 Key là: Customer & Target (Giống với Key của Table_DynamoDB)
  lstUrlCus = []
  for idxDataCus in lstCus:
    idx = 1
    while idx < len(idxDataCus):
      if idxDataCus[idx].startswith("http") is True:
        table.put_item(Item={"Customer": idxDataCus[0], "Target": idxDataCus[idx]})
      idx = idx + 1

############################################# Tạo file "helmUpgradeTarget.yaml" từ file Data_Table_DynamoDB ########################################

# Truy cập Table_DynamoDB: "PromTarget" và Get toàn bộ Items:
  allItem = table.scan()["Items"]
# Chuyển Item lấy dc sang dạng Yaml
  lstItemKey = [idxItemKey["Customer"] for idxItemKey in allItem]
  setItemKey = set(lstItemKey)

  lstCustomer = []
  allCustomer = []
  for idxItemKey in setItemKey:
    lstCustomer.append(idxItemKey)
    for idxCus in allItem:
      if idxCus["Customer"] == idxItemKey:
        lstCustomer.append(idxCus["Target"])
    allCustomer.append(lstCustomer)
    lstCustomer = []
  
  dataCus = []
  for idxCus in allCustomer:
    rawData = [{'targets':idxCus[1:len(idxCus)], 'labels':{'customer':idxCus[0]}}]
    dataCus.extend(rawData)
  
# Tạo file helmUpgradeTarget.yaml:
  params = yaml.load('[' + 'http_2xx' + ']')
  srcLabel = yaml.load('[' + '_address_' + ']')
  tarLabel = yaml.load('[' + '__param_target' + ']')
  raw = [{'source_labels': srcLabel, 'target_label': '__param_target'},
         {'source_labels': tarLabel, 'target_label': 'instance'},
         {'target_label': '_address_', 'replacement': 'prometheus-blackbox-exporter:9115'}]
  file = [{'job_name': 'prometheus-blackbox-exporter',
           'metrics_path': '/probe',
           'params':{'module': params},
           'static_configs': dataCus,
           'relabel_configs': raw}]
  # print(yaml.dump(file, sys.stdout))

# Upload helmUpgradeTarget.yaml lên S3: s3://khoi--grafana/helmUpgradeTarget.yaml
  with open(r'/tmp/helmUpgrade.yaml', 'w') as fd:
    yaml.dump(file, fd)
  with open('/tmp/helmUpgrade.yaml', 'rb') as fd:
    s3.upload_fileobj(fd, 'khoi--grafana', 'helmUpgradeTarget.yaml')

#############################################  GrafanaAutomateDashboard ############################################################################
    
  # # time.sleep(2)
  # # POST Request
  # # Automate Create Grafana Dashboard
  # postApi = "https://grafana.khoieks.tk/api/dashboards/db"
  # postHeaders = {
  #   "Content-Type": "application/json",
  #   "Authorization": 'Bearer eyJrIjoiODY4ZDFjUTNQOE5TeWhkNDdSN2U3dk9kZHVQWjZIRFoiLCJuIjoiQVBJS2V5IiwiaWQiOjF9'
  # }

  # # postData = event['body']        # Get Data from Configure test event
  # # s3://khoi--grafana/grafanaDashboard.json
  # s3.download_file(Bucket='khoi--grafana', Key='grafanaDashboard.json', Filename='/tmp/grafanaDashboard.json')
  # jsonRead = open('/tmp/grafanaDashboard.json',)
  # dictData = json.load(jsonRead)
    
  # str_postData = json.dumps(dictData)    # Convert Dictionary to String
  # label = "CusLabel"
  # for objData in setItemKey:
  #     str_postData = str_postData.replace(label, objData)
  #     postResponse = requests.post(postApi, data=str_postData, headers=postHeaders)
  #     label = objData