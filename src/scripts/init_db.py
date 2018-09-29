import logging

import coloredlogs

from src.models import Base, engine

logger = logging.getLogger(__name__)
coloredlogs.install()


def main():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    # Init DB
    main()
