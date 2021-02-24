import requests
import json

def addgroup(name):

    url = 'http://139.198.112.110:30880/kapis/iam.kubesphere.io/v1alpha2/workspaces/wx-demo/groups'

    headers = {
        'cookie': 'lang=zh; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidG9rZW5fdHlwZSI6ImFjY2Vzc190b2tlbiIsImV4cCI6MTYxMTU3MjQ2MSwiaWF0IjoxNjExNTY1MjYxLCJpc3MiOiJrdWJlc3BoZXJlIiwibmJmIjoxNjExNTY1MjYxfQ.cRwvtjAKvvPmKGa4smuaGZSPdZNdKSNILhQzB4wOBYM; expire=1611572471487; refreshToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwidG9rZW5fdHlwZSI6InJlZnJlc2hfdG9rZW4iLCJleHAiOjE2MTE1Nzk2NjEsImlhdCI6MTYxMTU2NTI2MSwiaXNzIjoia3ViZXNwaGVyZSIsIm5iZiI6MTYxMTU2NTI2MX0.f0xUzj4zh6gPaQdgNbnyha45JyVbsvxs2Qzs8qhB59U',
        'Content-Type': 'application/json'
    }

    data = {"apiVersion":"iam.kubesphere.io/v1alpha2","kind":"Group","metadata":{"annotations":{"kubesphere.io/workspace-role":"wx-demo-regular","kubesphere.io/project-roles":"[]","kubesphere.io/devops-roles":"[]","kubesphere.io/creator":"admin"},"labels":{"kubesphere.io/workspace":"wsp1","iam.kubesphere.io/group-parent":"root"},"generateName":name}}
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    print(r.json())


for i in range(20, 100):
    name = 'test1' + str(i)
    print(name)
    addgroup(name)