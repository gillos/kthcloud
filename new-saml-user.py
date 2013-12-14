# -*- coding: utf-8 -*-
from requests import *
from requests.auth import HTTPBasicAuth
import json
import sys
from xml.dom.minidom import parseString
import getpass
import keyring
def getxml(u,token):
	return get(u,headers={'Accept':'application/*+xml;version=5.1','x-vcloud-authorization':token},verify=False).text

def getorgurl(name,token):
	xml=getxml('https://www.cloud.kth.se/api/admin/',token)
	l=[x.getAttribute('href') for x in parseString(xml).getElementsByTagName('OrganizationReference') if x.getAttribute('name')==name]
	if len(l)==1:
		return l[0]
	return None

def gettoken(loginurl,uname):
	while True:
		pw=keyring.get_password("www.cloud.kth.se", uname)
		if not pw or pw=='':
			pw=getpass.getpass()
			keyring.set_password("www.cloud.kth.se", uname, pw)
		r=post(u,auth=HTTPBasicAuth(uname,pw),headers={'Accept':'application/*+xml;version=5.1'},verify=False)
		if r.status_code==200:
			return r.headers['x-vcloud-authorization']	
		else:
			keyring.set_password("www.cloud.kth.se", uname, '')

if __name__ == '__main__':
	if len(sys.argv)<4:
		print "usage: %s <org> <new user> <admin user>" % sys.argv[0]
		sys.exit()
	v=get('https://www.cloud.kth.se/api/versions',verify=False).text
	for e in parseString(v).getElementsByTagName('VersionInfo'):
		ver=e.getElementsByTagName('Version')[0].childNodes[0].data
		if ver=='5.1':
			u=e.getElementsByTagName('LoginUrl')[0].childNodes[0].data
	vca=gettoken(u,sys.argv[3])
	o=getorgurl(sys.argv[1],vca)
	orgadminurl=[e.getAttribute('href') for e in parseString(getxml('https://www.cloud.kth.se/api/admin/',vca)).getElementsByTagName('RoleReference') if e.getAttribute('name')=='Organization Administrator'][0]
	xml="""<?xml version="1.0" encoding="UTF-8"?>
	<User xmlns="http://www.vmware.com/vcloud/v1.5" name="%s" type="application/vnd.vmware.admin.user+xml">
	   <IsEnabled>true</IsEnabled>
	   <ProviderType>SAML</ProviderType>
	   <Role type="application/vnd.vmware.admin.role+xml" href="%s" />
	</User>""" % (sys.argv[2],orgadminurl)
	r=post(o+'/users',headers={'Content-Type':'application/vnd.vmware.admin.user+xml','Accept':'application/*+xml;version=5.1','x-vcloud-authorization':vca},verify=False,data=xml)
	if r.status_code==201:
		print "success"
	else:
		print "failure"
