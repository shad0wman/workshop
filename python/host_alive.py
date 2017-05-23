#!/usr/bin/python3

import argparse
import os
import re
import socket
import subprocess
from multiprocessing import Process, Queue

try:
    import netaddr
except ImportError:
    print('[-] You need to install the "netaddr" module.  Get it with "pip install netaddr".')
    sys.exit(0)

def get_ips_from_range(ipRange):
    if '/' in ipRange:
        try:
            cidrIPs = netaddr.IPNetwork(ipRange)
        except netaddr.core.AddrFormatError:
            print('[-] Invalid IP cidr specified: ' + ipRange)
            sys.exit(0)
        return cidrIPs
    elif '-' in ipRange:
        # build ending IP from range
        dashRange = ipRange
        startIP , endIP = dashRange.split('-')
        # convert to cidr notation
        try:
            cidrIPs = netaddr.iprange_to_cidrs(startIP,endIP)[0]
        except netaddr.core.AddrFormatError:
            print('[-] Invalid IP range specified: ' + ipRange)
            sys.exit(0)
        return cidrIPs
    else:
        print('Something went wrong. Check your input ' + ipRange + " caused an error")
        sys.exit(0)

def send_to_lookup(q, verbose, outfile, timeout, hosts):
    for ip in hosts:
        try:
            ip = str(ip)
            proc = Process(target=ping, args=(ip, verbose, outfile, q))
            proc.start()
            if outfile != False:
                line = q.get()
                if line != None:
                    outfile.write(line + '\n')
            proc.join(timeout)
            if proc.is_alive():
                print('[!] Lookup timeout exceeded for: ' + ip)
                proc.terminate()
                proc.join()
        except KeyboardInterrupt:
            print('\n[!] Kill signal detected, shutting down.')
            proc.terminate()
            proc.join()
            break
    return

def ping(ip, verbose, outfile, q):
    response = subprocess.call('ping -c 1 %s -q' % ip, shell=True,stdout=open('/dev/null', 'w'),stderr=subprocess.STDOUT)
    if response == 0:
        results = '[+] %s is up!' % ip
        return results
        if outfile != False:
            q.put(results)
    else:
        return ('[-] %s us UNREACHABLE]' % ip)

def main():
    #Set up arguments
    parser = argparse.ArgumentParser(description='DNS Enumerator')
    parser.add_argument('-r', '--range', help='IP range to check. i.e. 192.168.1.0/24 or 192.168.1.0-255', default=None)
    parser.add_argument('-H', '--host', help="single host lookup", default=None)
    parser.add_argument('-i', '--input', help='file to read ip addresses from')
    parser.add_argument('-o', '--output', help='file to write output')
    parser.add_argument('-t', '--timeout', help='time in seconds to wait for lookup to complete, default is 5.', default=5)
    parser.add_argument('-v', '--verbose', help='show verbose output', action='store_true')
    args = parser.parse_args()

    #Declaring Variables
    timeout = int(args.timeout)
    outfile = False
    infile = False
    host = False
    ipRange = False
    verbose = False
    q = Queue()


    # Conditional Variables
    if args.verbose:
        verbose = True
    if args.output:
        outfile = open(args.output, 'w')
    if args.input:
        infile = True
    if args.range:
        ipRange = args.range
    if args.host:
        host = args.host

    # Do things
    if ipRange:
        ip = get_ips_from_range(ipRange)
        send_to_lookup(q, verbose, outfile, timeout, ip)
    elif infile:
        with open (args.input, 'r') as f:
            for line in f:
                host = line.strip('\n')
#                if '-' in host or '/' in host:
#                    host = get_ips_from_range(host)
#                    send_to_lookup(q, verbose, outfile, timeout, host)
#                else:
                results = ping(host,verbose,outfile,q)
                print (results)
            f.close()
    elif host:
        results = ping(host,verbose,outfile,q)
        print (results)
    else:
        print("[-] You need to specify either a range, input file or a host to scan silly.")

    if outfile != False:
        outfile.close()
        print('[*] Results saved to: ' + args.output)


if __name__ == '__main__':
    main()
