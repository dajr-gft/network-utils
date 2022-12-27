from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import time
import configparser

# Reading properties file
config = configparser.ConfigParser()
config.read('checkList.properties')

# Uncomment to use Application Default Credentials (ADC)
credentials = GoogleCredentials.get_application_default()

cloudresourcemanager = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
compute = discovery.build('compute', 'v1', credentials=credentials)
container = discovery.build('container', 'v1', credentials=credentials)


class Colors:
    HEADER = '\033[32m'#$95
    OKBLUE = '\033[90m'
    OKCYAN = '\033[90m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CheckList:

    def __init__(self):
        self.project_id = config.get("dev", "PROJECT_ID")
        self.project_number = config.get("dev", "PROJECT_NUMBER")
        self.nar_id = config.get("dev", "NAR_ID")
        self.region = config.get("dev", "REGION")
        self.ip = config.get("dev", "CIDR")
        self.errors_msg = []

    @staticmethod
    def format_status(status):
        if status == "OK":
            status = Colors.BOLD + Colors.OKGREEN + "OK" + Colors.ENDC
        else:
            status = Colors.BOLD + Colors.FAIL + "NOK" + Colors.ENDC

        return status

    def print_header(self):
        print(Colors.HEADER + 125 * "=")
        print(Colors.BOLD + Colors.HEADER + "CHECK LIST - OFFBOARDING")
        print(Colors.HEADER + 125 * "-" + Colors.ENDC)
        print(Colors.BOLD + "INPUTS" + Colors.ENDC)
        print(Colors.OKCYAN + 125 * "-")
        print(Colors.OKBLUE + Colors.BOLD + "PROJECT_ID:" + Colors.ENDC + self.project_id)
        print(Colors.OKBLUE + Colors.BOLD + "PROJECT_NUMBER:" + Colors.ENDC + self.project_number)
        print(Colors.OKBLUE + Colors.BOLD + "REGION:" + Colors.ENDC + self.region)
        print(Colors.OKBLUE + Colors.BOLD + "CIDR:" + Colors.ENDC + self.ip)
        print(Colors.OKCYAN + 125 * "-" + Colors.ENDC)

    @property
    def format_time(self):
        return "[" + time.strftime("%Y-%m-%d %H:%M:%S") + "] "

    def check_project_exists(self):
        """
        Confirm if the project id in the CNE ticket exists in GCP.
        """
        request = cloudresourcemanager.projects().list()
        response = request.execute()

        if any(self.project_id in project['name'] for project in response.get('projects', [])):
            status = self.format_status("OK")
        else:
            status = self.format_status("OK")
            self.errors_msg.append(
                Colors.WARNING + "Error: Project {} doesn't exist!" + Colors.ENDC.format(self.project_id))

        print(self.format_time + "Checking if the project {} exists {} [{}]".format(self.project_id, 42 * ".", status))

    def check_project_number(self):
        """
        Confirm if the project number in the CNE ticket exists in GCP.
        """

        request = cloudresourcemanager.projects().list()
        response = request.execute()

        if any(str(self.project_number) in project['projectNumber'] for project in response.get('projects', [])):
            status = self.format_status("OK")
        else:
            status = self.format_status("NOK")
            self.errors_msg.append(
                Colors.WARNING + "Error: Project number {} doesn't exist!".format(self.project_number))

        print(self.format_time + "Checking if the project number {} exists {} [{}]".format(self.project_number,
                                                                                           47 * ".", status))

    def check_firewall_rule_status(self):
        """
        Check if there are FW rules for the project and if them are enabled.
        """

        request = compute.firewalls().list(project=self.project_id)
        response = request.execute()

        if any(str(self.nar_id) in firewall['name'] and firewall['disabled'] for firewall in
               response.get('items', [])):
            status = self.format_status("OK")
        elif any(str(self.nar_id) in firewall['name'] for firewall in response.get('items', [])):
            status = self.format_status("OK")
        else:
            status = self.format_status("NOK")
            self.errors_msg.append(
                Colors.WARNING + "Error: There is(are) FW rules for the NAR ID {}!".format(self.nar_id))

        print(self.format_time + "Checking if the FW rules was deleted for the NAR ID: {} {} [{}]".format(self.nar_id,
                                                                                                          41 * ".",
                                                                                                          status))

    def check_reserved_ip(self):
        """
        Verify if there is reserved IP addressess in the project.
        """

        request = compute.addresses().list(project=self.project_id, region=self.region)
        response = request.execute()

        if any(self.ip in addresses['address'] for addresses in response.get('items', [])):
            status = self.format_status("NOK")
            self.errors_msg.append(
                Colors.WARNING + "Error: The IP {} is reserved address for the project {}!" + Colors.ENDC.format(
                    self.ip,
                    self.project_id))
        else:
            status = self.format_status("OK")

        print(self.format_time + "Checking if there is reserved IPs for the project: {} {} [{}]".format(
            self.project_id, 22 * ".", status))

    def check_cluster_in_use(self):
        """
        Check if there are applications running in the cluster.
        """

        request = container.projects().zones().clusters().list(projectId=self.project_id, zone="-")
        response = request.execute()

        if any(self.ip in cluster['clusterIpv4Cidr'] for cluster in response.get('clusters', [])):
            status = self.format_status("NOK")
            self.errors_msg.append("{}Error: The CIDR {} is in use in the project {}! {}".format(Colors.WARNING,
                                                                                                 self.ip,
                                                                                                 self.project_id,
                                                                                                 Colors.ENDC))
        else:
            status = self.format_status("OK")

        print("{}Checking if there containers is in use for the project: {} {} [{}]".format(self.format_time,
                                                                                            self.project_id,
                                                                                            17 * ".", status))

    def list_errors(self):
        if len(self.errors_msg):
            print(Colors.OKCYAN + 125 * "-" + Colors.ENDC)
            print(Colors.BOLD + Colors.FAIL + "List of errors:")
            [print("-" + error) for error in self.errors_msg]
            print(Colors.OKCYAN + 125 * "-" + Colors.ENDC)

    def off_boarding(self):
        self.print_header()
        self.check_project_exists()
        self.check_project_number()
        self.check_firewall_rule_status()
        self.check_reserved_ip()
        self.check_cluster_in_use()
        self.list_errors()

        print(self.format_time + "Finished!")
        print(
            Colors.HEADER + 125 * "=" + Colors.ENDC)


if __name__ == '__main__':
    CheckList().off_boarding()
