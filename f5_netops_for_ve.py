#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: Li Long - Holyzone SE Team
# Date: 2018/3/14
import os
import sys
import traceback
import base64
import urllib
import urllib2
from suds.client import Client
import bigsuds
import pexpect
##############################################################
###
###license_key request list type ,bigip_host request str type
###               Set var request you modify
###
###############################################################
playbook = "go_ve.yaml"
eula_string = ""
server_hostname = "activate.f5.com"
bigip_a = '192.168.0.181'
bigip_b = '192.168.0.180'
bigip_a_key = ['UBNAO-KXSHO-QBARO-XBANZ-KXPVLYI']
bigip_b_key = ['WVHBO-IURVP-YGWXE-IVAXH-EXEDWFX']
##############################################################
###
###defined  function
###
###############################################################
def get_license_from_F5_License_Server(server_hostname, dossier_string, eula_string, email,
                                       firstName, lastName, companyName, phone, jobTitle,
                                       address, city, stateProvince, postalCode, country):
    try:

        license_string = ""
        # Unfortunately, F5 wsdl on license server references http but F5 only accepts https so as an ugly workaround need to
        # download wsdl, save to disk, replace links http with https, and have SUDS client reference local file instead
        # (eg. url = "file:///home/admin/f5wsdl.xml")

        download_url = "https://" + server_hostname + "/license/services/urn:com.f5.license.v5b.ActivationService?wsdl"
        #print "From this site down WSDL: " + download_url
        # Check to see if there's a copy of wsdl file on disk first
        # Careful with this behavior if you switch server hostnames.
        local_wsdl_file_name = str(server_hostname) + '-f5wsdl-w-https.xml'
        wsdl_data = []

        try:
            with open(local_wsdl_file_name, 'r') as fh_wsdl:
                wsdl_data = fh_wsdl.read()
        except:
            print "Can't find a locally stored WSDL file."

        if not wsdl_data:
            print "Attempting to fetch wsdl online."
            f5wsdl = urllib2.urlopen(download_url)
            newlines = []
            for line in f5wsdl:
                # do the replacing here
                newlines.append(line.replace('http://' + server_hostname, 'https://' + server_hostname))

            fh_local = open(local_wsdl_file_name, 'w')
            fh_local.writelines(newlines)
            fh_local.close()

        # put url going to pass to client in file format
        url = "file:" + urllib.pathname2url(os.getcwd()) + "/" + local_wsdl_file_name

        # Now create client object using wsdl from disk instead of the interwebs.
        client = Client(url)

        transaction = client.factory.create('ns0:LicenseTransaction')
        # If eula isn't present on first call to getLicense, transaction will fail
        # but it will return a eula after first attempt
        transaction = client.service.getLicense(
            dossier=dossier_string,
            eula=eula_string,
            email=email,
            firstName=firstName,
            lastName=lastName,
            companyName=companyName,
            phone=phone,
            jobTitle=jobTitle,
            address=address,
            city=city,
            stateProvince=stateProvince,
            postalCode=postalCode,
            country=country,
        )

        # Extract the eula offered from first try
        eula_string = transaction.eula

        if transaction.state == "EULA_REQUIRED":
            # Try again, this time with eula populated
            transaction = client.service.getLicense(
                dossier=dossier_string,
                eula=eula_string,
                email=email,
                firstName=firstName,
                lastName=lastName,
                companyName=companyName,
                phone=phone,
                jobTitle=jobTitle,
                address=address,
                city=city,
                stateProvince=stateProvince,
                postalCode=postalCode,
                country=country,
            )

        if transaction.state == "LICENSE_RETURNED":
            license_string = transaction.license
        else:
            print "Can't retrieve license from Licensing server"
            print "License server returned error: Number:" + str(transaction.fault.faultNumber) + " Text: " + str(
                transaction.fault.faultText)

        return license_string

    except:
        print "Can't retrieve License from Server"
        traceback.print_exc(file=sys.stdout)

