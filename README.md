# f5_netops_ve
通过python脚本调用ansible进行自动化部署F5 VE集群。 
===============================================

环境：
-----------------------------------------------
> ansible 2.4 

> python 2.7

> F5 VE TMOS v12

操作方法：
-----------------------------------------------


>（1）修改f5_netops_for_ve.py中的变量，如被管理F5 VE地址，VE license base key。

>（2）保证你的python 2 环境有如下module：

import os

import sys

import traceback

import base64

import urllib

import urllib2

from suds.client import Client

import bigsuds

>（3）修改ansible host 文件对两台设备的变量根据实际情况进行修改

>（4）修改roles-local_traffic-templates-test_loop.j2文件，设置loop的vs端口ip地址

>（5） python f5_netops_for_ve.py

5分钟后2台F5 VE License 激活，网络层，应用层，DSC双机集群部署完毕。
===============================================
