from __future__ import annotations

import re
import sys
import time
from typing import Dict

import logging
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")


class CustomFormatter(logging.Formatter):
    """
    Error formatting for proper displaying messages
    """
    grey = "\x1b[32;1m"
    yellow = "\x1b[33;1m"
    red = "\x1b[31;1m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class TenableAgents:

    def __init__(self):
        self.config = config
        self.headers = {
            "accept": "application/json",
            "X-ApiKeys": f"accessKey={self.config.get('access')};"
                         f"secretKey={self.config.get('secret')}"
        }
        self.url = self.config.get('url')
        self.agent_groups: list[Dict] = []
        self.networks: list[Dict] = []
        self.logger = logging.getLogger("Agent Group to Network")
        self.logger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(CustomFormatter())

        self.logger.addHandler(console)

    def main(self):
        self.__getAgentGroupsFromScanner()
        self.__getNetworksList()
        self.__linkGroups()

    def __getAgentGroupsFromScanner(self) -> None | int:
        """
        Function to get the all agent groups
        :return:
        """
        try:
            url = self.url + 'scanners/1/agent-groups'
            res = requests.get(url, headers=self.headers)
            if res.status_code == 200:
                self.agent_groups = res.json()['groups']
            self.logger.info(f"Found {len(self.agent_groups)} total unique groups!")
        except Exception as e:
            return self.errorLog(e)

    def __getNetworksList(self) -> None | int:
        """
        Function to get the all network lists
        :return:
        """
        try:
            url = self.url + f'networks'
            res = requests.get(url, headers=self.headers)
            if res.status_code == 200:
                self.networks = res.json()["networks"]
            self.logger.info(f"Found {len(self.networks)} total networks!")
        except Exception as e:
            return self.errorLog(e)

    def __linkGroups(self) -> None | int:
        """
        Function to link matched agent group to network
        :return:
        """
        try:
            found = False
            for agent_group in self.agent_groups:
                agent_group_name = agent_group['name']
                for network in self.networks:
                    network_name = network['name']
                    if re.search(r"\b" + agent_group_name + r"\b", network_name):
                        self.logger.info(
                            f"Found network for group name: {agent_group_name}, network name: {network_name}")
                        payload = {'network_uuid': network['uuid']}

                        # get the id list of agents
                        items = self.__getAgents(agent_group.get('id'), agent_group.get('name'))

                        if len(items) > 0:
                            payload['items'] = items
                            found = True
                            url = self.url + "scanners/null/agents/_bulk/addToNetwork"
                            res = requests.post(url, json=payload, headers=self.headers)
                            if res.status_code == 200:
                                self.logger.info(f"Linked agent group: {agent_group_name} to network: {network_name}")
                            else:
                                self.logger.warning(f"Unable to link agent group: {agent_group_name} "
                                                    f"to network: {network_name}")
                            break
                if not found:
                    self.logger.warning(f"Not found network for group name: {agent_group_name}")
                else:
                    found = False
        except Exception as e:
            return self.errorLog(e)

    def __getAgents(self, group_id: int, group_name: str) -> list[int] | int:
        """
        Function to get the agent ids of a agent group
        :param group_id: agent group id
        :param group_name: agent group name
        :return: list of agent ids
        """
        try:
            url = self.url + f"scanners/1/agent-groups/{group_id}/agents?limit=5000"
            res = requests.get(url, headers=self.headers)
            total = res.json()['pagination']['total']
            agents = res.json()['agents']
            agents = [agent['id'] for agent in agents]
            if total > 5000:
                i = 5000
                self.logger.info(f"Processing large agents for agent group {group_name}, "
                                 f"it may take few minutes! Hold tight.")
                while i < total:
                    url = self.url + f"scanners/1/agent-groups/{group_id}/agents?limit=5000&offset={i}"
                    res = requests.get(url, headers=self.headers)
                    res = res.json()['agents']
                    res = [res[_]['id'] for _ in range(len(res))]
                    agents = agents + res
                    i += len(res)
                    time.sleep(1)
                    self.logger.info(f"Processed {i} groups from total {total} for agent group: {group_name}")
            self.logger.info(f"Found total {len(agents)} for agent group id: {group_id}, name: {group_name}")
            return agents
        except Exception as e:
            return self.errorLog(e)

    def errorLog(self, msg):
        """
        Global function to print error message
        :param msg:
        :return:
        """
        exc_type, exc_obj, exc_tb = sys.exc_info()
        self.logger.error("Following error occurred during processing data, " + str(msg) +" "+ str(exc_tb.tb_lineno))
        return -1


if __name__ == "__main__":
    t = TenableAgents()
    t.main()
