from cpapi import APIClient, APIClientArgs
import json
import requests
import socket
import sys
sys.path.insert(0, '/usr/local/lib/python3.12/site-packages') #путь к каталогу, где лежит dns.resolver
import dns.resolver
import csv

class CSVWriter:
    def __init__(self, filename):
        self.filename = filename
        try:
            self.file = open(filename, 'a', newline='')
            self.writer = csv.writer(self.file)
        except FileNotFoundError:
            self.file = open(filename, 'w', newline='')
            self.writer = csv.writer(self.file)
            self.writer.writerow(['Имя от Чекпоинта', 'IP-адрес от Чекпоинта', 'IP-адрес от DNS', 'Статус проверки'])

    def write_row(self, row1, row2, row3, row4):
        self.writer.writerow([row1, row2, row3, row4])

    def close(self):
        self.file.close()

def dns_checker(name, address_from_cp):
    #address_from_dns = ''
    #if not name.endswith('.kozh.lc'): #указать DNS-суффикс
    #    name += '.kozh.lc' #указать DNS-суффикс
    try:
        record = dns.resolver.resolve(name, 'A')
        print ('Данная запись найдена на DNS-сервере!', name)
        for rdata in record:
            address_from_dns = str(rdata)
            if address_from_dns == address_from_cp:
                print ('IP-адрес совпадает.')
                status = 'IP-адрес совпадает.'
                return True, address_from_dns, status
            else:
                print ('IP-адрес не совпадает.', 'Корректный адрес:', address_from_cp)
                status = 'IP-адрес не совпадает.'
                return False, address_from_dns, status
    except dns.resolver.NoAnswer:
        status = 'Нет ответа от DNS-сервера!'
        return False, address_from_dns, status
    except dns.resolver.NXDOMAIN:  
        status = 'Запись не найдена!'
        return False, address_from_dns, status

def create_csv(filename, data):
    with open(filename, "a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data.keys())
        writer.writerow(data.values())      

name = ''
address = ''

client_args = APIClientArgs()
client_args = APIClientArgs(server='ip address') #адрес чекпоинта
with APIClient(client_args) as client: 
    client = APIClient(client_args)
    if client.check_fingerprint() is False:
        print ('Fingerprint failed!')
        exit(1)
    else:
        login = client.login('login', 'password') #креды для подключения к чекпоинту
        show_hosts = client.api_query('show-hosts')
        show_hosts = show_hosts.response()
    for item in show_hosts['data']:
        for key, value in item.items():
            if key == 'name':
                name = value
            elif key == 'ipv4-address':
                address = value
        converted_name = name.lower()
        print('Запись полученная от Чекпоинта:', converted_name, '-', address)
        result = dns_checker(name, address)
        print('----------')
        csv_name_from_cp = name
        csv_ip_from_cp = address
        if result[0] == True:
            csv_record_status = 'Совпадает'
            csv_ip_from_dns = result[1]
            csv_writer = CSVWriter('output.csv')
            csv_writer.write_row(csv_name_from_cp, csv_ip_from_cp, csv_ip_from_dns, csv_record_status)
            csv_writer.close()
        elif result[2] == 'Запись не найдена!' and result[0] == False:
            csv_record_status = 'Запись не найдена!'
            csv_writer = CSVWriter('output.csv')
            csv_writer.write_row(csv_name_from_cp, csv_ip_from_cp, csv_record_status, csv_record_status)
            csv_writer.close()
        elif result[0] == False:
            csv_record_status = 'Не совпадает'
            csv_ip_from_dns = result[1]
            csv_writer = CSVWriter('output.csv')
            csv_writer.write_row(csv_name_from_cp, csv_ip_from_cp, csv_ip_from_dns, csv_record_status)
            csv_writer.close()
        elif result[2] == 'Запись не найдена!' and result[0] == False:
            print (result[2])

    
