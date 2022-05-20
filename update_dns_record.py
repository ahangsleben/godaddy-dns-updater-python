import argparse
import configparser
import ipaddress

import requests


def parse_arguments():
    """
    Read in config file path from command line arguments.

    :returns: User input path to the config file.
    :rtype: string
    """

    parser = argparse.ArgumentParser(
        description="Updates a GoDaddy domain name DNS A-Record to the public IP address where this script was run."
    )
    parser.add_argument(
        "-c", "--config", help="Path to the config file.", default="config.ini"
    )

    arguments = parser.parse_args()
    return arguments.config


def read_config_file(config_file_path):
    """
    Reads in the config file that specifies the GoDaddy secrets and domain name to
    update.

    :param string config_file_path: Path to the config file.
    :returns: GoDaddy API key, API key secret, and domain name.
    :rtype: Tuple[string, string, string]
    """

    config = configparser.ConfigParser()
    config.read(config_file_path)
    if "godaddy" not in config:
        raise Exception("[godaddy] section not found in config file.")

    input_config = config["godaddy"]
    for field in ("api_key", "api_secret", "domain_name"):
        if field not in input_config:
            raise Exception(f"Required field {field} not found in config.")

    return (
        input_config["api_key"],
        input_config["api_secret"],
        input_config["domain_name"],
    )


def get_current_public_ip():
    """
    Determines the current public IP address of wherever this script is running.

    :returns: Public IP of the current computer.
    :rtype: string
    """

    url = "https://ifconfig.me/ip"

    response = requests.get(url)
    ip = response.text

    # Validate IP address. Raises a ValueError if the IP isn't valid.
    ipaddress.ip_address(ip)

    return ip


def update_godaddy_dns_entry(api_key, api_secret, domain_name, ip_address):
    """
    Updates a GoDaddy Domain Name A-Record with the given IP Address.

    :param string api_key: GoDaddy API key.
    :param string api_secret: GoDaddy API key secret.
    :param string domain_name: Domain name to update.
    :param string ip_address: IP address to set in A-Record.
    """

    url = f"https://api.godaddy.com/v1/domains/{domain_name}/records/A/@"

    headers = {
        "Authorization": f"sso-key {api_key}:{api_secret}",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    domain_record = response.json()

    current_godaddy_ip = domain_record[0]["data"]
    if current_godaddy_ip == ip_address:
        print("IP already up to date.")
        return

    domain_record[0]["data"] = ip_address

    response = requests.put(url, headers=headers, json=domain_record)
    if not response.ok:
        print("Failed to update IP.")

    print("Successfully updated IP.")


def main():
    """
    Updates the GoDaddy domain name with the current public IP address.
    """

    config_file_path = parse_arguments()
    api_key, api_secret, domain_name = read_config_file(config_file_path)
    public_ip = get_current_public_ip()

    update_godaddy_dns_entry(api_key, api_secret, domain_name, public_ip)


if __name__ == "__main__":
    main()
