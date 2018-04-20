#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import urllib,urllib2
import base64
import hmac
from hashlib import sha1
import time
import uuid
import json
import time

import calendar
import requests


#计算签名调用
def percent_encode(str):
    res = urllib.quote(str.decode(sys.stdin.encoding).encode('utf8'), '')
    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')
    return res

#根据自定义参数字典和秘钥，计算签名
def compute_signature(parameters, access_key_secret):
    sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])

    canonicalizedQueryString = ''
    for (k, v) in sortedParameters:
        canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)

    stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])

    h = hmac.new(access_key_secret + "&", stringToSign, sha1)
    signature = base64.encodestring(h.digest()).strip()
    return signature


def compose_url(user_params):
    #Python time strftime() 函数接收以时间元组，并返回以可读字符串表示的当地时间，格式由参数format决定。
    #Python time gmtime() 函数将一个时间戳转换为UTC时区（0时区）的struct_time，可选的参数sec表示从1970-1-1以来的秒数。
    # 其默认值为time.time()，函数返回time.struct_time类型的对象。（struct_time是在time模块中定义的表示时间的对象）。
    #print "time.gmtime() : %s" % time.gmtime()
    #time.gmtime() : time.struct_time(tm_year=2016, tm_mon=4, tm_mday=7, tm_hour=2, tm_min=55, tm_sec=45, tm_wday=3, tm_yday=98, tm_isdst=0)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    parameters = {
        'Format': 'JSON',
        'Version': '2014-11-11',
        'AccessKeyId': access_key_id,
        'SignatureVersion': '1.0',
        'SignatureMethod': 'HMAC-SHA1',
        'SignatureNonce': str(uuid.uuid1()),
        'TimeStamp': timestamp,
        }
#将用户输入的命令值存储在自定义的parameters字典中
    for key in user_params.keys():
        parameters[key] = user_params[key]
#生成签名
    signature = compute_signature(parameters, access_key_secret)
    #赋值到自定义参数中
    parameters['Signature'] = signature
    #拼接url字符串,urllib库里面有个urlencode函数，可以把key-value这样的键值对(字典)转换成我们想要的格式，返回的是a=1&b=2这样的字符串
    url = cdn_server_address + "/?" + urllib.urlencode(parameters)
    return url


def make_request(user_params, quiet=False):
    url = compose_url(user_params)
    return url

def geturl(stime,etime,domain):
    #######################cdn url

    user_params ={'Action': 'DescribeDomainBpsData',
                  'Interval': '86400',
                  'EndTime': etime,
                  'StartTime': stime,
                  'DomainName': domain
                  }
    return make_request(user_params)

#计算每月天数，有变数的只有2月份，在统计2月时已经是三月份了，所以跨年无影响
def monthdays(month):
    current_year=time.strftime("%Y",time.localtime())
    month=int(month)
    current_year=int(current_year)
    monthrange=calendar.monthrange(current_year,month)
    days=monthrange[1]
    return days

if __name__ == '__main__':

    """
    user_params is {'Action': 'DescribeDomainBpsData', 'Interval': '86400', 'EndTime': '2017-10-1T23:59Z', 'StartTime': '2017-10-1T00:00Z', 'DomainName': 'mp4.open.com.cn'}
    """
    access_key_id = 'xxxx'
    access_key_secret = 'xxxxx'
    cdn_server_address = 'https://cdn.aliyuncs.com'

    #######################get every months days


    days=monthdays(sys.argv[2])
    # days = monthdays(10)
    #######################domain list
    domain_list=[]
    #从文件中获取查询域名
    f=open('cdndomain.txt','rb')
    data=f.readlines()
    #大循环：取出每个域名单独查询
    for i in data:
        # print(i)
        # print (type(i))
        domain=i.decode('utf-8').strip('\n').strip(" ")
        # print(domain)
        current_year = time.strftime("%Y", time.localtime())
        month=sys.argv[2]
        # month=10
        #循环一个域名一个月每天的峰值带宽流量
        i=1
        s=0.0
        while i<=days:
            stime='{0}-{1}-{2}T00:00Z'.format(sys.argv[1],sys.argv[2],i)
            etime='{0}-{1}-{2}T23:59Z'.format(sys.argv[1],sys.argv[2],i)
            cdnurl=geturl(stime,etime,domain)
            req = requests.get(cdnurl)
            data = req.text
            data=json.loads(data)
            # print data
            try:
                s1=data['BpsDataPerInterval']['DataModule'][0]['Value']
            except IndexError :
                s1=0.0
            s = s + int(s1)
            i+=1
            # time.sleep(60)
        s=s/30000000.0
        print ("%s                                          %.2f")%(domain,s)






