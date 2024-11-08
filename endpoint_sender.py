import requests


class EndpointSender:
    def __init__(self, task: str, apikey: str, endpoint: str):
        self.task = task
        self.apikey = apikey
        self.endpoint = endpoint

    def send_answer(self, answer: dict):
        """
        Send the answer to the specified endpoint.

        :param answer: The answer data to send
        """
        answer_payload = {
            "task": self.task,
            "apikey": self.apikey,
            "answer": answer
        }
        response = requests.post(self.endpoint, json=answer_payload)
        print(response.status_code)
        print(response.text)
