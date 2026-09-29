from abc import ABC, abstractmethod


class LLM(ABC):

    @abstractmethod
    def generate(self, messages, tools=None):
        raise NotImplementedError