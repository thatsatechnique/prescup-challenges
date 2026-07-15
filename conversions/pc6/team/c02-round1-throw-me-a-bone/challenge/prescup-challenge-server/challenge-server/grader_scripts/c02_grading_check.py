#!/usr/bin/env python3

'''
This is the main script used by the Grading function on the Challenge Server
It calls the grading_system_check.py script to perform a check across the
hostnames listed.
'''

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grading_system_check

def main():
    host_list = ["app-server", "k3s-server", "cato", "virginia", "amicus", "cassius"]
    all_pass = True

    for host in host_list:
        results = grading_system_check.check_system(host)

        # Check top-level string results
        for key, value in results.items():
            if isinstance(value, dict):
                # Check nested dict values (users, homeDir)
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str) and "Fail" in sub_value:
                        all_pass = False
            elif isinstance(value, str) and "Fail" in value:
                all_pass = False

    if not all_pass:
        print("GradingCheck1 : Failure - One or more of the six (6) servers still have vulnerabilities present.")
    else:
        print("GradingCheck1 : Success - No outstanding vulnerabilities reported.")

if __name__=='__main__':
    main()