def get_dossier(obj,reg_keys):
    try:

        dossier_string = obj.Management.LicenseAdministration.get_system_dossier(reg_keys)
        return dossier_string

    except:
        print "Get Dossier error. Check log."
        traceback.print_exc(file=sys.stdout)

# def get_reg_keys(obj):
#     try:
#
#         reg_keys = []
#         reg_keys = obj.Management.LicenseAdministration.get_registration_keys()
#         return reg_keys
#
#     except:
#         print "Get Reg Keys from device error. Check log."
#         traceback.print_exc(file=sys.stdout)

def install_license(obj, license_string):
    try:

        license_char_array = base64.b64encode(license_string)
        obj.Management.LicenseAdministration.install_license(license_file_data=license_char_array)

    except:
        print "Install License error. Check log."
        traceback.print_exc(file=sys.stdout)

def get_license_status(obj):
    try:

        license_status = obj.Management.LicenseAdministration.get_license_activation_status()
        return license_status

    except:
        print "Get License Status error. Check log."
        traceback.print_exc(file=sys.stdout)

# def upload_iso(bigip_ip,iso,hotfix):
#     try:
#         for i in iso,hotfix:
#             spawn_arg = "rsync -avz --progress --rsh=ssh /etc/ansible/roles/upgrade/files/" + i + " root@" \
#                         + bigip_ip + ":/shared/images"
#             process = pexpect.spawn(spawn_arg, timeout=600)
#             process.logfile = sys.stdout
#             print '#'*100
#             print 'Execute rsync and auto input password.'
#             process.expect('Password:')
#             process.sendline('default')
#             print '#'*100
#             print 'Start copy the %s to BIG-IP %s' % (i,bigip_ip)
#             process.expect(pexpect.EOF)
#             print 'Copy the %s to BIG-IP %s has been completed' % (i,bigip_ip)
#     except:
#         print 'Not copy  %s to %s, please check your configuration' % (i,bigip_ip)

def all_in_fun(bigip_host,license_keys):
    b = bigsuds.BIGIP(
            hostname=bigip_host,
            username='admin',
            password='admin',
        )
    # Auto get Reg_key from device if license_keys is empty
    if len(license_keys) < 1:
        print"#"*15 + "Pls input your Reg-KEY at python script"
        # print "Reg Key list is empty, attempting to retrieve existing keys from the unit"
        # get_reg_key_value = get_reg_keys(b)
        # print "Python from bigip /config/RegKey.license get key value is : " + get_reg_key_value[0]
        # license_keys = get_reg_key_value[0]

    if license_keys :
        # Get dosser used Reg_key by Pre setting
        print "Getting dossier using You SET VARS'S keys:" + str(license_keys)
        dossier_string = get_dossier(b, license_keys)
        print "dossier = " + str(dossier_string)

        license_string = get_license_from_F5_License_Server(
            server_hostname,
            dossier_string,
            eula_string,
            email='se@holyzone.com.cn',
            firstName='SE',
            lastName='SE',
            companyName='Holyzone beijing',
            phone='18001161000',
            jobTitle='SE',
            address='beijing',
            city='beijing',
            stateProvince='beijing',
            postalCode='100000',
            country='china'
        )
        print license_string
        # Install the license
        if license_string:
            print "License Found. Attempting to installing License on BIGIP:"
            install_license(b, license_string)
        else:
            print "Sorry. Could not retrieve License. Check your connection"
        # View license status
        license_status = get_license_status(b)
        print "License status = " + str(license_status)

##############################################################
###
###Start my script
###
###############################################################

if __name__ == "__main__":
    print '#'*100
    print 'Start Activate  ' + bigip_a + '  License'
    print '#'*100
    all_in_fun(bigip_host=bigip_a,license_keys=bigip_a_key)
    print '#'*100
    print 'Start Activate  ' + bigip_b + '  License'
    print '#'*100
    all_in_fun(bigip_host=bigip_b, license_keys=bigip_b_key)
    print '#' * 100
    print 'Start Exec Ansible Playbook :' + playbook
    print '#' * 100
    command_ansible = 'ansible-playbook %s' % (playbook)
    os.system(command_ansible)
