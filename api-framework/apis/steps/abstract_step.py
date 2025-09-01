import logging
from abc import ABC

logger = logging.getLogger(__name__)


class AbstractStep(ABC):
    def __init__(self, parent, step_name="abstract_step"):
        self.parent = parent
        self.__step_name = step_name

    def __str__(self):
        return self.__step_name

    @property
    def step_name(self):
        return self.__step_name
